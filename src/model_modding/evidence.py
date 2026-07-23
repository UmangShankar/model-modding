from __future__ import annotations

import json
import os
import subprocess
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .builds import BUILD_ENGINE_NAME, canonical_json_bytes, render_build, sha256_bytes

EVIDENCE_SCHEMA_VERSION = "0.1"
EVIDENCE_ENGINE_VERSION = "0.1.0"
EVIDENCE_FILENAMES = {
    "manifest.json",
    "responses.jsonl",
    "evaluation.json",
    "recipe.lock.json",
    "abom.json",
}


def _json_line(value: dict[str, Any]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _validate_manifest(root: Path, manifest: dict[str, Any]) -> None:
    schema = json.loads((root / "schemas" / "evidence-bundle.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(manifest), key=lambda item: list(item.path))
    if errors:
        detail = "; ".join(
            f"{'.'.join(str(part) for part in error.path) or '<root>'}: {error.message}"
            for error in errors
        )
        raise ValueError(f"Generated evidence bundle manifest is invalid: {detail}")


def _source_control(root: Path) -> dict[str, str | bool | None]:
    commit = os.environ.get("MODEL_MODDING_SOURCE_COMMIT") or os.environ.get("GITHUB_SHA")
    dirty: bool | None = None
    try:
        if not commit:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                capture_output=True,
                text=True,
                check=True,
            )
            commit = result.stdout.strip() or None
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
        dirty = bool(status.stdout.strip())
    except (OSError, subprocess.CalledProcessError):
        pass
    return {"commit": commit, "dirty": dirty}


def response_record(
    *,
    identifier: str,
    role: str,
    prompt: str,
    system_prompt: str,
    response: Any,
    case: str | None = None,
    mod: str | None = None,
) -> dict[str, Any]:
    text = str(response.text)
    record: dict[str, Any] = {
        "id": identifier,
        "role": role,
        "prompt_sha256": sha256_bytes(prompt.encode("utf-8")),
        "system_prompt_sha256": sha256_bytes(system_prompt.encode("utf-8")),
        "response_sha256": sha256_bytes(text.encode("utf-8")),
        "response": text,
        "execution": response.execution_metadata(),
    }
    record["execution"]["latency_seconds"] = response.latency_seconds
    if case is not None:
        record["case"] = case
    if mod is not None:
        record["mod"] = mod
    return record


def _sanitise_evaluation(report: dict[str, Any]) -> dict[str, Any]:
    clean = deepcopy(report)
    for row in clean.get("cases", []):
        if isinstance(row, dict):
            row.pop("prompt", None)
            for side in ("stock", "modded"):
                result = row.get(side)
                if isinstance(result, dict):
                    result.pop("response", None)
    for model in clean.get("models", []):
        if not isinstance(model, dict):
            continue
        for row in model.get("cases", []):
            if not isinstance(row, dict):
                continue
            row.pop("prompt", None)
            for side in ("stock", "modded"):
                result = row.get(side)
                if isinstance(result, dict):
                    result.pop("response", None)
    return clean


def _artifact(path: str, role: str, media_type: str, content: bytes) -> dict[str, Any]:
    return {
        "path": path,
        "role": role,
        "media_type": media_type,
        "sha256": sha256_bytes(content),
        "bytes": len(content),
    }


def write_evidence_bundle(
    root: Path,
    recipe_name: str,
    destination: Path,
    *,
    bundle_type: str,
    runtime: dict[str, Any],
    requested_models: list[str],
    records: list[dict[str, Any]],
    evaluation: dict[str, Any] | None = None,
    created_at: str | None = None,
) -> Path:
    if bundle_type not in {"run", "evaluation", "benchmark"}:
        raise ValueError("bundle_type must be run, evaluation or benchmark")
    if not records:
        raise ValueError("Evidence bundles require at least one raw response record")
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    unmanaged = sorted(path.name for path in destination.iterdir() if path.name not in EVIDENCE_FILENAMES)
    if unmanaged:
        raise ValueError("Evidence directory contains unmanaged paths: " + ", ".join(unmanaged))

    build_files, _ = render_build(root, recipe_name)
    lock_bytes = build_files["recipe.lock.json"]
    abom_bytes = build_files["abom.json"]
    lock = json.loads(lock_bytes)

    responses_bytes = b"".join(_json_line(record) for record in records)
    files: dict[str, bytes] = {
        "responses.jsonl": responses_bytes,
        "recipe.lock.json": lock_bytes,
        "abom.json": abom_bytes,
    }
    artifacts = [
        _artifact("responses.jsonl", "raw-responses", "application/x-ndjson", responses_bytes),
        _artifact("recipe.lock.json", "recipe-lock", "application/json", lock_bytes),
        _artifact("abom.json", "abom", "application/json", abom_bytes),
    ]
    evaluator: dict[str, Any] | None = None
    if evaluation is not None:
        clean_evaluation = _sanitise_evaluation(evaluation)
        evaluation_bytes = canonical_json_bytes(clean_evaluation)
        files["evaluation.json"] = evaluation_bytes
        artifacts.append(_artifact("evaluation.json", "evaluation", "application/json", evaluation_bytes))
        raw_evaluator = clean_evaluation.get("evaluator")
        evaluator = raw_evaluator if isinstance(raw_evaluator, dict) else None

    fixture_inputs = [
        {
            "id": record.get("id"),
            "case": record.get("case"),
            "mod": record.get("mod"),
            "prompt_sha256": record.get("prompt_sha256"),
        }
        for record in records
        if record.get("case") is not None
    ]
    fixture_digest = sha256_bytes(canonical_json_bytes(fixture_inputs)) if fixture_inputs else None
    normalised_runtime = deepcopy(runtime)
    normalised_runtime["provider"] = str(normalised_runtime.get("provider", "")).casefold()
    normalised_runtime["requested_models"] = requested_models
    normalised_runtime["requested_options"] = dict(normalised_runtime.get("requested_options", {}))

    manifest_without_digest = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "document_type": "model-modding-run-evidence",
        "evidence_engine": {"name": BUILD_ENGINE_NAME, "version": EVIDENCE_ENGINE_VERSION},
        "bundle_type": bundle_type,
        "created_at": created_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "recipe": {
            "name": lock["recipe"]["name"],
            "version": lock["recipe"]["version"],
            "source_digest": lock["source_digest"],
            "build_digest": lock["build_digest"],
            "abom_sha256": sha256_bytes(abom_bytes),
            "lock_sha256": sha256_bytes(lock_bytes),
        },
        "runtime": normalised_runtime,
        "evaluator": evaluator,
        "fixture_set_digest": fixture_digest,
        "source_control": _source_control(root),
        "privacy": {"prompt_text_included": False, "response_text_included": True},
        "response_count": len(records),
        "artifacts": sorted(artifacts, key=lambda item: item["path"]),
        "limitations": [
            "Prompt text is omitted by default; prompt hashes support identity checks without copying source documents.",
            "Raw responses are preserved separately from interpreted evaluation output.",
            "This bundle records one execution context and is not a universal provider or model compatibility claim.",
        ],
    }
    manifest = {
        **manifest_without_digest,
        "evidence_digest": sha256_bytes(canonical_json_bytes(manifest_without_digest)),
    }
    _validate_manifest(root, manifest)
    files["manifest.json"] = canonical_json_bytes(manifest)

    for stale in EVIDENCE_FILENAMES:
        path = destination / stale
        if path.exists() and stale not in files:
            path.unlink()
    for relative_path, content in files.items():
        (destination / relative_path).write_bytes(content)
    return destination


def verify_evidence_bundle(root: Path, destination: Path) -> list[str]:
    destination = destination.resolve()
    failures: list[str] = []
    manifest_path = destination / "manifest.json"
    if not manifest_path.exists():
        return ["missing artifact: manifest.json"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        _validate_manifest(root, manifest)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"invalid manifest.json: {exc}"]

    digest_payload = dict(manifest)
    claimed_digest = digest_payload.pop("evidence_digest", None)
    actual_digest = sha256_bytes(canonical_json_bytes(digest_payload))
    if claimed_digest != actual_digest:
        failures.append(f"evidence digest mismatch: expected {actual_digest}, got {claimed_digest}")

    for artifact in manifest["artifacts"]:
        path = destination / artifact["path"]
        if not path.exists():
            failures.append(f"missing artifact: {artifact['path']}")
            continue
        content = path.read_bytes()
        digest = sha256_bytes(content)
        if digest != artifact["sha256"]:
            failures.append(f"artifact mismatch: {artifact['path']} (expected {artifact['sha256']}, got {digest})")
        if len(content) != artifact["bytes"]:
            failures.append(f"artifact byte count mismatch: {artifact['path']}")

    responses_path = destination / "responses.jsonl"
    if responses_path.exists():
        records: list[dict[str, Any]] = []
        try:
            records = [json.loads(line) for line in responses_path.read_text(encoding="utf-8").splitlines() if line]
        except json.JSONDecodeError as exc:
            failures.append(f"invalid responses.jsonl: {exc}")
        if len(records) != manifest["response_count"]:
            failures.append("response count mismatch")
        for record in records:
            if "prompt" in record:
                failures.append(f"prompt text unexpectedly present in record: {record.get('id', 'unknown')}")
            response_text = str(record.get("response", ""))
            if sha256_bytes(response_text.encode("utf-8")) != record.get("response_sha256"):
                failures.append(f"response hash mismatch: {record.get('id', 'unknown')}")

    try:
        lock = json.loads((destination / "recipe.lock.json").read_text(encoding="utf-8"))
        abom = json.loads((destination / "abom.json").read_text(encoding="utf-8"))
        if sha256_bytes(canonical_json_bytes(lock["digest_inputs"])) != lock.get("build_digest"):
            failures.append("recipe lock build digest is invalid")
        if lock.get("build_digest") != manifest["recipe"]["build_digest"]:
            failures.append("manifest and recipe lock build digests differ")
        if abom.get("build_digest") != manifest["recipe"]["build_digest"]:
            failures.append("manifest and ABOM build digests differ")
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        failures.append(f"invalid build identity artifacts: {exc}")

    expected = {"manifest.json", *(artifact["path"] for artifact in manifest["artifacts"])}
    unexpected = sorted(path.name for path in destination.iterdir() if path.name not in expected)
    for name in unexpected:
        failures.append(f"unexpected artifact: {name}")
    return failures


def verify_evidence_command(root: Path, destination: Path) -> int:
    failures = verify_evidence_bundle(root, destination)
    if failures:
        print("Evidence verification failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(f"Evidence verified: {destination.resolve()}")
    return 0
