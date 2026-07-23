from __future__ import annotations

import json
import sys
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator

from .builds import BUILD_ENGINE_NAME, canonical_json_bytes, sha256_bytes
from .evaluation import FAIL_ON_VALUES, SEVERITIES, is_blocking_severity
from .evidence import verify_evidence_bundle

COMPARISON_SCHEMA_VERSION = "0.1"
COMPARISON_ENGINE_VERSION = "0.1.0"
SEVERITY_RANK = {"minor": 1, "major": 2, "critical": 3}


def _load_schema(root: Path, name: str) -> dict[str, Any]:
    schema = json.loads((root / "schemas" / name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema


def _validate(root: Path, schema_name: str, value: dict[str, Any]) -> None:
    schema = _load_schema(root, schema_name)
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


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def _load_bundle(root: Path, directory: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    failures = verify_evidence_bundle(root, directory)
    if failures:
        raise ValueError(
            f"Evidence bundle failed verification: {directory.resolve()}: "
            + "; ".join(failures)
        )
    manifest = _read_json(directory / "manifest.json")
    evaluation_path = directory / "evaluation.json"
    if not evaluation_path.exists():
        raise ValueError(
            f"Evidence bundle has no evaluation.json and cannot be compared: {directory.resolve()}"
        )
    evaluation = _read_json(evaluation_path)
    return manifest, evaluation


def _bundle_descriptor(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "evidence_digest": manifest["evidence_digest"],
        "bundle_type": manifest["bundle_type"],
        "created_at": manifest["created_at"],
        "recipe": deepcopy(manifest["recipe"]),
        "runtime": deepcopy(manifest["runtime"]),
        "evaluator": deepcopy(manifest.get("evaluator")),
        "fixture_set_digest": manifest.get("fixture_set_digest"),
        "source_control": deepcopy(manifest["source_control"]),
    }


def _failure_identity(failure: dict[str, Any]) -> str:
    identifier = failure.get("id")
    if isinstance(identifier, str) and identifier:
        return identifier
    fields = (
        failure.get("mod"),
        failure.get("case"),
        failure.get("layer"),
        failure.get("kind"),
        failure.get("invariant"),
        failure.get("source_fact_id"),
        failure.get("description"),
    )
    return "|".join("" if value is None else str(value) for value in fields)


def _failure_map(failures: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    mapped: dict[str, dict[str, Any]] = {}
    for failure in failures:
        key = _failure_identity(failure)
        if key in mapped:
            raise ValueError(f"Duplicate failure identity in evidence: {key}")
        mapped[key] = deepcopy(failure)
    return mapped


def _severity_counts(failures: Iterable[dict[str, Any]]) -> dict[str, int]:
    values = list(failures)
    return {
        severity: sum(1 for failure in values if failure.get("severity") == severity)
        for severity in SEVERITIES
    }


def _target_key(provider: str, model: str) -> str:
    return f"{provider.casefold()}/{model}"


def _target_from_evaluation(
    manifest: dict[str, Any],
    report: dict[str, Any],
) -> dict[str, Any]:
    provider = str(manifest["runtime"]["provider"]).casefold()
    requested_models = list(manifest["runtime"].get("requested_models", []))
    model = str(report.get("model") or (requested_models[0] if requested_models else ""))
    if not model:
        raise ValueError("Evaluation evidence does not identify a model")
    failures = report.get("failures", {})
    return {
        "key": _target_key(provider, model),
        "provider": provider,
        "model": model,
        "runtime": deepcopy(manifest["runtime"]),
        "summary": deepcopy(report.get("summary", {})),
        "failures": {
            "stock": deepcopy(failures.get("stock", [])),
            "modded": deepcopy(failures.get("modded", [])),
        },
        "cases": deepcopy(report.get("cases", [])),
    }


def _targets_from_benchmark(
    manifest: dict[str, Any],
    report: dict[str, Any],
) -> list[dict[str, Any]]:
    provider = str(manifest["runtime"]["provider"]).casefold()
    targets: list[dict[str, Any]] = []
    for model_report in report.get("models", []):
        if not isinstance(model_report, dict) or model_report.get("status") != "completed":
            continue
        model = str(model_report.get("resolved_model") or model_report.get("model") or "")
        if not model:
            raise ValueError("Completed benchmark target does not identify a model")
        failures = model_report.get("failures", {})
        targets.append(
            {
                "key": _target_key(provider, model),
                "provider": provider,
                "model": model,
                "runtime": deepcopy(model_report.get("execution", manifest["runtime"])),
                "summary": deepcopy(model_report.get("summary", {})),
                "failures": {
                    "stock": deepcopy(failures.get("stock", [])),
                    "modded": deepcopy(failures.get("modded", [])),
                },
                "cases": deepcopy(model_report.get("cases", [])),
            }
        )
    if not targets:
        raise ValueError("Benchmark evidence has no completed model targets")
    return targets


def _extract_targets(
    manifest: dict[str, Any],
    evaluation: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    if manifest["bundle_type"] == "evaluation":
        targets = [_target_from_evaluation(manifest, evaluation)]
    elif manifest["bundle_type"] == "benchmark":
        targets = _targets_from_benchmark(manifest, evaluation)
    else:
        raise ValueError(
            f"Bundle type {manifest['bundle_type']!r} has no comparable evaluator output"
        )
    mapped: dict[str, dict[str, Any]] = {}
    for target in targets:
        key = target["key"]
        if key in mapped:
            raise ValueError(f"Duplicate provider/model target in evidence: {key}")
        mapped[key] = target
    return mapped


def _comparability_checks(
    baseline_manifest: dict[str, Any],
    candidate_manifest: dict[str, Any],
    baseline_targets: dict[str, dict[str, Any]],
    candidate_targets: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    pairs = [
        ("bundle_type", baseline_manifest["bundle_type"], candidate_manifest["bundle_type"]),
        ("recipe.name", baseline_manifest["recipe"]["name"], candidate_manifest["recipe"]["name"]),
        ("recipe.version", baseline_manifest["recipe"]["version"], candidate_manifest["recipe"]["version"]),
        ("recipe.source_digest", baseline_manifest["recipe"]["source_digest"], candidate_manifest["recipe"]["source_digest"]),
        ("recipe.build_digest", baseline_manifest["recipe"]["build_digest"], candidate_manifest["recipe"]["build_digest"]),
        ("fixture_set_digest", baseline_manifest.get("fixture_set_digest"), candidate_manifest.get("fixture_set_digest")),
        ("evaluator", baseline_manifest.get("evaluator"), candidate_manifest.get("evaluator")),
        ("target_keys", sorted(baseline_targets), sorted(candidate_targets)),
    ]
    return [
        {
            "field": field,
            "baseline": baseline,
            "candidate": candidate,
            "matched": baseline == candidate,
            "required": True,
        }
        for field, baseline, candidate in pairs
    ]


def _compare_target(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    fail_on: str,
) -> dict[str, Any]:
    baseline_failures = _failure_map(baseline["failures"]["modded"])
    candidate_failures = _failure_map(candidate["failures"]["modded"])
    baseline_ids = set(baseline_failures)
    candidate_ids = set(candidate_failures)

    new_failures = [candidate_failures[key] for key in sorted(candidate_ids - baseline_ids)]
    resolved_failures = [baseline_failures[key] for key in sorted(baseline_ids - candidate_ids)]
    unchanged: list[dict[str, Any]] = []
    severity_changes: list[dict[str, Any]] = []
    escalations: list[dict[str, Any]] = []
    for key in sorted(baseline_ids & candidate_ids):
        before = baseline_failures[key]
        after = candidate_failures[key]
        before_severity = str(before.get("severity", ""))
        after_severity = str(after.get("severity", ""))
        if before_severity == after_severity:
            unchanged.append(after)
            continue
        change = {
            "id": key,
            "baseline_severity": before_severity,
            "candidate_severity": after_severity,
            "failure": after,
        }
        severity_changes.append(change)
        if SEVERITY_RANK.get(after_severity, 0) > SEVERITY_RANK.get(before_severity, 0):
            escalations.append(change)

    blocking_failures = [
        failure
        for failure in new_failures
        if is_blocking_severity(str(failure.get("severity", "")), fail_on)
    ]
    blocking_escalations = [
        change
        for change in escalations
        if is_blocking_severity(change["candidate_severity"], fail_on)
    ]
    return {
        "key": candidate["key"],
        "provider": candidate["provider"],
        "model": candidate["model"],
        "runtime_changed": baseline.get("runtime") != candidate.get("runtime"),
        "baseline": {
            "summary": deepcopy(baseline.get("summary", {})),
            "modded_failures": _severity_counts(baseline_failures.values()),
        },
        "candidate": {
            "summary": deepcopy(candidate.get("summary", {})),
            "modded_failures": _severity_counts(candidate_failures.values()),
        },
        "new_failures": new_failures,
        "resolved_failures": resolved_failures,
        "unchanged_failures": unchanged,
        "severity_changes": severity_changes,
        "severity_escalations": escalations,
        "blocking_failures": blocking_failures,
        "blocking_escalations": blocking_escalations,
    }


def compare_evidence(
    root: Path,
    baseline_directory: Path,
    candidate_directory: Path,
    *,
    fail_on: str = "critical",
) -> dict[str, Any]:
    if fail_on not in FAIL_ON_VALUES:
        raise ValueError(f"fail_on must be one of: {', '.join(FAIL_ON_VALUES)}")
    baseline_manifest, baseline_evaluation = _load_bundle(root, baseline_directory)
    candidate_manifest, candidate_evaluation = _load_bundle(root, candidate_directory)
    baseline_targets = _extract_targets(baseline_manifest, baseline_evaluation)
    candidate_targets = _extract_targets(candidate_manifest, candidate_evaluation)
    checks = _comparability_checks(
        baseline_manifest,
        candidate_manifest,
        baseline_targets,
        candidate_targets,
    )
    comparable = all(check["matched"] for check in checks)
    target_reports: list[dict[str, Any]] = []
    if comparable:
        target_reports = [
            _compare_target(baseline_targets[key], candidate_targets[key], fail_on)
            for key in sorted(candidate_targets)
        ]

    blocking_failures = [
        {"target": target["key"], **failure}
        for target in target_reports
        for failure in target["blocking_failures"]
    ]
    blocking_escalations = [
        {"target": target["key"], **change}
        for target in target_reports
        for change in target["blocking_escalations"]
    ]
    if not comparable:
        pipeline_status = "not_comparable"
    elif blocking_failures or blocking_escalations:
        pipeline_status = "failed"
    else:
        pipeline_status = "passed"

    summary = {
        "targets": len(target_reports),
        "new_failures": _severity_counts(
            failure for target in target_reports for failure in target["new_failures"]
        ),
        "resolved_failures": _severity_counts(
            failure for target in target_reports for failure in target["resolved_failures"]
        ),
        "severity_escalations": len(
            [change for target in target_reports for change in target["severity_escalations"]]
        ),
        "runtime_changes": sum(1 for target in target_reports if target["runtime_changed"]),
    }
    report = {
        "schema_version": COMPARISON_SCHEMA_VERSION,
        "document_type": "model-modding-evidence-comparison",
        "comparison_engine": {
            "name": BUILD_ENGINE_NAME,
            "version": COMPARISON_ENGINE_VERSION,
        },
        "comparison_digest": "0" * 64,
        "baseline": _bundle_descriptor(baseline_manifest),
        "candidate": _bundle_descriptor(candidate_manifest),
        "comparability": {
            "status": "comparable" if comparable else "not_comparable",
            "checks": checks,
        },
        "summary": summary,
        "pipeline": {
            "status": pipeline_status,
            "fail_on": fail_on,
            "blocking_failure_count": len(blocking_failures) + len(blocking_escalations),
            "blocking_failures": blocking_failures,
            "blocking_escalations": blocking_escalations,
        },
        "targets": target_reports,
        "limitations": [
            "Comparison is authoritative only for the evaluator assertions encoded in the evidence bundles.",
            "A passing comparison does not prove semantic correctness or universal provider compatibility.",
            "Runtime changes are reported but do not by themselves make otherwise matching evidence incomparable.",
        ],
    }
    digest_payload = deepcopy(report)
    digest_payload.pop("comparison_digest")
    report["comparison_digest"] = sha256_bytes(canonical_json_bytes(digest_payload))
    _validate(root, "evidence-comparison.schema.json", report)
    return report


def _target_observations(target: dict[str, Any]) -> dict[tuple[str, str, str], dict[str, int]]:
    observations: dict[tuple[str, str, str], dict[str, int]] = defaultdict(
        lambda: {"tested": 0, "passed": 0, "failed": 0}
    )
    for row in target.get("cases", []):
        if not isinstance(row, dict):
            continue
        modded = row.get("modded", {})
        if not isinstance(modded, dict):
            continue
        for field in ("invariant_checks", "source_comparisons"):
            for item in modded.get(field, []):
                if not isinstance(item, dict):
                    continue
                key = (
                    str(item.get("kind", "")),
                    str(item.get("invariant", "")),
                    str(item.get("severity", "")),
                )
                if not all(key):
                    continue
                observation = observations[key]
                observation["tested"] += 1
                if item.get("passed") is True:
                    observation["passed"] += 1
                else:
                    observation["failed"] += 1
    return dict(observations)


def build_compatibility_matrix(
    root: Path,
    directories: list[Path],
) -> dict[str, Any]:
    if not directories:
        raise ValueError("At least one evidence bundle is required")
    loaded = [_load_bundle(root, directory) for directory in directories]
    manifests = [item[0] for item in loaded]
    reference = manifests[0]
    checks: list[dict[str, Any]] = []
    for index, manifest in enumerate(manifests[1:], 2):
        for field, left, right in (
            ("recipe.name", reference["recipe"]["name"], manifest["recipe"]["name"]),
            ("recipe.version", reference["recipe"]["version"], manifest["recipe"]["version"]),
            ("recipe.source_digest", reference["recipe"]["source_digest"], manifest["recipe"]["source_digest"]),
            ("recipe.build_digest", reference["recipe"]["build_digest"], manifest["recipe"]["build_digest"]),
            ("fixture_set_digest", reference.get("fixture_set_digest"), manifest.get("fixture_set_digest")),
            ("evaluator", reference.get("evaluator"), manifest.get("evaluator")),
        ):
            checks.append(
                {
                    "bundle": index,
                    "field": field,
                    "reference": left,
                    "actual": right,
                    "matched": left == right,
                }
            )
    mismatches = [check for check in checks if not check["matched"]]
    if mismatches:
        fields = ", ".join(
            f"bundle {item['bundle']} {item['field']}" for item in mismatches
        )
        raise ValueError(f"Evidence bundles are not matrix-compatible: {fields}")

    targets: dict[str, dict[str, Any]] = {}
    for manifest, evaluation in loaded:
        for key, target in _extract_targets(manifest, evaluation).items():
            if key in targets:
                raise ValueError(f"Duplicate provider/model target across evidence bundles: {key}")
            target["evidence_digest"] = manifest["evidence_digest"]
            targets[key] = target

    invariant_rows: dict[tuple[str, str, str], dict[str, Any]] = {}
    target_rows: list[dict[str, Any]] = []
    for key in sorted(targets):
        target = targets[key]
        observations = _target_observations(target)
        target_failures = target["failures"]["modded"]
        target_rows.append(
            {
                "key": key,
                "provider": target["provider"],
                "model": target["model"],
                "evidence_digest": target["evidence_digest"],
                "status": "passed" if not target_failures else "failed",
                "modded_failures": _severity_counts(target_failures),
                "invariant_observations": sum(value["tested"] for value in observations.values()),
            }
        )
        for invariant_key, counts in observations.items():
            row = invariant_rows.setdefault(
                invariant_key,
                {
                    "kind": invariant_key[0],
                    "invariant": invariant_key[1],
                    "severity": invariant_key[2],
                    "targets": {},
                },
            )
            row["targets"][key] = {
                **counts,
                "status": "passed" if counts["failed"] == 0 else "failed",
            }

    rows = [
        invariant_rows[key]
        for key in sorted(invariant_rows, key=lambda item: (item[1], item[0], item[2]))
    ]
    report = {
        "schema_version": COMPARISON_SCHEMA_VERSION,
        "document_type": "model-modding-compatibility-matrix",
        "comparison_engine": {
            "name": BUILD_ENGINE_NAME,
            "version": COMPARISON_ENGINE_VERSION,
        },
        "matrix_digest": "0" * 64,
        "recipe": deepcopy(reference["recipe"]),
        "evaluator": deepcopy(reference.get("evaluator")),
        "fixture_set_digest": reference.get("fixture_set_digest"),
        "target_count": len(target_rows),
        "targets": target_rows,
        "invariants": rows,
        "limitations": [
            "The matrix describes only the invariant and source assertions encoded in the supplied evidence.",
            "A passed cell is not a universal model or provider compatibility claim.",
            "Human and domain review remain required for high-stakes compatibility claims.",
        ],
    }
    digest_payload = deepcopy(report)
    digest_payload.pop("matrix_digest")
    report["matrix_digest"] = sha256_bytes(canonical_json_bytes(digest_payload))
    _validate(root, "compatibility-matrix.schema.json", report)
    return report


def comparison_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Evidence comparison",
        "",
        f"- Status: **{report['pipeline']['status'].upper()}**",
        f"- Failure threshold: `{report['pipeline']['fail_on']}`",
        f"- Baseline evidence: `{report['baseline']['evidence_digest']}`",
        f"- Candidate evidence: `{report['candidate']['evidence_digest']}`",
        f"- Build digest: `{report['candidate']['recipe']['build_digest']}`",
        f"- Fixture set: `{report['candidate']['fixture_set_digest']}`",
        f"- Comparison digest: `{report['comparison_digest']}`",
        "",
        "## Comparability",
        "",
        "| Field | Match |",
        "| --- | --- |",
    ]
    for check in report["comparability"]["checks"]:
        lines.append(f"| `{check['field']}` | {'yes' if check['matched'] else 'no'} |")
    if report["comparability"]["status"] == "not_comparable":
        lines.extend(["", "The evidence bundles are not comparable under the strict contract.", ""])
        return "\n".join(lines)

    summary = report["summary"]
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Targets: {summary['targets']}",
            f"- New critical failures: {summary['new_failures']['critical']}",
            f"- New major failures: {summary['new_failures']['major']}",
            f"- New minor failures: {summary['new_failures']['minor']}",
            f"- Resolved failures: {sum(summary['resolved_failures'].values())}",
            f"- Severity escalations: {summary['severity_escalations']}",
            f"- Runtime changes: {summary['runtime_changes']}",
            "",
            "## Targets",
            "",
        ]
    )
    for target in report["targets"]:
        lines.extend(
            [
                f"### `{target['key']}`",
                "",
                f"- New failures: {len(target['new_failures'])}",
                f"- Resolved failures: {len(target['resolved_failures'])}",
                f"- Severity escalations: {len(target['severity_escalations'])}",
                f"- Runtime changed: {'yes' if target['runtime_changed'] else 'no'}",
            ]
        )
        for failure in target["new_failures"]:
            lines.append(
                f"- **NEW {str(failure.get('severity', '')).upper()}** "
                f"`{_failure_identity(failure)}`: {failure.get('description', '')}"
            )
        lines.append("")
    lines.extend(
        [
            "## Interpretation boundary",
            "",
            "This comparison reports changes in encoded evaluator assertions. It does not prove complete semantic correctness or universal compatibility.",
            "",
        ]
    )
    return "\n".join(lines)


def matrix_markdown(report: dict[str, Any]) -> str:
    target_keys = [target["key"] for target in report["targets"]]
    lines = [
        "# Compatibility matrix",
        "",
        f"- Recipe: `{report['recipe']['name']} {report['recipe']['version']}`",
        f"- Build digest: `{report['recipe']['build_digest']}`",
        f"- Fixture set: `{report['fixture_set_digest']}`",
        f"- Targets: {report['target_count']}",
        f"- Matrix digest: `{report['matrix_digest']}`",
        "",
        "## Target summary",
        "",
        "| Target | Status | Critical | Major | Minor |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for target in report["targets"]:
        failures = target["modded_failures"]
        lines.append(
            f"| `{target['key']}` | {target['status']} | {failures['critical']} | "
            f"{failures['major']} | {failures['minor']} |"
        )
    lines.extend(
        [
            "",
            "## Invariants",
            "",
            "| Invariant | Severity | " + " | ".join(f"`{key}`" for key in target_keys) + " |",
            "| --- | --- | " + " | ".join("---" for _ in target_keys) + " |",
        ]
    )
    for row in report["invariants"]:
        cells = []
        for key in target_keys:
            cell = row["targets"].get(key)
            if cell is None:
                cells.append("not tested")
            else:
                cells.append(f"{cell['status']} ({cell['passed']}/{cell['tested']})")
        lines.append(
            f"| `{row['kind']}:{row['invariant']}` | {row['severity']} | "
            + " | ".join(cells)
            + " |"
        )
    lines.extend(
        [
            "",
            "A passed cell applies only to this locked build, fixture set, evaluator and recorded provider/model configuration.",
            "",
        ]
    )
    return "\n".join(lines)


def _write_report(destination: Path, stem: str, report: dict[str, Any], markdown: str) -> Path:
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    allowed = {f"{stem}.json", f"{stem}.md"}
    unmanaged = sorted(path.name for path in destination.iterdir() if path.name not in allowed)
    if unmanaged:
        raise ValueError("Output directory contains unmanaged paths: " + ", ".join(unmanaged))
    (destination / f"{stem}.json").write_bytes(canonical_json_bytes(report))
    (destination / f"{stem}.md").write_text(markdown, encoding="utf-8", newline="\n")
    return destination


def compare_evidence_command(
    root: Path,
    baseline: Path,
    candidate: Path,
    output: Path | None = None,
    *,
    fail_on: str = "critical",
) -> int:
    try:
        report = compare_evidence(root, baseline, candidate, fail_on=fail_on)
        destination = output or root / "build" / "comparisons" / (
            report["baseline"]["evidence_digest"][:12]
            + "-to-"
            + report["candidate"]["evidence_digest"][:12]
        )
        _write_report(destination, "comparison", report, comparison_markdown(report))
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"Comparison status: {report['pipeline']['status'].upper()}")
    print(f"Comparison report: {destination.resolve() / 'comparison.json'}")
    if report["pipeline"]["status"] == "not_comparable":
        return 2
    return 1 if report["pipeline"]["status"] == "failed" else 0


def compatibility_matrix_command(
    root: Path,
    directories: list[Path],
    output: Path | None = None,
) -> int:
    try:
        report = build_compatibility_matrix(root, directories)
        destination = output or root / "build" / "matrices" / report["recipe"]["name"]
        _write_report(destination, "matrix", report, matrix_markdown(report))
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"Compatibility targets: {report['target_count']}")
    print(f"Compatibility matrix: {destination.resolve() / 'matrix.json'}")
    return 0
