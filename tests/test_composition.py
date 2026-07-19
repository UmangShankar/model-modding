from __future__ import annotations

import json
from pathlib import Path

from model_modding.cli import compose_recipe, inspect_mod, resolve_mod

ROOT = Path(__file__).resolve().parents[1]


def test_resolve_mod_accepts_full_reference() -> None:
    reference, path, manifest = resolve_mod(ROOT, "personality/socratic-teacher")
    assert reference == "personality/socratic-teacher"
    assert path.name == "mod.yaml"
    assert manifest["name"] == "socratic-teacher"


def test_inspect_mod_reports_evaluation_coverage(capsys) -> None:
    assert inspect_mod(ROOT, "citation-guardian") == 0
    output = capsys.readouterr().out
    assert "citation-guardian" in output
    assert "Evaluation cases: 5" in output


def test_compose_recipe_writes_deterministic_outputs(tmp_path: Path) -> None:
    assert compose_recipe(ROOT, "research-learning-companion", tmp_path) == 0
    system_prompt = (tmp_path / "system.md").read_text(encoding="utf-8")
    metadata = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert system_prompt.index("Mod: personality/socratic-teacher") < system_prompt.index("Mod: safety/citation-guardian")
    assert "Ask one high-value question at a time" in system_prompt
    assert "Never invent a citation" in system_prompt
    assert [mod["reference"] for mod in metadata["mods"]] == [
        "personality/socratic-teacher",
        "safety/citation-guardian",
    ]


def test_compose_recipe_rejects_missing_mod(tmp_path: Path) -> None:
    recipe_dir = tmp_path / "recipes" / "broken"
    recipe_dir.mkdir(parents=True)
    (recipe_dir / "recipe.yaml").write_text(
        "name: broken\nversion: 0.1.0\ndescription: A deliberately broken recipe for testing missing references.\nmods:\n  - safety/not-real\nlicense: Apache-2.0\n",
        encoding="utf-8",
    )
    (tmp_path / "mods").mkdir()
    assert compose_recipe(tmp_path, "broken", tmp_path / "build") == 1
