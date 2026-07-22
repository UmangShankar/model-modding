from __future__ import annotations

import json
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .cli import load_yaml, resolve_mod
from .ollama import (
    DEFAULT_OLLAMA_HOST,
    compile_recipe_in_memory,
    stream_chat,
    validate_ollama_host,
)

SUPPORTED_CHECKS = {
    "contains_any",
    "not_contains",
    "question_count_min",
    "question_count_max",
    "max_words",
}
SEVERITIES = ("critical", "major", "minor")
FAIL_ON_VALUES = ("critical", "major", "minor", "none")
SEVERITY_RANK = {"minor": 1, "major": 2, "critical": 3}
EVALUATOR_VERSION = "0.2.0"


@dataclass(frozen=True)
class InvariantCheck:
    kind: str
    invariant: str
    severity: str
    description: str
    checks: dict[str, Any]


@dataclass(frozen=True)
class EvaluationCase:
    mod: str
    name: str
    prompt: str
    expected_behaviours: tuple[str, ...]
    failure_indicators: tuple[str, ...]
    checks: dict[str, Any]
    invariant_checks: tuple[InvariantCheck, ...] = ()


def human_name(value: str) -> str:
    return value.replace("-", " ").title()


def _declared_invariants(manifest: dict[str, Any]) -> dict[tuple[str, str], str]:
    declared: dict[tuple[str, str], str] = {}
    invariants = manifest.get("invariants", {})
    if not isinstance(invariants, dict):
        return declared
    for kind in ("preserve", "prohibit"):
        entries = invariants.get(kind, [])
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if isinstance(entry, dict) and isinstance(entry.get("type"), str) and isinstance(entry.get("severity"), str):
                declared[(kind, entry["type"])] = entry["severity"]
    return declared


def _load_invariant_checks(
    reference: str,
    case_name: str,
    item: dict[str, Any],
    declared: dict[tuple[str, str], str],
) -> tuple[InvariantCheck, ...]:
    loaded: list[InvariantCheck] = []
    raw_checks = item.get("invariant_checks", [])
    if raw_checks is None:
        return ()
    if not isinstance(raw_checks, list):
        raise ValueError(f"{reference}:{case_name} invariant_checks must be a list")
    for index, raw in enumerate(raw_checks, 1):
        if not isinstance(raw, dict):
            raise ValueError(f"{reference}:{case_name} invariant check {index} must be an object")
        kind = str(raw.get("kind", ""))
        invariant = str(raw.get("invariant", ""))
        severity = str(raw.get("severity", ""))
        description = str(raw.get("description", f"{kind} {invariant}")).strip()
        checks = raw.get("checks", {})
        if kind not in {"preserve", "prohibit"}:
            raise ValueError(f"{reference}:{case_name} invariant check {index} has invalid kind: {kind}")
        if (kind, invariant) not in declared:
            raise ValueError(
                f"{reference}:{case_name} invariant check {index} targets undeclared {kind} invariant: {invariant}"
            )
        if severity != declared[(kind, invariant)]:
            raise ValueError(
                f"{reference}:{case_name} invariant check {index} severity {severity!r} does not match "
                f"manifest severity {declared[(kind, invariant)]!r}"
            )
        if not isinstance(checks, dict) or not checks:
            raise ValueError(f"{reference}:{case_name} invariant check {index} requires deterministic checks")
        unsupported = sorted(set(checks) - SUPPORTED_CHECKS)
        if unsupported:
            raise ValueError(
                f"{reference}:{case_name} invariant check {index} uses unsupported checks: {', '.join(unsupported)}"
            )
        loaded.append(
            InvariantCheck(
                kind=kind,
                invariant=invariant,
                severity=severity,
                description=description,
                checks=dict(checks),
            )
        )
    return tuple(loaded)


def load_evaluation_cases(root: Path, recipe_name: str) -> tuple[Any, list[EvaluationCase]]:
    compiled = compile_recipe_in_memory(root, recipe_name)
    cases: list[EvaluationCase] = []
    for reference in compiled.references:
        _, manifest_path, manifest = resolve_mod(root, reference)
        declared = _declared_invariants(manifest)
        for path in sorted((manifest_path.parent / "evaluations").glob("*.yaml")):
            payload = load_yaml(path)
            for item in payload.get("cases", []):
                if not isinstance(item, dict):
                    continue
                name = str(item["name"])
                cases.append(
                    EvaluationCase(
                        mod=reference,
                        name=name,
                        prompt=str(item["input"]),
                        expected_behaviours=tuple(item.get("expected_behaviours", [])),
                        failure_indicators=tuple(item.get("failure_indicators", [])),
                        checks=dict(item.get("checks", {})),
                        invariant_checks=_load_invariant_checks(reference, name, item, declared),
                    )
                )
    if not cases:
        raise ValueError(f"No evaluation cases found for recipe: {recipe_name}")
    return compiled, cases


def score_response(text: str, checks: dict[str, Any]) -> tuple[bool, list[dict[str, Any]]]:
    lowered = text.casefold()
    results: list[dict[str, Any]] = []

    for group in checks.get("contains_any", []):
        terms = [str(term) for term in group]
        passed = any(term.casefold() in lowered for term in terms)
        results.append({"check": "contains_any", "terms": terms, "passed": passed})

    for term in checks.get("not_contains", []):
        value = str(term)
        passed = value.casefold() not in lowered
        results.append({"check": "not_contains", "term": value, "passed": passed})

    if "question_count_min" in checks:
        minimum = int(checks["question_count_min"])
        count = text.count("?")
        results.append({"check": "question_count_min", "expected": minimum, "actual": count, "passed": count >= minimum})

    if "question_count_max" in checks:
        maximum = int(checks["question_count_max"])
        count = text.count("?")
        results.append({"check": "question_count_max", "expected": maximum, "actual": count, "passed": count <= maximum})

    if "max_words" in checks:
        maximum = int(checks["max_words"])
        count = len(text.split())
        results.append({"check": "max_words", "expected": maximum, "actual": count, "passed": count <= maximum})

    return bool(results) and all(item["passed"] for item in results), results


def score_invariant_checks(
    text: str,
    case: EvaluationCase,
) -> tuple[bool, list[dict[str, Any]], list[dict[str, Any]]]:
    results: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for index, target in enumerate(case.invariant_checks, 1):
        passed, check_results = score_response(text, target.checks)
        result = {
            "kind": target.kind,
            "invariant": target.invariant,
            "severity": target.severity,
            "description": target.description,
            "passed": passed,
            "checks": check_results,
        }
        results.append(result)
        if not passed:
            failures.append(
                {
                    "id": f"{case.mod}:{case.name}:{target.kind}:{target.invariant}:{index}",
                    "mod": case.mod,
                    "case": case.name,
                    "kind": target.kind,
                    "invariant": target.invariant,
                    "severity": target.severity,
                    "description": target.description,
                    "failed_checks": [item for item in check_results if not item["passed"]],
                }
            )
    return all(item["passed"] for item in results), results, failures


def evaluate_case_response(text: str, case: EvaluationCase) -> dict[str, Any]:
    if case.checks:
        legacy_passed, legacy_checks = score_response(text, case.checks)
    else:
        legacy_passed, legacy_checks = True, []
    invariant_passed, invariant_results, invariant_failures = score_invariant_checks(text, case)
    return {
        "passed": legacy_passed and invariant_passed,
        "checks": legacy_checks,
        "invariant_checks": invariant_results,
        "invariant_failures": invariant_failures,
    }


def collect_response(host: str, model: str, prompt: str, system_prompt: str, timeout: float, opener: Callable[..., Any]) -> str:
    return "".join(stream_chat(host, model, prompt, system_prompt, timeout=timeout, opener=opener))


def _average_metric(rows: list[dict[str, Any]], side: str, key: str) -> float:
    values = [float(row[side][key]) for row in rows if key in row.get(side, {})]
    return sum(values) / len(values) if values else 0.0


def failure_counts(failures: list[dict[str, Any]]) -> dict[str, int]:
    return {severity: sum(1 for failure in failures if failure.get("severity") == severity) for severity in SEVERITIES}


def is_blocking_severity(severity: str, fail_on: str) -> bool:
    if fail_on == "none":
        return False
    if fail_on not in FAIL_ON_VALUES:
        raise ValueError(f"fail_on must be one of: {', '.join(FAIL_ON_VALUES)}")
    return SEVERITY_RANK.get(severity, 0) >= SEVERITY_RANK[fail_on]


def build_report(
    recipe_name: str,
    model: str,
    cases: list[EvaluationCase],
    rows: list[dict[str, Any]],
    fail_on: str = "critical",
) -> dict[str, Any]:
    if fail_on not in FAIL_ON_VALUES:
        raise ValueError(f"fail_on must be one of: {', '.join(FAIL_ON_VALUES)}")
    stock_passed = sum(1 for row in rows if row["stock"]["passed"])
    modded_passed = sum(1 for row in rows if row["modded"]["passed"])
    total = len(rows)
    by_mod: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "total": 0,
            "stock_passed": 0,
            "modded_passed": 0,
            "stock_failures": {severity: 0 for severity in SEVERITIES},
            "modded_failures": {severity: 0 for severity in SEVERITIES},
        }
    )
    regressions: list[str] = []
    improvements: list[str] = []
    stock_failures: list[dict[str, Any]] = []
    modded_failures: list[dict[str, Any]] = []
    for row in rows:
        summary = by_mod[row["mod"]]
        summary["total"] += 1
        summary["stock_passed"] += int(row["stock"]["passed"])
        summary["modded_passed"] += int(row["modded"]["passed"])
        row_stock_failures = list(row["stock"].get("invariant_failures", []))
        row_modded_failures = list(row["modded"].get("invariant_failures", []))
        stock_failures.extend(row_stock_failures)
        modded_failures.extend(row_modded_failures)
        for severity, count in failure_counts(row_stock_failures).items():
            summary["stock_failures"][severity] += count
        for severity, count in failure_counts(row_modded_failures).items():
            summary["modded_failures"][severity] += count
        if row["stock"]["passed"] and not row["modded"]["passed"]:
            regressions.append(f"{row['mod']}:{row['case']}")
        if not row["stock"]["passed"] and row["modded"]["passed"]:
            improvements.append(f"{row['mod']}:{row['case']}")
    blocking_failures = [failure for failure in modded_failures if is_blocking_severity(failure["severity"], fail_on)]
    return {
        "schema_version": "0.2",
        "evaluator": {"name": "deterministic-invariant-evaluator", "version": EVALUATOR_VERSION},
        "recipe": recipe_name,
        "recipe_display_name": human_name(recipe_name),
        "model": model,
        "summary": {
            "cases": total,
            "stock_passed": stock_passed,
            "modded_passed": modded_passed,
            "stock_pass_rate": stock_passed / total if total else 0,
            "modded_pass_rate": modded_passed / total if total else 0,
            "improvement_points": ((modded_passed - stock_passed) / total * 100) if total else 0,
            "average_stock_latency_seconds": _average_metric(rows, "stock", "latency_seconds"),
            "average_modded_latency_seconds": _average_metric(rows, "modded", "latency_seconds"),
            "average_stock_words": _average_metric(rows, "stock", "words"),
            "average_modded_words": _average_metric(rows, "modded", "words"),
            "stock_failures": failure_counts(stock_failures),
            "modded_failures": failure_counts(modded_failures),
        },
        "pipeline": {
            "status": "failed" if blocking_failures else "passed",
            "fail_on": fail_on,
            "blocking_failure_count": len(blocking_failures),
            "blocking_failures": blocking_failures,
        },
        "by_mod": dict(by_mod),
        "improvements": improvements,
        "regressions": regressions,
        "failures": {"stock": stock_failures, "modded": modded_failures},
        "cases": rows,
    }


def markdown_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    pipeline = report.get("pipeline", {"status": "passed", "fail_on": "none", "blocking_failure_count": 0})
    stock_failures = summary.get("stock_failures", {severity: 0 for severity in SEVERITIES})
    modded_failures = summary.get("modded_failures", {severity: 0 for severity in SEVERITIES})
    lines = [
        f"# {report['recipe_display_name']} evaluation",
        "",
        f"- Model: `{report['model']}`",
        f"- Evaluator: `{report.get('evaluator', {}).get('version', 'legacy')}`",
        f"- Pipeline status: **{pipeline['status'].upper()}**",
        f"- Failure threshold: `{pipeline['fail_on']}`",
        f"- Cases: {summary['cases']}",
        f"- Stock passed: {summary['stock_passed']}/{summary['cases']}",
        f"- Modded passed: {summary['modded_passed']}/{summary['cases']}",
        f"- Improvement: {summary['improvement_points']:+.1f} percentage points",
        f"- Average stock latency: {summary['average_stock_latency_seconds']:.2f}s",
        f"- Average modded latency: {summary['average_modded_latency_seconds']:.2f}s",
        f"- Average stock words: {summary['average_stock_words']:.0f}",
        f"- Average modded words: {summary['average_modded_words']:.0f}",
        "",
        "## Invariant failures",
        "",
        "| Severity | Stock | Modded |",
        "| --- | ---: | ---: |",
    ]
    for severity in SEVERITIES:
        lines.append(f"| {severity.title()} | {stock_failures.get(severity, 0)} | {modded_failures.get(severity, 0)} |")
    lines.extend([
        "",
        "## Results by mod",
        "",
        "| Mod | Stock | Modded | Critical | Major | Minor |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ])
    for mod, values in report["by_mod"].items():
        failures = values.get("modded_failures", {})
        lines.append(
            f"| `{mod}` | {values['stock_passed']}/{values['total']} | {values['modded_passed']}/{values['total']} | "
            f"{failures.get('critical', 0)} | {failures.get('major', 0)} | {failures.get('minor', 0)} |"
        )
    lines.extend(["", "## Cases", ""])
    for row in report["cases"]:
        stock_metrics = ""
        modded_metrics = ""
        if "latency_seconds" in row["stock"] and "words" in row["stock"]:
            stock_metrics = f", {row['stock']['latency_seconds']:.2f}s, {row['stock']['words']} words"
        if "latency_seconds" in row["modded"] and "words" in row["modded"]:
            modded_metrics = f", {row['modded']['latency_seconds']:.2f}s, {row['modded']['words']} words"
        lines.append(
            f"- {'PASS' if row['modded']['passed'] else 'FAIL'} `{row['mod']}:{row['case']}` -- "
            f"stock: {'pass' if row['stock']['passed'] else 'fail'}{stock_metrics}; "
            f"modded: {'pass' if row['modded']['passed'] else 'fail'}{modded_metrics}"
        )
        for failure in row["modded"].get("invariant_failures", []):
            lines.append(
                f"  - **{failure['severity'].upper()}** {failure['kind']} `{failure['invariant']}`: "
                f"{failure['description']}"
            )
    if report["regressions"]:
        lines.extend(["", "## Regressions", ""] + [f"- `{item}`" for item in report["regressions"]])
    if pipeline.get("blocking_failures"):
        lines.extend(["", "## Blocking failures", ""])
        for failure in pipeline["blocking_failures"]:
            lines.append(
                f"- **{failure['severity'].upper()}** `{failure['mod']}:{failure['case']}` "
                f"{failure['kind']} `{failure['invariant']}`"
            )
    lines.extend([
        "",
        "## Human review",
        "",
        "Deterministic invariant checks are explicit regression gates, but they do not prove complete semantic correctness. Review expected behaviours, failure indicators and full responses.",
        "",
    ])
    return "\n".join(lines)


def evaluate_recipe(
    root: Path,
    recipe_name: str,
    model: str,
    output: Path | None = None,
    dry_run: bool = False,
    host: str = DEFAULT_OLLAMA_HOST,
    timeout: float = 120.0,
    allow_remote: bool = False,
    opener: Callable[..., Any] | None = None,
    fail_on: str = "critical",
) -> int:
    try:
        if fail_on not in FAIL_ON_VALUES:
            raise ValueError(f"fail_on must be one of: {', '.join(FAIL_ON_VALUES)}")
        compiled, cases = load_evaluation_cases(root, recipe_name)
        normalized_host = validate_ollama_host(host, allow_remote)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"Evaluation: {human_name(recipe_name)}")
    print(f"Model: {model}")
    print(f"Cases: {len(cases)}")
    print(f"Failure threshold: {fail_on}")
    if dry_run:
        for case in cases:
            targets = ", ".join(
                f"{target.kind}:{target.invariant}[{target.severity}]" for target in case.invariant_checks
            ) or "legacy checks only"
            print(f"- {case.mod}:{case.name} -- {targets} -- {case.prompt}")
        return 0

    actual_opener = opener
    if actual_opener is None:
        from urllib.request import urlopen
        actual_opener = urlopen

    rows: list[dict[str, Any]] = []
    try:
        for index, case in enumerate(cases, 1):
            print(f"[{index}/{len(cases)}] {case.mod}:{case.name}")
            started = time.monotonic()
            stock_text = collect_response(normalized_host, model, case.prompt, "", timeout, actual_opener)
            stock_latency = time.monotonic() - started
            started = time.monotonic()
            modded_text = collect_response(normalized_host, model, case.prompt, compiled.system_prompt, timeout, actual_opener)
            modded_latency = time.monotonic() - started
            stock_result = evaluate_case_response(stock_text, case)
            modded_result = evaluate_case_response(modded_text, case)
            stock_result.update({
                "response": stock_text,
                "latency_seconds": stock_latency,
                "words": len(stock_text.split()),
            })
            modded_result.update({
                "response": modded_text,
                "latency_seconds": modded_latency,
                "words": len(modded_text.split()),
            })
            rows.append({
                "mod": case.mod,
                "case": case.name,
                "prompt": case.prompt,
                "expected_behaviours": list(case.expected_behaviours),
                "failure_indicators": list(case.failure_indicators),
                "stock": stock_result,
                "modded": modded_result,
            })
    except Exception as exc:
        print(f"Evaluation run failed: {exc}", file=sys.stderr)
        return 1

    report = build_report(recipe_name, model, cases, rows, fail_on=fail_on)
    destination = (output or root / "build" / "evaluations" / recipe_name).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    json_path = destination / "report.json"
    markdown_path = destination / "report.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    markdown_path.write_text(markdown_report(report), encoding="utf-8", newline="\n")
    summary = report["summary"]
    pipeline = report["pipeline"]
    print(f"\nStock passed: {summary['stock_passed']}/{summary['cases']}")
    print(f"Modded passed: {summary['modded_passed']}/{summary['cases']}")
    print(f"Improvement: {summary['improvement_points']:+.1f} percentage points")
    print(f"Modded failures: critical={summary['modded_failures']['critical']}, major={summary['modded_failures']['major']}, minor={summary['modded_failures']['minor']}")
    print(f"Pipeline status: {pipeline['status'].upper()} (fail on {pipeline['fail_on']})")
    print(f"Average stock latency: {summary['average_stock_latency_seconds']:.2f}s")
    print(f"Average modded latency: {summary['average_modded_latency_seconds']:.2f}s")
    print(f"Average stock words: {summary['average_stock_words']:.0f}")
    print(f"Average modded words: {summary['average_modded_words']:.0f}")
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {markdown_path}")
    return 1 if pipeline["status"] == "failed" else 0
