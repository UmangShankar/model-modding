from __future__ import annotations

import hashlib
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .cli import load_yaml, resolve_mod
from .ollama import compile_recipe_in_memory

BUILD_SCHEMA_VERSION = "0.1"
LOCK_SCHEMA_VERSION = "0.1"
ABOM_SCHEMA_VERSION = "0.1"
DIGEST_ALGORITHM = "sha256"
BUILD_FILENAMES = (
    "system.md",
    "recipe.lock.json",
    "abom.json",
    "abom.md",
    "manifest.json",
)


@dataclass(frozen=True)
class BuildResult:
    recipe: str
    destination: Path
    source_digest: str
    build_digest: str
    artifacts: dict[str, str]


def canonical_text_bytes(path: Path) -> bytes:
    """Return UTF-8 text bytes with platform line endings normalised to LF."""

    text = path.read_text(encoding="utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _file_record(root: Path, path: Path) -> dict[str, Any]:
    content = canonical_text_bytes(path)
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": sha256_bytes(content),
        "bytes": len(content),
    }


def _invariants(manifest: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    value = manifest.get("invariants")
    if not isinstance(value, dict):
        return {"preserve": [], "prohibit": []}
    preserve = value.get("preserve", [])
    prohibit = value.get("prohibit", [])
    return {
        "preserve": preserve if isinstance(preserve, list) else [],
        "prohibit": prohibit if isinstance(prohibit, list) else [],
    }


def _source_descriptor(root: Path, name: str) -> tuple[dict[str, Any], str]:
    recipe_path = root / "recipes" / name / "recipe.yaml"
    if not recipe_path.exists():
        raise ValueError(f"Recipe not found: {name}")
    recipe = load_yaml(recipe_path)
    compiled = compile_recipe_in_memory(root, name)
    components: list[dict[str, Any]] = []
    for order, raw_reference in enumerate(recipe["mods"], 1):
        reference, manifest_path, manifest = resolve_mod(root, raw_reference)
        instruction_paths = sorted((manifest_path.parent / "instructions").glob("**/*.md"))
        component = {
            "order": order,
            "reference": reference,
            "name": manifest["name"],
            "version": manifest["version"],
            "role": manifest.get("role"),
            "status": manifest.get("status"),
            "license": manifest.get("license"),
            "manifest": _file_record(root, manifest_path),
            "instructions": [_file_record(root, path) for path in instruction_paths],
            "capabilities": manifest.get("capabilities", []),
            "dependencies": manifest.get("dependencies", []),
            "conflicts": manifest.get("conflicts", []),
            "compatible_models": manifest.get("compatible_models", []),
            "invariants": _invariants(manifest),
        }
        component["component_digest"] = sha256_bytes(canonical_json_bytes(component))
        components.append(component)
    descriptor = {
        "recipe": {
            "name": recipe["name"],
            "version": recipe["version"],
            "description": recipe["description"].strip(),
            "license": recipe["license"],
            "configuration": recipe.get("configuration", {}),
            "manifest": _file_record(root, recipe_path),
        },
        "components": components,
    }
    return descriptor, compiled.system_prompt


def _lock_payload(descriptor: dict[str, Any], system_prompt_sha256: str) -> dict[str, Any]:
    source_digest = sha256_bytes(canonical_json_bytes(descriptor))
    build_digest = sha256_bytes(
        canonical_json_bytes(
            {
                "source_digest": source_digest,
                "system_prompt_sha256": system_prompt_sha256,
            }
        )
    )
    return {
        "schema_version": LOCK_SCHEMA_VERSION,
        "algorithm": DIGEST_ALGORITHM,
        "source_digest": source_digest,
        "build_digest": build_digest,
        "recipe": descriptor["recipe"],
        "components": descriptor["components"],
        "outputs": {
            "system_prompt": {
                "path": "system.md",
                "sha256": system_prompt_sha256,
            }
        },
    }


def _abom_payload(lock: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": ABOM_SCHEMA_VERSION,
        "document_type": "agent-behaviour-bill-of-materials",
        "algorithm": DIGEST_ALGORITHM,
        "source_digest": lock["source_digest"],
        "build_digest": lock["build_digest"],
        "recipe": lock["recipe"],
        "components": lock["components"],
        "artifacts": lock["outputs"],
        "limitations": [
            "The ABOM describes packaged behavioural inputs; it does not prove model compliance.",
            "Runtime provider, model and generation settings belong to execution evidence, not this build.",
        ],
    }


def _abom_markdown(abom: dict[str, Any]) -> str:
    recipe = abom["recipe"]
    lines = [
        f"# Agent Behaviour Bill of Materials: {recipe['name']}",
        "",
        f"- Recipe version: `{recipe['version']}`",
        f"- Recipe licence: `{recipe['license']}`",
        f"- Digest algorithm: `{abom['algorithm']}`",
        f"- Source digest: `{abom['source_digest']}`",
        f"- Build digest: `{abom['build_digest']}`",
        f"- System prompt digest: `{abom['artifacts']['system_prompt']['sha256']}`",
        "",
        "## Ordered components",
        "",
    ]
    for component in abom["components"]:
        lines.extend(
            [
                f"### {component['order']}. `{component['reference']}`",
                "",
                f"- Version: `{component['version']}`",
                f"- Role: `{component['role'] or 'not-declared'}`",
                f"- Licence: `{component['license'] or 'not-declared'}`",
                f"- Component digest: `{component['component_digest']}`",
                f"- Manifest: `{component['manifest']['path']}` (`{component['manifest']['sha256']}`)",
                "- Instruction files:",
            ]
        )
        for instruction in component["instructions"]:
            lines.append(f"  - `{instruction['path']}` (`{instruction['sha256']}`)")
        preserve = component["invariants"]["preserve"]
        prohibit = component["invariants"]["prohibit"]
        lines.append(
            "- Preserved invariants: "
            + (", ".join(f"`{item['type']}` [{item['severity']}]" for item in preserve) or "none")
        )
        lines.append(
            "- Prohibited transformations: "
            + (", ".join(f"`{item['type']}` [{item['severity']}]" for item in prohibit) or "none")
        )
        lines.append("")
    lines.extend(["## Limitations", ""])
    lines.extend(f"- {item}" for item in abom["limitations"])
    return "\n".join(lines).rstrip() + "\n"


def render_build(root: Path, name: str) -> tuple[dict[str, bytes], BuildResult]:
    descriptor, system_prompt = _source_descriptor(root, name)
    system_bytes = system_prompt.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    system_sha = sha256_bytes(system_bytes)
    lock = _lock_payload(descriptor, system_sha)
    abom = _abom_payload(lock)
    files: dict[str, bytes] = {
        "system.md": system_bytes,
        "recipe.lock.json": canonical_json_bytes(lock),
        "abom.json": canonical_json_bytes(abom),
        "abom.md": _abom_markdown(abom).encode("utf-8"),
    }
    artifact_hashes = {path: sha256_bytes(content) for path, content in files.items()}
    manifest = {
        "schema_version": BUILD_SCHEMA_VERSION,
        "document_type": "model-modding-build",
        "algorithm": DIGEST_ALGORITHM,
        "recipe": lock["recipe"]["name"],
        "recipe_version": lock["recipe"]["version"],
        "source_digest": lock["source_digest"],
        "build_digest": lock["build_digest"],
        "artifacts": [
            {"path": path, "sha256": artifact_hashes[path], "bytes": len(files[path])}
            for path in sorted(files)
        ],
    }
    files["manifest.json"] = canonical_json_bytes(manifest)
    artifacts = {path: sha256_bytes(content) for path, content in files.items()}
    return files, BuildResult(
        recipe=name,
        destination=Path(),
        source_digest=lock["source_digest"],
        build_digest=lock["build_digest"],
        artifacts=artifacts,
    )


def build_recipe(root: Path, name: str, output: Path | None = None) -> BuildResult:
    files, result = render_build(root, name)
    destination = (output or root / "build" / name).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    for stale in BUILD_FILENAMES:
        path = destination / stale
        if path.exists() and path.is_dir():
            shutil.rmtree(path)
    for relative_path, content in files.items():
        (destination / relative_path).write_bytes(content)
    return BuildResult(
        recipe=result.recipe,
        destination=destination,
        source_digest=result.source_digest,
        build_digest=result.build_digest,
        artifacts=result.artifacts,
    )


def verify_build(root: Path, name: str, build_directory: Path | None = None) -> list[str]:
    expected, _ = render_build(root, name)
    destination = (build_directory or root / "build" / name).resolve()
    failures: list[str] = []
    for relative_path, expected_content in expected.items():
        path = destination / relative_path
        if not path.exists():
            failures.append(f"missing artifact: {relative_path}")
            continue
        actual_content = path.read_bytes()
        if actual_content != expected_content:
            failures.append(
                f"artifact mismatch: {relative_path} "
                f"(expected {sha256_bytes(expected_content)}, got {sha256_bytes(actual_content)})"
            )
    unexpected = (
        sorted(path.name for path in destination.iterdir() if path.is_file() and path.name not in expected)
        if destination.exists()
        else []
    )
    for name_ in unexpected:
        failures.append(f"unexpected artifact: {name_}")
    return failures


def build_command(root: Path, name: str, output: Path | None = None) -> int:
    try:
        result = build_recipe(root, name, output)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"Built {name}")
    print(f"Destination: {result.destination}")
    print(f"Source digest: {result.source_digest}")
    print(f"Build digest: {result.build_digest}")
    print(f"ABOM: {result.destination / 'abom.json'}")
    print(f"Lock: {result.destination / 'recipe.lock.json'}")
    return 0


def verify_command(root: Path, name: str, build_directory: Path | None = None) -> int:
    try:
        failures = verify_build(root, name, build_directory)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if failures:
        print("Build verification failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    destination = (build_directory or root / "build" / name).resolve()
    print(f"Build verified: {destination}")
    return 0
