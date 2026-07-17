#!/usr/bin/env python3
"""Validate all Model Modding mod and recipe manifests."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML object")
    return data


def validate_group(label: str, schema_path: Path, manifests: list[Path]) -> list[str]:
    schema = load_json(schema_path)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    failures: list[str] = []

    if not manifests:
        failures.append(f"No {label} manifests found")
        return failures

    for manifest_path in manifests:
        try:
            manifest = load_yaml(manifest_path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            failures.append(f"{manifest_path.relative_to(ROOT)}: {exc}")
            continue

        errors = sorted(validator.iter_errors(manifest), key=lambda error: list(error.path))
        if errors:
            for error in errors:
                location = ".".join(str(part) for part in error.path) or "<root>"
                failures.append(
                    f"{manifest_path.relative_to(ROOT)} [{location}]: {error.message}"
                )
        else:
            print(f"PASS {manifest_path.relative_to(ROOT)}")

    return failures


def main() -> int:
    failures: list[str] = []
    failures.extend(
        validate_group(
            "mod",
            ROOT / "schemas" / "mod.schema.json",
            sorted((ROOT / "mods").glob("**/mod.yaml")),
        )
    )
    failures.extend(
        validate_group(
            "recipe",
            ROOT / "schemas" / "recipe.schema.json",
            sorted((ROOT / "recipes").glob("**/recipe.yaml")),
        )
    )

    if failures:
        print("\nValidation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("\nAll manifests are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
