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


@dataclass(frozen=True)
class EvaluationCase:
    mod: str
    name: str
    prompt: str
    expected_behaviours: tuple[str, ...]
    failure_indicators: tuple[str, ...]
    checks: dict[str, Any]


def human_name(value: str) -> str:
    return value.replace("-", " ").title()


def load_evaluation_cases(root: Path, recipe_name: str) -> tuple[Any, list[EvaluationCase]]:
    compiled = compile_recipe_in_memory(root, recipe_name)
    cases: list[EvaluationCase] = []
    for reference in compiled.references:
        _, manifest_path, _ = resolve_mod(root, reference)
        for path in sorted((manifest_path.parent / "evaluations").glob("*.yaml")):
            payload = load_yaml(path)
            for item in payload.get("cases", []):
                if not isinstance(item, dict):
                    continue
                cases.append(
                    EvaluationCase(
                        mod=reference,
                        name=str(item["name"]),
                        prompt=str(item["input"]),
                        expected_behaviours=tuple(item.get("expected_behaviours", [])),
                        failure_indicators=tuple(item.get("failure_indicators", [])),
                        checks=dict(item.get("checks", {})),
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


def collect_response(host: str, model: str, prompt: str, system_prompt: str, timeout: float, opener: Callable[..., Any]) -> str:
    return "".join(stream_chat(host, model, prompt, system_prompt, timeout=timeout, opener=opener))


def _average_metric(rows: list[dict[str, Any]], side: str, key: str) -> float:
    values = [float(row[side][key]) for row in rows if key in row.get(side, {})]
    return sum(values) / len(values) if values else 0.0


def build_report(recipe_name: str, model: str, cases: list[EvaluationCase], rows: list[dict[str, Any]]) -> dict[str, Any]:
    stock_passed = sum(1 for row in rows if row["stock"]["passed"])
    modded_passed = sum(1 for row in rows if row["modded"]["passed"])
    total = len(rows)
    by_mod: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "stock_passed": 0, "modded_passed": 0})
    regressions: list[str] = []
    improvements: list[str] = []
    for row in rows:
        summary = by_mod[row["mod"]]
        summary["total"] += 1
        summary["stock_passed"] += int(row["stock"]["passed"])
        summary["modded_passed"] += int(row["modded"]["passed"])
        if row["stock"]["passed"] and not row["modded"]["passed"]:
            regressions.append(f"{row['mod']}:{row['case']}")
        if not row["stock"]["passed"] and row["modded"]["passed"]:
            improvements.append(f"{row['mod']}:{row['case']}")
    return {
        "schema_version": "0.1",
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
        },
        "by_mod": dict(by_mod),
        "improvements": improvements,
        "regressions": regressions,
        "cases": rows,
    }


def markdown_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        f"# {report['recipe_display_name']} evaluation",
        "",
        f"- Model: `{report['model']}`",
        f"- Cases: {summary['cases']}",
        f"- Stock passed: {summary['stock_passed']}/{summary['cases']}",
        f"- Modded passed: {summary['modded_passed']}/{summary['cases']}",
        f"- Improvement: {summary['improvement_points']:+.1f} percentage points",
        f"- Average stock latency: {summary['average_stock_latency_seconds']:.2f}s",
        f"- Average modded latency: {summary['average_modded_latency_seconds']:.2f}s",
        f"- Average stock words: {summary['average_stock_words']:.0f}",
        f"- Average modded words: {summary['average_modded_words']:.0f}",
        "",
        "## Results by mod",
        "",
        "| Mod | Stock | Modded |",
        "| --- | ---: | ---: |",
    ]
    for mod, values in report["by_mod"].items():
        lines.append(f"| `{mod}` | {values['stock_passed']}/{values['total']} | {values['modded_passed']}/{values['total']} |")
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
    if report["regressions"]:
        lines.extend(["", "## Regressions", ""] + [f"- `{item}`" for item in report["regressions"]])
    lines.extend(["", "## Human review", "", "Deterministic checks are indicators, not a substitute for reviewing the expected behaviours and full responses.", ""])
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
) -> int:
    try:
        compiled, cases = load_evaluation_cases(root, recipe_name)
        normalized_host = validate_ollama_host(host, allow_remote)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"Evaluation: {human_name(recipe_name)}")
    print(f"Model: {model}")
    print(f"Cases: {len(cases)}")
    if dry_run:
        for case in cases:
            print(f"- {case.mod}:{case.name} -- {case.prompt}")
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
            stock_passed, stock_checks = score_response(stock_text, case.checks)
            modded_passed, modded_checks = score_response(modded_text, case.checks)
            rows.append({
                "mod": case.mod,
                "case": case.name,
                "prompt": case.prompt,
                "expected_behaviours": list(case.expected_behaviours),
                "failure_indicators": list(case.failure_indicators),
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
        print(f"Evaluation run failed: {exc}", file=sys.stderr)
        return 1

    report = build_report(recipe_name, model, cases, rows)
    destination = (output or root / "build" / "evaluations" / recipe_name).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    json_path = destination / "report.json"
    markdown_path = destination / "report.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    markdown_path.write_text(markdown_report(report), encoding="utf-8", newline="\n")
    summary = report["summary"]
    print(f"\nStock passed: {summary['stock_passed']}/{summary['cases']}")
    print(f"Modded passed: {summary['modded_passed']}/{summary['cases']}")
    print(f"Improvement: {summary['improvement_points']:+.1f} percentage points")
    print(f"Average stock latency: {summary['average_stock_latency_seconds']:.2f}s")
    print(f"Average modded latency: {summary['average_modded_latency_seconds']:.2f}s")
    print(f"Average stock words: {summary['average_stock_words']:.0f}")
    print(f"Average modded words: {summary['average_modded_words']:.0f}")
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {markdown_path}")
    return 0
