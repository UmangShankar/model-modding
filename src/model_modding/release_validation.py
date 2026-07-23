from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .evidence import verify_evidence_bundle


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
    """Validate one evidence bundle for use in a reviewed release candidate."""
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
