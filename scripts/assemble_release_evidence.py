from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from model_modding.builds import canonical_json_bytes
from model_modding.evidence import verify_evidence_bundle
from model_modding.evidence_comparison import build_compatibility_matrix, matrix_markdown
from model_modding.release_pipeline import (
    build_pr_summary,
    check_release_readiness,
    readiness_markdown,
    write_aggregate,
)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def read_records(path: Path) -> list[dict[str, Any]]:
    try:
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read {path}: {exc}") from exc
    if not all(isinstance(record, dict) for record in records):
        raise ValueError(f"Expected JSON objects in {path}")
    return records


def validate_release_bundle(root: Path, directory: Path, *, minimum_cases: int) -> dict[str, Any]:
    failures = verify_evidence_bundle(root, directory)
    if failures:
        raise ValueError(f"Release evidence failed verification: {directory}: " + "; ".join(failures))

    manifest = read_json(directory / "manifest.json")
    if manifest.get("bundle_type") != "evaluation":
        raise ValueError(f"Release evidence must be an evaluation bundle: {directory}")

    evaluation = read_json(directory / "evaluation.json")
    rows = evaluation.get("cases")
    if not isinstance(rows, list):
        raise ValueError(f"Release evaluation cases must be a list: {directory}")
    actual_cases = len(rows)
    reported_cases = evaluation.get("summary", {}).get("cases")
    if reported_cases != actual_cases:
        raise ValueError(
            f"Release evidence case count mismatch in {directory}: "
            f"summary reports {reported_cases}, evaluation contains {actual_cases}"
        )
    if actual_cases < minimum_cases:
        raise ValueError(
            f"Release evidence contains {actual_cases} cases, below required {minimum_cases}: {directory}"
        )

    expected_pairs: set[tuple[str, str, str]] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"Release evaluation contains a non-object case: {directory}")
        mod = str(row.get("mod", ""))
        case = str(row.get("case", ""))
        if not mod or not case:
            raise ValueError(f"Release evaluation case is missing mod or case identity: {directory}")
        for role in ("stock", "modded"):
            pair = (mod, case, role)
            if pair in expected_pairs:
                raise ValueError(f"Duplicate release evaluation case identity {pair}: {directory}")
            expected_pairs.add(pair)

    records = read_records(directory / "responses.jsonl")
    actual_pairs: set[tuple[str, str, str]] = set()
    returned_models: set[str] = set()
    returned_providers: set[str] = set()
    for record in records:
        pair = (str(record.get("mod", "")), str(record.get("case", "")), str(record.get("role", "")))
        if pair in actual_pairs:
            raise ValueError(f"Duplicate release response identity {pair}: {directory}")
        actual_pairs.add(pair)
        execution = record.get("execution")
        if not isinstance(execution, dict):
            raise ValueError(f"Release response is missing execution metadata: {directory}")
        model = str(execution.get("model", ""))
        provider = str(execution.get("provider", "")).casefold()
        if not model or not provider:
            raise ValueError(f"Release response is missing returned provider/model identity: {directory}")
        returned_models.add(model)
        returned_providers.add(provider)

    if actual_pairs != expected_pairs:
        missing = sorted(expected_pairs - actual_pairs)
        unexpected = sorted(actual_pairs - expected_pairs)
        raise ValueError(
            f"Release response coverage mismatch in {directory}: missing={missing}, unexpected={unexpected}"
        )
    if len(returned_models) != 1:
        raise ValueError(f"Release evidence must contain one exact returned model: {directory}: {sorted(returned_models)}")
    if len(returned_providers) != 1:
        raise ValueError(f"Release evidence must contain one returned provider: {directory}: {sorted(returned_providers)}")

    provider = str(manifest["runtime"]["provider"]).casefold()
    requested_models = list(manifest["runtime"].get("requested_models", []))
    if len(requested_models) != 1:
        raise ValueError(f"Release evidence must identify exactly one requested model: {directory}")
    returned_model = next(iter(returned_models))
    returned_provider = next(iter(returned_providers))
    if provider != returned_provider:
        raise ValueError(
            f"Manifest provider {provider!r} does not match returned provider {returned_provider!r}: {directory}"
        )
    if requested_models[0] != returned_model:
        raise ValueError(
            f"Release model must be an exact returned model ID: requested {requested_models[0]!r}, "
            f"returned {returned_model!r}: {directory}"
        )

    return {
        "manifest": manifest,
        "provider": provider,
        "model": returned_model,
        "target_key": f"{provider}/{returned_model}",
        "cases": actual_cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--evidence-root", type=Path, default=Path("evidence/release-candidate"))
    parser.add_argument("--output", type=Path, default=Path("build/release-candidate"))
    parser.add_argument("--minimum-repetitions", type=int, default=3)
    parser.add_argument("--minimum-cases", type=int, default=40)
    args = parser.parse_args()

    root = args.root.resolve()
    evidence_root = args.evidence_root if args.evidence_root.is_absolute() else root / args.evidence_root
    output = args.output if args.output.is_absolute() else root / args.output
    bundles = sorted({path.parent for path in evidence_root.rglob("manifest.json")})
    if not bundles:
        raise SystemExit(f"No release-candidate evidence bundles found under {evidence_root}")

    descriptors = [
        validate_release_bundle(root, bundle, minimum_cases=args.minimum_cases)
        for bundle in bundles
    ]
    evidence_digests = [descriptor["manifest"]["evidence_digest"] for descriptor in descriptors]
    if len(set(evidence_digests)) != len(evidence_digests):
        raise SystemExit("Release-candidate evidence contains duplicate evidence digests; copied runs do not count as repetitions")

    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    aggregate_directory, aggregate = write_aggregate(
        root,
        bundles,
        output / "aggregate",
        minimum_repetitions=args.minimum_repetitions,
        require_zero_critical=True,
    )

    representatives: dict[str, tuple[dict[str, Any], Path]] = {}
    for descriptor, bundle in zip(descriptors, bundles):
        manifest = descriptor["manifest"]
        key = descriptor["target_key"]
        current = representatives.get(key)
        if current is None or manifest["created_at"] < current[0]["created_at"]:
            representatives[key] = (manifest, bundle)
    representative_paths = [representatives[key][1] for key in sorted(representatives)]
    matrix = build_compatibility_matrix(root, representative_paths)
    matrix_directory = output / "matrix"
    matrix_directory.mkdir()
    (matrix_directory / "matrix.json").write_bytes(canonical_json_bytes(matrix))
    (matrix_directory / "matrix.md").write_text(matrix_markdown(matrix), encoding="utf-8", newline="\n")

    readiness = check_release_readiness(
        root,
        aggregate_directory / "aggregate.json",
        matrix_directory / "matrix.json",
        minimum_repetitions=args.minimum_repetitions,
        minimum_cases=args.minimum_cases,
    )
    readiness_directory = output / "readiness"
    readiness_directory.mkdir()
    (readiness_directory / "readiness.json").write_bytes(canonical_json_bytes(readiness))
    (readiness_directory / "readiness.md").write_text(readiness_markdown(readiness), encoding="utf-8", newline="\n")

    summary = build_pr_summary(matrix=matrix, aggregate=aggregate, readiness=readiness)
    (output / "release-summary.md").write_text(summary, encoding="utf-8", newline="\n")
    print(output / "release-summary.md")
    return 0 if readiness["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
