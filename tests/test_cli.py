from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

from model_modding.cli import create_mod, inspect_mod, resolve_mod, validate_repository


ROOT = Path(__file__).resolve().parents[1]


def copy_repo_contract(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "schemas").mkdir(parents=True)
    (root / "templates" / "mod").mkdir(parents=True)
    (root / "mods" / "personality" / "existing").mkdir(parents=True)
    (root / "recipes" / "sample").mkdir(parents=True)

    shutil.copy(ROOT / "schemas" / "mod.schema.json", root / "schemas" / "mod.schema.json")
    shutil.copy(ROOT / "schemas" / "invariant.schema.json", root / "schemas" / "invariant.schema.json")
    shutil.copy(ROOT / "schemas" / "recipe.schema.json", root / "schemas" / "recipe.schema.json")
    shutil.copy(ROOT / "templates" / "mod" / "mod.yaml", root / "templates" / "mod" / "mod.yaml")
    shutil.copy(
        ROOT / "mods" / "personality" / "inquisitive-strategist" / "mod.yaml",
        root / "mods" / "personality" / "existing" / "mod.yaml",
    )
    shutil.copy(
        ROOT / "recipes" / "product-strategy-copilot" / "recipe.yaml",
        root / "recipes" / "sample" / "recipe.yaml",
    )
    return root


def update_existing_manifest(root: Path, **changes: object) -> Path:
    manifest_path = root / "mods" / "personality" / "existing" / "mod.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest.update(changes)
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return manifest_path


def test_validate_repository_accepts_legacy_manifest_without_invariants(tmp_path: Path) -> None:
    root = copy_repo_contract(tmp_path)
    assert validate_repository(root) == 0


def test_validate_repository_accepts_declared_invariants(tmp_path: Path) -> None:
    root = copy_repo_contract(tmp_path)
    update_existing_manifest(
        root,
        role="assurance",
        invariants={
            "preserve": [{"type": "deadline", "severity": "critical"}],
            "prohibit": [{"type": "unsupported_advice", "severity": "major"}],
        },
    )

    assert validate_repository(root) == 0


def test_validate_repository_rejects_unknown_invariant_term(tmp_path: Path, capsys) -> None:
    root = copy_repo_contract(tmp_path)
    update_existing_manifest(
        root,
        role="transformation",
        invariants={"preserve": [{"type": "made_up_term", "severity": "critical"}]},
    )

    assert validate_repository(root) == 1
    assert "made_up_term" in capsys.readouterr().err


def test_validate_repository_rejects_invalid_invariant_severity(tmp_path: Path, capsys) -> None:
    root = copy_repo_contract(tmp_path)
    update_existing_manifest(
        root,
        role="transformation",
        invariants={"preserve": [{"type": "deadline", "severity": "blocker"}]},
    )

    assert validate_repository(root) == 1
    assert "blocker" in capsys.readouterr().err


def test_validate_repository_rejects_empty_invariant_declaration(tmp_path: Path) -> None:
    root = copy_repo_contract(tmp_path)
    update_existing_manifest(root, role="transformation", invariants={})

    assert validate_repository(root) == 1


def test_validate_repository_reports_invalid_manifest(tmp_path: Path) -> None:
    root = copy_repo_contract(tmp_path)
    manifest_path = root / "mods" / "personality" / "existing" / "mod.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest.pop("name")
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    assert validate_repository(root) == 1


def test_create_mod_generates_valid_package(tmp_path: Path) -> None:
    root = copy_repo_contract(tmp_path)
    result = create_mod(root, "socratic-teacher", "personality", "Ada Example", "ada")

    assert result == 0
    destination = root / "mods" / "personality" / "socratic-teacher"
    assert (destination / "mod.yaml").exists()
    assert (destination / "README.md").exists()
    assert (destination / "instructions" / "system.md").exists()
    assert (destination / "examples" / "README.md").exists()
    assert (destination / "evaluations" / "cases.yaml").exists()
    manifest = yaml.safe_load((destination / "mod.yaml").read_text(encoding="utf-8"))
    assert manifest["role"] == "transformation"
    assert validate_repository(root) == 0


def test_create_mod_rejects_invalid_name(tmp_path: Path) -> None:
    root = copy_repo_contract(tmp_path)
    assert create_mod(root, "Bad Name", "personality", "Ada Example", None) == 2


def test_create_mod_rejects_category_outside_schema(tmp_path: Path) -> None:
    root = copy_repo_contract(tmp_path)
    assert create_mod(root, "example-mod", "custom", "Ada Example", None) == 2
    assert not (root / "mods" / "custom" / "example-mod").exists()


def test_create_mod_refuses_overwrite(tmp_path: Path) -> None:
    root = copy_repo_contract(tmp_path)
    assert create_mod(root, "new-mod", "personality", "Ada Example", None) == 0
    assert create_mod(root, "new-mod", "personality", "Ada Example", None) == 2


def test_resolve_mod_accepts_both_separator_styles(tmp_path: Path) -> None:
    root = copy_repo_contract(tmp_path)

    posix_reference, _, _ = resolve_mod(root, "personality/existing")
    windows_reference, _, _ = resolve_mod(root, "personality\\existing")

    assert posix_reference == "personality/existing"
    assert windows_reference == "personality/existing"


def test_inspect_emits_canonical_posix_reference(tmp_path: Path, capsys) -> None:
    root = copy_repo_contract(tmp_path)

    assert inspect_mod(root, "personality\\existing", as_json=True) == 0
    report = json.loads(capsys.readouterr().out)

    assert report["reference"] == "personality/existing"
    assert report["role"] is None
    assert report["invariants"] == {"preserve": [], "prohibit": []}


def test_inspect_displays_declared_role_and_invariants(capsys) -> None:
    assert inspect_mod(ROOT, "plain-language-explainer", as_json=True) == 0
    report = json.loads(capsys.readouterr().out)

    assert report["role"] == "transformation"
    assert {entry["type"] for entry in report["invariants"]["preserve"]} >= {
        "deadline",
        "obligation",
        "exception",
    }
    assert {entry["type"] for entry in report["invariants"]["prohibit"]} >= {
        "invented_deadline",
        "weakened_obligation",
        "removed_exception",
    }


def test_repository_has_one_case_insensitive_pull_request_template() -> None:
    templates = [
        path.name
        for path in (ROOT / ".github").iterdir()
        if path.is_file() and path.name.casefold() == "pull_request_template.md"
    ]
    assert templates == ["pull_request_template.md"]


def test_legacy_validator_uses_script_repository_from_other_cwd(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_manifests.py")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "All manifests are valid." in result.stdout
