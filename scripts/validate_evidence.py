from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PLACEHOLDERS = ("REPLACE_ME", "FULL_GIT_COMMIT_SHA", "YYYY-MM-DD")
REQUIRED_FILES = ("benchmark.json", "benchmark.md", "environment.json", "methodology.md")


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return payload


def contains_placeholder(value: Any) -> bool:
    if isinstance(value, str):
        return any(marker in value for marker in PLACEHOLDERS)
    if isinstance(value, dict):
        return any(contains_placeholder(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_placeholder(item) for item in value)
    return False


def validate_result(case_name: str, mode: str, result: Any) -> list[str]:
    failures: list[str] = []
    if not isinstance(result, dict):
        return [f"case {case_name} is missing {mode} result evidence"]

    if not isinstance(result.get("response"), str):
        failures.append(f"case {case_name} is missing {mode} response evidence")
    if not isinstance(result.get("passed"), bool):
        failures.append(f"case {case_name} is missing {mode} passed outcome")
    checks = result.get("checks")
    if not isinstance(checks, list):
        failures.append(f"case {case_name} is missing {mode} checks evidence")
    elif any(not isinstance(check, dict) or not isinstance(check.get("passed"), bool) for check in checks):
        failures.append(f"case {case_name} has invalid {mode} checks evidence")
    latency = result.get("latency_seconds")
    if not isinstance(latency, (int, float)) or isinstance(latency, bool) or latency < 0:
        failures.append(f"case {case_name} is missing valid {mode} latency_seconds")
    words = result.get("words")
    if not isinstance(words, int) or isinstance(words, bool) or words < 0:
        failures.append(f"case {case_name} is missing valid {mode} words")
    return failures


def validate_package(directory: Path) -> list[str]:
    failures: list[str] = []
    for filename in REQUIRED_FILES:
        if not (directory / filename).is_file():
            failures.append(f"missing required file: {filename}")
    if failures:
        return failures

    try:
        benchmark = load_json(directory / "benchmark.json")
        environment = load_json(directory / "environment.json")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [str(exc)]

    if benchmark.get("schema_version") != "0.1":
        failures.append("benchmark.json must use schema_version 0.1")
    if not benchmark.get("recipe"):
        failures.append("benchmark.json is missing recipe")
    models = benchmark.get("models")
    if not isinstance(models, list) or not models:
        failures.append("benchmark.json must contain model results")
        models = []
    completed = [row for row in models if isinstance(row, dict) and row.get("status") == "completed"]
    if not completed:
        failures.append("benchmark.json contains no completed models")
    if benchmark.get("completed_models") != len(completed):
        failures.append("completed_models does not match completed result count")

    completed_pairs: set[tuple[str, str]] = set()
    for row in completed:
        requested = row.get("model")
        resolved = row.get("resolved_model")
        if not isinstance(requested, str) or not requested:
            failures.append("completed model is missing requested model selector")
        if not isinstance(resolved, str) or not resolved:
            failures.append(f"completed model {requested or '<unknown>'} is missing resolved_model")
        if isinstance(requested, str) and requested and isinstance(resolved, str) and resolved:
            completed_pairs.add((requested, resolved))

        cases = row.get("cases")
        if not isinstance(cases, list) or not cases:
            failures.append(f"completed model {requested or '<unknown>'} has no cases")
            continue
        for case in cases:
            if not isinstance(case, dict):
                failures.append("benchmark case must be an object")
                continue
            case_name = str(case.get("case", "<unknown>"))
            for mode in ("stock", "modded"):
                failures.extend(validate_result(case_name, mode, case.get(mode)))

    if environment.get("schema_version") != "0.1":
        failures.append("environment.json must use schema_version 0.1")
    commit = environment.get("model_modding_commit")
    if not isinstance(commit, str) or len(commit) != 40 or any(char not in "0123456789abcdefABCDEF" for char in commit):
        failures.append("environment.json must contain a full 40-character commit SHA")
    if contains_placeholder(environment):
        failures.append("environment.json still contains template placeholders")

    environment_models = environment.get("models")
    if not isinstance(environment_models, list) or not environment_models:
        failures.append("environment.json must list tested models")
    else:
        environment_pairs: set[tuple[str, str]] = set()
        for index, item in enumerate(environment_models):
            if not isinstance(item, dict):
                failures.append(f"environment.json model entry {index} must be an object")
                continue
            requested = item.get("requested")
            resolved = item.get("resolved")
            if not isinstance(requested, str) or not requested:
                failures.append(f"environment.json model entry {index} is missing requested selector")
            if not isinstance(resolved, str) or not resolved:
                failures.append(f"environment.json model entry {index} is missing resolved tag")
            if isinstance(requested, str) and requested and isinstance(resolved, str) and resolved:
                environment_pairs.add((requested, resolved))
        missing_pairs = completed_pairs - environment_pairs
        extra_pairs = environment_pairs - completed_pairs
        for requested, resolved in sorted(missing_pairs):
            failures.append(
                f"environment.json is missing completed benchmark model {requested} -> {resolved}"
            )
        for requested, resolved in sorted(extra_pairs):
            failures.append(
                f"environment.json lists model not completed by benchmark: {requested} -> {resolved}"
            )

    methodology = (directory / "methodology.md").read_text(encoding="utf-8")
    for heading in ("## Purpose", "## Procedure", "## Human review", "## Limitations", "## Conclusion"):
        if heading not in methodology:
            failures.append(f"methodology.md is missing {heading}")
    if contains_placeholder(methodology):
        failures.append("methodology.md still contains template placeholders")

    markdown = (directory / "benchmark.md").read_text(encoding="utf-8")
    if not markdown.strip():
        failures.append("benchmark.md is empty")

    return failures


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) != 1:
        print("Usage: python scripts/validate_evidence.py <evidence-directory>", file=sys.stderr)
        return 2
    directory = Path(arguments[0]).resolve()
    failures = validate_package(directory)
    if failures:
        print("Evidence validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(f"Evidence package is publishable: {directory}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
