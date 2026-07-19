from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "mods/domain/plain-language-explainer"
RECIPE = ROOT / "recipes/trusted-document-explainer/recipe.yaml"


def test_plain_language_explainer_package_is_complete() -> None:
    for relative in (
        "mod.yaml",
        "README.md",
        "instructions/system.md",
        "examples/README.md",
        "evaluations/cases.yaml",
    ):
        assert (MOD / relative).is_file()


def test_instructions_preserve_material_meaning_and_boundaries() -> None:
    content = (MOD / "instructions/system.md").read_text(encoding="utf-8")
    for expected in (
        "Preserve dates, amounts, deadlines, conditions, exceptions",
        "Distinguish clearly between what the source states",
        "Do not invent missing definitions",
        "not professional advice",
        "What you may need to do next",
    ):
        assert expected in content


def test_evaluations_cover_real_document_risks() -> None:
    payload = yaml.safe_load((MOD / "evaluations/cases.yaml").read_text(encoding="utf-8"))
    cases = payload["cases"]
    assert len(cases) >= 6
    names = {case["name"] for case in cases}
    assert {
        "preserve-contract-deadline-and-exception",
        "medical-letter-boundary",
        "government-deadline-with-discretion",
        "distinguish-source-from-interpretation",
        "incomplete-source",
        "explain-jargon-without-deleting-it",
    }.issubset(names)
    assert all(case.get("checks") for case in cases)


def test_trusted_document_recipe_composes_citation_guardian() -> None:
    recipe = yaml.safe_load(RECIPE.read_text(encoding="utf-8"))
    assert recipe["mods"] == [
        "domain/plain-language-explainer",
        "safety/citation-guardian",
    ]
