from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Callable

from .evaluation import collect_response, human_name, load_evaluation_cases, score_response
from .ollama import DEFAULT_OLLAMA_HOST, list_models, validate_ollama_host


def parse_models(value: str) -> list[str]:
    models = [item.strip() for item in value.split(",") if item.strip()]
    if not models:
        raise ValueError("Provide at least one model with --models")
    return list(dict.fromkeys(models))


def resolve_model_selector(requested: str, installed: set[str]) -> str | None:
    """Resolve a user selector to an installed Ollama model name.

    Ollama commonly reports default-tag models as ``name:latest`` while accepting
    the shorter ``name`` selector. Prefer an exact match, then resolve only the
    implicit ``:latest`` form so explicit non-default tags remain strict.
    """
    if requested in installed:
        return requested
    if ":" not in requested:
        default_tag = f"{requested}:latest"
        if default_tag in installed:
            return default_tag
    return None


def markdown_report(report: dict[str, Any]) -> str:
    lines = [
        f"# {report['recipe_display_name']} model fitment benchmark",
        "",
        f"- Cases per model: {report['case_count']}",
        f"- Requested models: {', '.join(report['requested_models'])}",
        "",
        "| Model | Status | Stock | Modded | Change | Regressions | Avg latency | Avg words |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in report["models"]:
        if row["status"] != "completed":
            lines.append(f"| `{row['model']}` | {row['status']} | n/a | n/a | n/a | n/a | n/a | n/a |")
            continue
        summary = row["summary"]
        lines.append(
            f"| `{row['model']}` | completed | {summary['stock_passed']}/{summary['cases']} | "
            f"{summary['modded_passed']}/{summary['cases']} | {summary['improvement_points']:+.1f} pp | "
            f"{summary['regressions']} | {summary['average_latency_seconds']:.2f}s | {summary['average_modded_words']:.0f} |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "Deterministic checks indicate fitment and regressions; they do not prove overall model quality. Review full responses before changing compatibility claims.",
        "",
    ])
    return "\n".join(lines)


def benchmark_recipe(
    root: Path,
    recipe_name: str,
    models_value: str,
    output: Path | None = None,
    dry_run: bool = False,
    host: str = DEFAULT_OLLAMA_HOST,
    timeout: float = 120.0,
    allow_remote: bool = False,
    opener: Callable[..., Any] | None = None,
) -> int:
    try:
        models = parse_models(models_value)
        compiled, cases = load_evaluation_cases(root, recipe_name)
        normalized_host = validate_ollama_host(host, allow_remote)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"Benchmark: {human_name(recipe_name)}")
    print(f"Models: {', '.join(models)}")
    print(f"Cases per model: {len(cases)}")
    if dry_run:
        for model in models:
            print(f"- {model}: {len(cases)} stock + {len(cases)} modded runs")
        return 0

    if opener is None:
        from urllib.request import urlopen
        opener = urlopen

    try:
        installed = set(list_models(normalized_host, timeout=min(timeout, 5.0), opener=opener))
    except Exception as exc:
        print(f"Could not discover Ollama models: {exc}", file=sys.stderr)
        return 1

    model_reports: list[dict[str, Any]] = []
    for model in models:
        resolved_model = resolve_model_selector(model, installed)
        if resolved_model is None:
            print(f"SKIP {model}: not installed")
            model_reports.append({"model": model, "status": "unavailable", "reason": "not installed"})
            continue

        rows: list[dict[str, Any]] = []
        print(f"\nModel: {model}" + (f" ({resolved_model})" if resolved_model != model else ""))
        try:
            for index, case in enumerate(cases, 1):
                print(f"[{index}/{len(cases)}] {case.mod}:{case.name}")
                started = time.monotonic()
                stock_text = collect_response(normalized_host, resolved_model, case.prompt, "", timeout, opener)
                stock_latency = time.monotonic() - started
                started = time.monotonic()
                modded_text = collect_response(normalized_host, resolved_model, case.prompt, compiled.system_prompt, timeout, opener)
                modded_latency = time.monotonic() - started
                stock_passed, stock_checks = score_response(stock_text, case.checks)
                modded_passed, modded_checks = score_response(modded_text, case.checks)
                rows.append({
                    "mod": case.mod,
                    "case": case.name,
                    "prompt": case.prompt,
                    "stock": {
                        "passed": stock_passed,
                        "response": stock_text,
                        "checks": stock_checks,
                        "latency_seconds": stock_latency,
                        "words": len(stock_text.split()),
                    },
                    "modded": {
                        "passed": modded_passed,
                        "response": modded_text,
                        "checks": modded_checks,
                        "latency_seconds": modded_latency,
                        "words": len(modded_text.split()),
                    },
                })
        except Exception as exc:
            print(f"FAILED {model}: {exc}", file=sys.stderr)
            model_reports.append({"model": model, "resolved_model": resolved_model, "status": "failed", "reason": str(exc)})
            continue

        total = len(rows)
        stock_passed = sum(int(row["stock"]["passed"]) for row in rows)
        modded_passed = sum(int(row["modded"]["passed"]) for row in rows)
        regressions = [f"{row['mod']}:{row['case']}" for row in rows if row["stock"]["passed"] and not row["modded"]["passed"]]
        improvements = [f"{row['mod']}:{row['case']}" for row in rows if not row["stock"]["passed"] and row["modded"]["passed"]]
        summary = {
            "cases": total,
            "stock_passed": stock_passed,
            "modded_passed": modded_passed,
            "stock_pass_rate": stock_passed / total if total else 0,
            "modded_pass_rate": modded_passed / total if total else 0,
            "improvement_points": ((modded_passed - stock_passed) / total * 100) if total else 0,
            "regressions": len(regressions),
            "improvements": len(improvements),
            "average_latency_seconds": sum(row["stock"]["latency_seconds"] + row["modded"]["latency_seconds"] for row in rows) / (2 * total) if total else 0,
            "average_modded_words": sum(row["modded"]["words"] for row in rows) / total if total else 0,
        }
        model_reports.append({"model": model, "resolved_model": resolved_model, "status": "completed", "summary": summary, "regressions": regressions, "improvements": improvements, "cases": rows})

    completed = [row for row in model_reports if row["status"] == "completed"]
    report = {
        "schema_version": "0.1",
        "recipe": recipe_name,
        "recipe_display_name": human_name(recipe_name),
        "case_count": len(cases),
        "requested_models": models,
        "completed_models": len(completed),
        "models": model_reports,
    }
    destination = (output or root / "build" / "benchmarks" / recipe_name).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    json_path = destination / "benchmark.json"
    markdown_path = destination / "benchmark.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    markdown_path.write_text(markdown_report(report), encoding="utf-8", newline="\n")
    print(f"\nCompleted models: {len(completed)}/{len(models)}")
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {markdown_path}")
    return 0 if completed else 1
