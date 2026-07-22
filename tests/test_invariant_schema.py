from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from model_modding.cli import build_schema_registry, load_json

ROOT = Path(__file__).resolve().parents[1]


def mod_validator() -> Draft202012Validator:
    schema = load_json(ROOT / "schemas" / "mod.schema.json")
    registry = build_schema_registry(ROOT / "schemas")
    return Draft202012Validator(schema, registry=registry)


def test_unknown_semantic_role_is_rejected() -> None:
    manifest = yaml.safe_load(
        (ROOT / "mods" / "domain" / "plain-language-explainer" / "mod.yaml").read_text(encoding="utf-8")
    )
    manifest["role"] = "hybrid"

    errors = list(mod_validator().iter_errors(manifest))

    assert errors
    assert any("hybrid" in error.message for error in errors)


def test_invariant_schema_is_registered_by_canonical_id() -> None:
    registry = build_schema_registry(ROOT / "schemas")

    resource = registry.get("https://model-modding.org/schemas/invariant.schema.json")

    assert resource is not None
