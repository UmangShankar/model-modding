from __future__ import annotations

import json
import os
import shutil
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator

from .builds import BUILD_ENGINE_NAME, canonical_json_bytes, sha256_bytes
from .evaluation import SEVERITIES
from .evidence import verify_evidence_bundle
from .evidence_comparison import _extract_targets, _load_bundle, _target_observations

RELEASE_SCHEMA_VERSION = "0.1"
RELEASE_ENGINE_VERSION = "0.1.0"
REQUIRED_PROVIDERS = ("ollama", "anthropic", "openai")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def _validate(root: Path, schema_name: str, value: dict[str, Any]) -> None:
    schema = _read_json(root / "schemas" / schema_name)
    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value),
        key=lambda item: list(item.path),
    )
    if errors:
        detail = "; ".join(
            f"{'.'.join(str(part) for part in error.path) or '<root>'}: {error.message}"
            for error in errors
        )
        raise ValueError(f"Generated {schema_name} payload is invalid: {detail}")


def _severity_counts(failures: Iterable[dict[str, Any]]) -> dict[str, int]:
    values = list(failures)
    return {
        severity: sum(1 for failure in values if failure.get("severity") == severity)
        for severity in SEVERITIES
    }


def _shared_identity(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "recipe": deepcopy(manifest["recipe"]),
        "evaluator": deepcopy(manifest.get("evaluator")),
        "fixture_set_digest": manifest.get("fixture_set_digest"),
    }


def _assert_shared_identity(reference: dict[str, Any], current: dict[str, Any], label: str) -> None:
    pairs = (
        ("recipe.name", reference["recipe"]["name"], current["recipe"]["name"]),
        ("recipe.version", reference["recipe"]["version"], current["recipe"]["version"]),
        ("recipe.source_digest", reference["recipe"]["source_digest"], current["recipe"]["source_digest"]),
        ("recipe.build_digest", reference["recipe"]["build_digest"], current["recipe"]["build_digest"]),
        ("fixture_set_digest", reference.get("fixture_set_digest"), current.get("fixture_set_digest")),
        ("evaluator", reference.get("evaluator"), current.get("evaluator")),
    )
    mismatches = [field for field, left, right in pairs if left != right]
    if mismatches:
        raise ValueError(f"{label} is not release-compatible: {', '.join(mismatches)}")


def _run_descriptor(manifest: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    failures = list(target["failures"]["modded"])
    cases = int(target.get("summary", {}).get("cases", len(target.get("cases", []))))
    observations = _target_observations(target)
    return {
        "evidence_digest": manifest["evidence_digest"],
        "created_at": manifest["created_at"],
        "source_control": deepcopy(manifest["source_control"]),
        "runtime": deepcopy(target.get("runtime", manifest["runtime"])),
        "cases": cases,
        "passed": not failures,
        "modded_failures": _severity_counts(failures),
        "invariant_observations": {
            "|".join(key): deepcopy(counts) for key, counts in sorted(observations.items())
        },
    }


def aggregate_evidence(
    root: Path,
    directories: list[Path],
    *,
    minimum_repetitions: int = 1,
    require_zero_critical: bool = False,
) -> dict[str, Any]:
    if not directories:
        raise ValueError("At least one evidence bundle is required")
    if minimum_repetitions < 1:
        raise ValueError("minimum_repetitions must be at least 1")

    loaded = [_load_bundle(root, directory) for directory in directories]
    manifests = [item[0] for item in loaded]
    reference = manifests[0]
    for index, manifest in enumerate(manifests[1:], 2):
        _assert_shared_identity(reference, manifest, f"Evidence bundle {index}")

    grouped: dict[str, dict[str, Any]] = {}
    for manifest, evaluation in loaded:
        for key, target in _extract_targets(manifest, evaluation).items():
            bucket = grouped.setdefault(
                key,
                {
                    "key": key,
                    "provider": target["provider"],
                    "model": target["model"],
                    "runs": [],
                },
            )
            bucket["runs"].append(_run_descriptor(manifest, target))

    target_rows: list[dict[str, Any]] = []
    for key in sorted(grouped):
        bucket = grouped[key]
        runs = sorted(bucket["runs"], key=lambda item: (item["created_at"], item["evidence_digest"]))
        total_failures = {severity: sum(run["modded_failures"][severity] for run in runs) for severity in SEVERITIES}
        observation_totals: dict[str, dict[str, int]] = defaultdict(
            lambda: {"tested": 0, "passed": 0, "failed": 0}
        )
        for run in runs:
            for identity, counts in run["invariant_observations"].items():
                for field in ("tested", "passed", "failed"):
                    observation_totals[identity][field] += int(counts[field])
        invariants = []
        for identity in sorted(observation_totals):
            kind, invariant, severity = identity.split("|", 2)
            counts = observation_totals[identity]
            invariants.append(
                {
                    "kind": kind,
                    "invariant": invariant,
                    "severity": severity,
                    **counts,
                    "pass_rate": counts["passed"] / counts["tested"] if counts["tested"] else 0.0,
                    "status": "passed" if counts["failed"] == 0 else "failed",
                }
            )
        repetitions = len(runs)
        target_rows.append(
            {
                "key": key,
                "provider": bucket["provider"],
                "model": bucket["model"],
                "repetitions": repetitions,
                "minimum_cases": min((run["cases"] for run in runs), default=0),
                "runs_passed": sum(1 for run in runs if run["passed"]),
                "runs_failed": sum(1 for run in runs if not run["passed"]),
                "critical_free_runs": sum(1 for run in runs if run["modded_failures"]["critical"] == 0),
                "modded_failures": total_failures,
                "evidence_digests": [run["evidence_digest"] for run in runs],
                "invariants": invariants,
                "runs": runs,
            }
        )

    repetition_failures = [row["key"] for row in target_rows if row["repetitions"] < minimum_repetitions]
    critical_failures = [row["key"] for row in target_rows if row["modded_failures"]["critical"] > 0]
    pipeline_failed = bool(repetition_failures or (require_zero_critical and critical_failures))
    report = {
        "schema_version": RELEASE_SCHEMA_VERSION,
        "document_type": "model-modding-repeated-evidence-aggregate",
        "release_engine": {"name": BUILD_ENGINE_NAME, "version": RELEASE_ENGINE_VERSION},
        "aggregate_digest": "0" * 64,
        **_shared_identity(reference),
        "evidence_count": len(directories),
        "target_count": len(target_rows),
        "minimum_repetitions": minimum_repetitions,
        "require_zero_critical": require_zero_critical,
        "pipeline": {
            "status": "failed" if pipeline_failed else "passed",
            "repetition_failures": repetition_failures,
            "critical_failure_targets": critical_failures,
        },
        "targets": target_rows,
        "limitations": [
            "Aggregation describes repeated executions of the exact locked build, fixture set and evaluator only.",
            "Repeated passing runs do not prove universal provider compatibility or semantic correctness.",
            "Human and domain review remain required before publishing high-stakes compatibility claims.",
        ],
    }
    payload = deepcopy(report)
    payload.pop("aggregate_digest")
    report["aggregate_digest"] = sha256_bytes(canonical_json_bytes(payload))
    _validate(root, "repeated-evidence.schema.json", report)
    return report


def aggregate_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Repeated evidence aggregate",
        "",
        f"- Pipeline: **{report['pipeline']['status'].upper()}**",
        f"- Evidence bundles: {report['evidence_count']}",
        f"- Targets: {report['target_count']}",
        f"- Required repetitions: {report['minimum_repetitions']}",
        f"- Build digest: `{report['recipe']['build_digest']}`",
        f"- Aggregate digest: `{report['aggregate_digest']}`",
        "",
        "## Targets",
        "",
        "| Target | Repetitions | Minimum cases | Runs passed | Critical failures | Status |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for target in report["targets"]:
        status = "passed" if target["runs_failed"] == 0 else "failed"
        lines.append(
            f"| `{target['key']}` | {target['repetitions']} | {target['minimum_cases']} | "
            f"{target['runs_passed']} | {target['modded_failures']['critical']} | {status} |"
        )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    return "\n".join(lines) + "\n"


def write_aggregate(root: Path, directories: list[Path], output: Path, *, minimum_repetitions: int = 1, require_zero_critical: bool = False) -> tuple[Path, dict[str, Any]]:
    report = aggregate_evidence(
        root,
        directories,
        minimum_repetitions=minimum_repetitions,
        require_zero_critical=require_zero_critical,
    )
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    (output / "aggregate.json").write_bytes(canonical_json_bytes(report))
    (output / "aggregate.md").write_text(aggregate_markdown(report), encoding="utf-8", newline="\n")
    return output, report


def activate_baseline(
    root: Path,
    source: Path,
    destination: Path,
    *,
    reviewer: str,
    scope: str,
    notes: str,
) -> Path:
    reviewer = reviewer.strip()
    scope = scope.strip()
    if not reviewer or not scope:
        raise ValueError("reviewer and scope are required")
    failures = verify_evidence_bundle(root, source)
    if failures:
        raise ValueError("Source evidence failed verification: " + "; ".join(failures))
    manifest = _read_json(source / "manifest.json")
    destination = destination.resolve()
    evidence_destination = destination / "evidence"
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, evidence_destination)
    baseline = {
        "schema_version": RELEASE_SCHEMA_VERSION,
        "document_type": "model-modding-reviewed-baseline",
        "baseline_digest": "0" * 64,
        "scope": scope,
        "reviewer": reviewer,
        "notes": notes.strip(),
        "evidence_digest": manifest["evidence_digest"],
        "recipe": deepcopy(manifest["recipe"]),
        "evaluator": deepcopy(manifest.get("evaluator")),
        "fixture_set_digest": manifest.get("fixture_set_digest"),
        "limitations": [
            "Baseline acceptance is scoped and does not imply universal provider or model compatibility.",
            "The embedded evidence bundle remains authoritative for exact execution details.",
        ],
    }
    payload = deepcopy(baseline)
    payload.pop("baseline_digest")
    baseline["baseline_digest"] = sha256_bytes(canonical_json_bytes(payload))
    _validate(root, "reviewed-baseline.schema.json", baseline)
    (destination / "baseline.json").write_bytes(canonical_json_bytes(baseline))
    return destination


def _matrix_provider_set(matrix: dict[str, Any]) -> set[str]:
    return {str(target["provider"]).casefold() for target in matrix.get("targets", [])}


def check_release_readiness(
    root: Path,
    aggregate_path: Path,
    matrix_path: Path,
    *,
    minimum_repetitions: int = 3,
    minimum_cases: int = 40,
    required_providers: tuple[str, ...] = REQUIRED_PROVIDERS,
) -> dict[str, Any]:
    aggregate = _read_json(aggregate_path)
    matrix = _read_json(matrix_path)
    _validate(root, "repeated-evidence.schema.json", aggregate)
    _validate(root, "compatibility-matrix.schema.json", matrix)

    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": passed, "detail": detail})

    add("recipe identity", aggregate["recipe"] == matrix["recipe"], "aggregate and matrix recipe identities must match")
    add("fixture set", aggregate.get("fixture_set_digest") == matrix.get("fixture_set_digest"), "aggregate and matrix fixture sets must match")
    add("evaluator", aggregate.get("evaluator") == matrix.get("evaluator"), "aggregate and matrix evaluators must match")
    providers = {str(target["provider"]).casefold() for target in aggregate["targets"]}
    matrix_providers = _matrix_provider_set(matrix)
    missing = sorted(set(required_providers) - providers)
    missing_matrix = sorted(set(required_providers) - matrix_providers)
    add("provider coverage", not missing, "missing aggregate providers: " + (", ".join(missing) or "none"))
    add("matrix coverage", not missing_matrix, "missing matrix providers: " + (", ".join(missing_matrix) or "none"))
    repetition_failures = [target["key"] for target in aggregate["targets"] if target["repetitions"] < minimum_repetitions]
    add("repetitions", not repetition_failures, "targets below minimum: " + (", ".join(repetition_failures) or "none"))
    case_failures = [target["key"] for target in aggregate["targets"] if target["minimum_cases"] < minimum_cases]
    add("case coverage", not case_failures, "targets below case minimum: " + (", ".join(case_failures) or "none"))
    critical_targets = [target["key"] for target in aggregate["targets"] if target["modded_failures"]["critical"] > 0]
    add("zero critical failures", not critical_targets, "targets with critical failures: " + (", ".join(critical_targets) or "none"))
    matrix_failures = [target["key"] for target in matrix["targets"] if target["status"] != "passed"]
    add("matrix target status", not matrix_failures, "failed matrix targets: " + (", ".join(matrix_failures) or "none"))

    passed = all(check["passed"] for check in checks)
    report = {
        "schema_version": RELEASE_SCHEMA_VERSION,
        "document_type": "model-modding-v0.2-release-readiness",
        "release_engine": {"name": BUILD_ENGINE_NAME, "version": RELEASE_ENGINE_VERSION},
        "readiness_digest": "0" * 64,
        "status": "ready" if passed else "not_ready",
        "minimum_repetitions": minimum_repetitions,
        "minimum_cases": minimum_cases,
        "required_providers": list(required_providers),
        "aggregate_digest": aggregate["aggregate_digest"],
        "matrix_digest": matrix["matrix_digest"],
        "recipe": deepcopy(aggregate["recipe"]),
        "checks": checks,
        "limitations": [
            "Release readiness is authoritative only for the supplied reviewed evidence and encoded evaluator assertions.",
            "Independent reproduction and domain review remain separate release acceptance requirements.",
        ],
    }
    payload = deepcopy(report)
    payload.pop("readiness_digest")
    report["readiness_digest"] = sha256_bytes(canonical_json_bytes(payload))
    _validate(root, "release-readiness.schema.json", report)
    return report


def readiness_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Model Modding v0.2 release readiness",
        "",
        f"Status: **{report['status'].upper()}**",
        "",
        "| Check | Result | Detail |",
        "|---|---|---|",
    ]
    for check in report["checks"]:
        lines.append(f"| {check['name']} | {'PASS' if check['passed'] else 'FAIL'} | {check['detail']} |")
    lines.extend(["", f"Readiness digest: `{report['readiness_digest']}`", ""])
    return "\n".join(lines)


def write_release_readiness(root: Path, aggregate_path: Path, matrix_path: Path, output: Path, *, minimum_repetitions: int = 3, minimum_cases: int = 40) -> tuple[Path, dict[str, Any]]:
    report = check_release_readiness(
        root,
        aggregate_path,
        matrix_path,
        minimum_repetitions=minimum_repetitions,
        minimum_cases=minimum_cases,
    )
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    (output / "readiness.json").write_bytes(canonical_json_bytes(report))
    (output / "readiness.md").write_text(readiness_markdown(report), encoding="utf-8", newline="\n")
    return output, report


def build_pr_summary(
    *,
    comparison: dict[str, Any] | None = None,
    matrix: dict[str, Any] | None = None,
    aggregate: dict[str, Any] | None = None,
    readiness: dict[str, Any] | None = None,
) -> str:
    lines = ["<!-- model-modding-evidence-summary -->", "## Model Modding evidence summary", ""]
    if comparison is not None:
        pipeline = comparison["pipeline"]
        summary = comparison["summary"]
        lines.extend([
            f"- Comparison: **{pipeline['status'].upper()}**",
            f"- New failures: critical {summary['new_failures']['critical']}, major {summary['new_failures']['major']}, minor {summary['new_failures']['minor']}",
            f"- Resolved failures: critical {summary['resolved_failures']['critical']}, major {summary['resolved_failures']['major']}, minor {summary['resolved_failures']['minor']}",
            f"- Severity escalations: {summary['severity_escalations']}",
            f"- Comparison digest: `{comparison['comparison_digest']}`",
        ])
    if matrix is not None:
        failed = [target["key"] for target in matrix["targets"] if target["status"] != "passed"]
        lines.extend([
            f"- Compatibility matrix targets: {matrix['target_count']}",
            f"- Matrix failed targets: {', '.join(failed) if failed else 'none'}",
            f"- Matrix digest: `{matrix['matrix_digest']}`",
        ])
    if aggregate is not None:
        lines.extend([
            f"- Repeated evidence: **{aggregate['pipeline']['status'].upper()}**",
            f"- Evidence bundles: {aggregate['evidence_count']}",
            f"- Aggregate digest: `{aggregate['aggregate_digest']}`",
        ])
    if readiness is not None:
        lines.extend([
            f"- v0.2 readiness: **{readiness['status'].upper()}**",
            f"- Readiness digest: `{readiness['readiness_digest']}`",
        ])
    if all(value is None for value in (comparison, matrix, aggregate, readiness)):
        lines.append("- No evidence report was supplied.")
    lines.extend([
        "",
        "> Passing evidence is contextual to the exact locked build, fixture set, evaluator, provider, model and recorded configuration.",
        "",
    ])
    return "\n".join(lines)


def write_pr_summary(
    output: Path,
    *,
    comparison_path: Path | None = None,
    matrix_path: Path | None = None,
    aggregate_path: Path | None = None,
    readiness_path: Path | None = None,
    append_github_summary: bool = False,
) -> Path:
    summary = build_pr_summary(
        comparison=_read_json(comparison_path) if comparison_path else None,
        matrix=_read_json(matrix_path) if matrix_path else None,
        aggregate=_read_json(aggregate_path) if aggregate_path else None,
        readiness=_read_json(readiness_path) if readiness_path else None,
    )
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(summary, encoding="utf-8", newline="\n")
    if append_github_summary:
        summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary_path:
            with Path(summary_path).open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(summary)
    return output


def validate_provider_run_plan(
    *,
    provider: str,
    model: str,
    repetitions: int,
    max_tokens: int,
    case_limit: int,
    allowlist: str,
) -> dict[str, Any]:
    provider = provider.casefold().strip()
    allowed_providers = {"anthropic", "openai"}
    if provider not in allowed_providers:
        raise ValueError("Protected cloud workflow provider must be anthropic or openai")
    if not 1 <= repetitions <= 3:
        raise ValueError("repetitions must be between 1 and 3")
    if not 1 <= max_tokens <= 1024:
        raise ValueError("max_tokens must be between 1 and 1024")
    if case_limit not in {5, 10, 40}:
        raise ValueError("case_limit must be one of 5, 10 or 40")
    allowed = {item.strip() for item in allowlist.split(",") if item.strip()}
    if not allowed:
        raise ValueError("MODEL_MODDING_ALLOWED_MODELS must contain an explicit model allowlist")
    if model not in allowed:
        raise ValueError(f"Model {model!r} is not in MODEL_MODDING_ALLOWED_MODELS")
    return {
        "provider": provider,
        "model": model,
        "repetitions": repetitions,
        "max_tokens": max_tokens,
        "case_limit": case_limit,
    }
