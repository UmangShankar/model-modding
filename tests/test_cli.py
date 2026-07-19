from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import yaml

from model_modding.cli import create_mod, validate_repository


ROOT = Path(__file__).resolve().parents[1]


def copy_repo_contract(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "schemas").mkdir(parents=True)
    (root / "templates" / "mod").mkdir(parents=True)
    (root / "mods" / "personality" / "existing").mkdir(parents=True)
    (root / "recipes" / "sample").mkdir(parents=True)

    shutil.copy(ROOT / "schemas" / "mod.schema.json", root / "schemas" / "mod.schema.json")
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


def test_validate_repository_accepts_current_contract(tmp_path: Path) -> None:
    root = copy_repo_contract(tmp_path)
    assert validate_repository(root) == 0


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
