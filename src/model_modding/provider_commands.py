from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

from .benchmark import markdown_report as benchmark_markdown
from .benchmark import parse_models, resolve_model_selector
from .evidence import response_record, write_evidence_bundle
from .evaluation import (
    EVALUATOR_VERSION,
    build_report,
    evaluate_case_response,
    failure_counts,
    human_name,
    load_evaluation_cases,
    markdown_report as evaluation_markdown,
)
from .ollama import compile_recipe_in_memory
from .provider import ProviderConfigurationError, ProviderError, ProviderRequest
from .runtime import RuntimeConfig, generate_response, generation_options_from_values

RUNTIME_COMMANDS = {"run", "evaluate", "benchmark"}
REPORT_SCHEMA_VERSION = "0.4"


def handles(arguments: list[str]) -> bool:
    skip = False
    for token in arguments:
        if skip:
            skip = False
            continue
        if token == "--root":
            skip = True
            continue
        if token.startswith("-"):
            continue
        return token in RUNTIME_COMMANDS
    return False


def _add_runtime_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--provider", default="ollama", help="Registered provider name (default: ollama)")
    parser.add_argument("--host", dest="endpoint", help="Provider endpoint; defaults to the provider's local/default endpoint")
    parser.add_argument("--timeout", type=float, default=120.0, help="Request timeout in seconds")
    parser.add_argument("--allow-remote-host", action="store_true", help="Allow a non-loopback provider endpoint")
    parser.add_argument("--temperature", type=float)
    parser.add_argument("--top-p", type=float)
    parser.add_argument("--max-tokens", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--stop", action="append", default=[], help="Repeatable stop sequence")
    parser.add_argument("--evidence", type=Path, help="Write a durable run evidence bundle to this directory")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="modding", description="Provider-aware Model Modding runtime commands")
    parser.add_argument("--root", dest="global_root", type=Path, default=Path.cwd(), help="Repository root")
    subcommands = parser.add_subparsers(dest="command", required=True)

    run = subcommands.add_parser("run", help="Run a recipe through a registered provider")
    run.add_argument("name")
    run.add_argument("--model", required=True)
    run.add_argument("--prompt", required=True)
    _add_runtime_arguments(run)

    evaluate = subcommands.add_parser("evaluate", help="Evaluate stock and modded behaviour through a provider")
    evaluate.add_argument("name")
    evaluate.add_argument("--model", required=True)
    evaluate.add_argument("--output", type=Path)
    evaluate.add_argument("--dry-run", action="store_true")
    evaluate.add_argument("--fail-on", choices=("critical", "major", "minor", "none"), default="critical")
    _add_runtime_arguments(evaluate)

    benchmark = subcommands.add_parser("benchmark", help="Benchmark a recipe across provider models")
    benchmark.add_argument("name")
    benchmark.add_argument("--models", required=True)
    benchmark.add_argument("--output", type=Path)
    benchmark.add_argument("--dry-run", action="store_true")
    _add_runtime_arguments(benchmark)
    return parser


def _runtime(args: argparse.Namespace) -> RuntimeConfig:
    return RuntimeConfig(
        provider=args.provider,
        endpoint=args.endpoint,
        allow_remote=args.allow_remote_host,
        options=generation_options_from_values(
            temperature=args.temperature,
            top_p=args.top_p,
            max_tokens=args.max_tokens,
            seed=args.seed,
            stop=args.stop,
        ),
    )


def _execution(response: Any) -> dict[str, Any]:
    metadata = response.execution_metadata()
    metadata["latency_seconds"] = response.latency_seconds
    return metadata


def _score_response(response: Any, case: Any) -> dict[str, Any]:
    result = evaluate_case_response(response.text, case)
    result.update({
        "response": response.text,
        "latency_seconds": response.latency_seconds,
        "words": len(response.text.split()),
        "execution": _execution(response),
    })
    return result


def _evidence_destination(root: Path, value: Path) -> Path:
    return value.resolve() if value.is_absolute() else (root / value).resolve()


def _runtime_from_response(runtime: RuntimeConfig, response: Any) -> dict[str, Any]:
    result = runtime.as_dict()
    result["provider"] = response.provider
    endpoint = response.metadata.get("endpoint") if isinstance(response.metadata, dict) else None
    if endpoint:
        result["endpoint"] = endpoint
    return result


def run_command(root: Path, args: argparse.Namespace, opener: Callable[..., Any] | None = None) -> int:
    try:
        compiled = compile_recipe_in_memory(root, args.name)
        runtime = _runtime(args)
        response = generate_response(
            runtime,
            model=args.model,
            prompt=args.prompt,
            system_prompt=compiled.system_prompt,
            timeout=args.timeout,
            opener=opener,
            on_chunk=lambda chunk: print(chunk, end="", flush=True),
        )
    except (OSError, ValueError, ProviderError) as exc:
        print(str(exc), file=sys.stderr)
        return 1 if isinstance(exc, ProviderError) else 2

    execution = _execution(response)
    print(f"Recipe: {human_name(compiled.name)}")
    print(f"Provider: {execution['provider']}")
    print(f"Model: {execution['model']}")
    print(f"Endpoint: {execution.get('metadata', {}).get('endpoint', 'not reported')}")
    print(f"Installed mods: {', '.join(compiled.references)}")
    print("\nResponse:\n")
    print(response.text)
    print(f"\nCompleted in {response.latency_seconds:.2f}s")
    print(f"Requested options: {json.dumps(execution['requested_options'], sort_keys=True)}")
    print(f"Effective options: {json.dumps(execution['effective_options'], sort_keys=True)}")
    print(f"Finish reason: {execution['finish_reason'] or 'not reported'}")

    if args.evidence:
        try:
            evidence = write_evidence_bundle(
                root,
                args.name,
                _evidence_destination(root, args.evidence),
                bundle_type="run",
                runtime=_runtime_from_response(runtime, response),
                requested_models=[args.model],
                records=[
                    response_record(
                        identifier="run:modded:1",
                        role="modded",
                        prompt=args.prompt,
                        system_prompt=compiled.system_prompt,
                        response=response,
                    )
                ],
            )
        except (OSError, ValueError) as exc:
            print(f"Evidence creation failed: {exc}", file=sys.stderr)
            return 1
        print(f"Evidence bundle: {evidence}")
    return 0


def evaluate_command(root: Path, args: argparse.Namespace, opener: Callable[..., Any] | None = None) -> int:
    try:
        compiled, cases = load_evaluation_cases(root, args.name)
        runtime = _runtime(args)
        adapter = runtime.create_adapter(opener)
    except (OSError, ValueError, ProviderError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"Evaluation: {human_name(args.name)}")
    print(f"Provider: {runtime.provider.casefold()}")
    print(f"Model: {args.model}")
    print(f"Cases: {len(cases)}")
    if args.dry_run:
        print(f"Runtime: {json.dumps(runtime.as_dict(adapter), sort_keys=True)}")
        return 0

    rows: list[dict[str, Any]] = []
    evidence_records: list[dict[str, Any]] = []
    try:
        for index, case in enumerate(cases, 1):
            print(f"[{index}/{len(cases)}] {case.mod}:{case.name}")
            stock = adapter.generate(
                ProviderRequest(model=args.model, prompt=case.prompt, options=runtime.options, timeout=args.timeout)
            )
            modded = adapter.generate(
                ProviderRequest(
                    model=args.model,
                    prompt=case.prompt,
                    system_prompt=compiled.system_prompt,
                    options=runtime.options,
                    timeout=args.timeout,
                )
            )
            rows.append({
                "mod": case.mod,
                "case": case.name,
                "prompt": case.prompt,
                "expected_behaviours": list(case.expected_behaviours),
                "failure_indicators": list(case.failure_indicators),
                "stock": _score_response(stock, case),
                "modded": _score_response(modded, case),
            })
            evidence_records.extend([
                response_record(
                    identifier=f"evaluation:{index}:stock",
                    role="stock",
                    prompt=case.prompt,
                    system_prompt="",
                    response=stock,
                    case=case.name,
                    mod=case.mod,
                ),
                response_record(
                    identifier=f"evaluation:{index}:modded",
                    role="modded",
                    prompt=case.prompt,
                    system_prompt=compiled.system_prompt,
                    response=modded,
                    case=case.name,
                    mod=case.mod,
                ),
            ])
    except ProviderError as exc:
        print(f"Evaluation run failed: {exc}", file=sys.stderr)
        return 1

    report = build_report(args.name, args.model, cases, rows, fail_on=args.fail_on)
    report["schema_version"] = REPORT_SCHEMA_VERSION
    report["runtime"] = runtime.as_dict(adapter)
    report["runtime"]["provider"] = runtime.provider.casefold()
    report["runtime"]["model"] = args.model
    destination = (args.output or root / "build" / "evaluations" / args.name).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    (destination / "report.md").write_text(evaluation_markdown(report), encoding="utf-8", newline="\n")

    if args.evidence:
        try:
            evidence = write_evidence_bundle(
                root,
                args.name,
                _evidence_destination(root, args.evidence),
                bundle_type="evaluation",
                runtime=runtime.as_dict(adapter),
                requested_models=[args.model],
                records=evidence_records,
                evaluation=report,
            )
        except (OSError, ValueError) as exc:
            print(f"Evidence creation failed: {exc}", file=sys.stderr)
            return 1
        print(f"Evidence bundle: {evidence}")

    print(f"Pipeline status: {report['pipeline']['status'].upper()}")
    print(f"JSON report: {destination / 'report.json'}")
    return 1 if report["pipeline"]["status"] == "failed" else 0


def benchmark_command(root: Path, args: argparse.Namespace, opener: Callable[..., Any] | None = None) -> int:
    try:
        models = parse_models(args.models)
        compiled, cases = load_evaluation_cases(root, args.name)
        runtime = _runtime(args)
        adapter = runtime.create_adapter(opener)
    except (OSError, ValueError, ProviderError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.dry_run:
        print(f"Provider: {runtime.provider.casefold()}")
        print(f"Models: {', '.join(models)}")
        return 0

    try:
        installed = set(adapter.list_models(timeout=min(args.timeout, 5.0)))
    except ProviderError as exc:
        print(f"Could not discover {runtime.provider} models: {exc}", file=sys.stderr)
        return 1

    model_reports: list[dict[str, Any]] = []
    evidence_records: list[dict[str, Any]] = []
    for model_index, requested_model in enumerate(models, 1):
        resolved = resolve_model_selector(requested_model, installed) if runtime.provider.casefold() == "ollama" else requested_model
        if resolved is None:
            model_reports.append({"model": requested_model, "status": "unavailable", "reason": "not installed"})
            continue
        rows: list[dict[str, Any]] = []
        try:
            for case_index, case in enumerate(cases, 1):
                stock = adapter.generate(
                    ProviderRequest(model=resolved, prompt=case.prompt, options=runtime.options, timeout=args.timeout)
                )
                modded = adapter.generate(
                    ProviderRequest(
                        model=resolved,
                        prompt=case.prompt,
                        system_prompt=compiled.system_prompt,
                        options=runtime.options,
                        timeout=args.timeout,
                    )
                )
                rows.append({
                    "mod": case.mod,
                    "case": case.name,
                    "stock": _score_response(stock, case),
                    "modded": _score_response(modded, case),
                })
                evidence_records.extend([
                    response_record(
                        identifier=f"benchmark:{model_index}:{case_index}:stock",
                        role="stock",
                        prompt=case.prompt,
                        system_prompt="",
                        response=stock,
                        case=case.name,
                        mod=case.mod,
                    ),
                    response_record(
                        identifier=f"benchmark:{model_index}:{case_index}:modded",
                        role="modded",
                        prompt=case.prompt,
                        system_prompt=compiled.system_prompt,
                        response=modded,
                        case=case.name,
                        mod=case.mod,
                    ),
                ])
        except ProviderError as exc:
            model_reports.append({"model": requested_model, "resolved_model": resolved, "status": "failed", "reason": str(exc)})
            continue
        stock_failures = [failure for row in rows for failure in row["stock"].get("failures", [])]
        modded_failures = [failure for row in rows for failure in row["modded"].get("failures", [])]
        total = len(rows)
        stock_passed = sum(int(row["stock"]["passed"]) for row in rows)
        modded_passed = sum(int(row["modded"]["passed"]) for row in rows)
        regressions = [f"{row['mod']}:{row['case']}" for row in rows if row["stock"]["passed"] and not row["modded"]["passed"]]
        model_reports.append({
            "model": requested_model,
            "resolved_model": resolved,
            "status": "completed",
            "execution": {"provider": runtime.provider.casefold(), "model": resolved, "requested_options": runtime.options.supplied(), **adapter.describe()},
            "summary": {
                "cases": total,
                "stock_passed": stock_passed,
                "modded_passed": modded_passed,
                "improvement_points": ((modded_passed - stock_passed) / total * 100) if total else 0,
                "regressions": len(regressions),
                "stock_failures": failure_counts(stock_failures),
                "modded_failures": failure_counts(modded_failures),
                "modded_source_comparison_failures": sum(1 for failure in modded_failures if failure.get("layer") == "source_comparison"),
                "average_latency_seconds": sum(row["stock"]["latency_seconds"] + row["modded"]["latency_seconds"] for row in rows) / (2 * total) if total else 0,
                "average_modded_words": sum(row["modded"]["words"] for row in rows) / total if total else 0,
            },
            "regressions": regressions,
            "failures": {"stock": stock_failures, "modded": modded_failures},
            "cases": rows,
        })

    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "evaluator": {"name": "deterministic-source-invariant-evaluator", "version": EVALUATOR_VERSION},
        "runtime": runtime.as_dict(adapter),
        "recipe": args.name,
        "recipe_display_name": human_name(args.name),
        "case_count": len(cases),
        "source_fact_count": sum(len(case.source_facts) for case in cases),
        "requested_models": models,
        "completed_models": sum(1 for row in model_reports if row["status"] == "completed"),
        "models": model_reports,
    }
    destination = (args.output or root / "build" / "benchmarks" / args.name).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "benchmark.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    (destination / "benchmark.md").write_text(benchmark_markdown(report), encoding="utf-8", newline="\n")

    if args.evidence and evidence_records:
        try:
            evidence = write_evidence_bundle(
                root,
                args.name,
                _evidence_destination(root, args.evidence),
                bundle_type="benchmark",
                runtime=runtime.as_dict(adapter),
                requested_models=models,
                records=evidence_records,
                evaluation=report,
            )
        except (OSError, ValueError) as exc:
            print(f"Evidence creation failed: {exc}", file=sys.stderr)
            return 1
        print(f"Evidence bundle: {evidence}")

    print(f"Completed models: {report['completed_models']}/{len(models)}")
    return 0 if report["completed_models"] else 1


def main(arguments: list[str] | None = None, opener: Callable[..., Any] | None = None) -> int:
    args = build_parser().parse_args(arguments)
    root = args.global_root.resolve()
    try:
        if args.command == "run":
            return run_command(root, args, opener)
        if args.command == "evaluate":
            return evaluate_command(root, args, opener)
        if args.command == "benchmark":
            return benchmark_command(root, args, opener)
    except (ValueError, ProviderConfigurationError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 2
