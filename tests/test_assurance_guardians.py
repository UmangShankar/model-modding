from pathlib import Path

import yaml

from model_modding.cli import compose_recipe
from model_modding.evaluation import load_evaluation_cases


ROOT = Path(__file__).resolve().parents[1]
GUARDIANS = {
    "deadline-guardian": {
        "preserve": {"deadline", "date", "duration"},
        "prohibit": {"invented_deadline"},
    },
    "obligation-guardian": {
        "preserve": {"named_party", "obligation", "prohibition"},
        "prohibit": {"weakened_obligation"},
    },
    "exception-guardian": {
        "preserve": {"condition", "exception", "eligibility_rule", "sequence"},
        "prohibit": {"removed_exception"},
    },
    "source-grounding-guardian": {
        "preserve": {"source_claim", "uncertainty"},
        "prohibit": {
            "unsupported_advice",
            "invented_source_claim",
            "fabricated_citation",
            "presented_missing_evidence",
        },
    },
}



def load_manifest(name: str) -> dict:
    path = ROOT / "mods" / "safety" / name / "mod.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))



def test_guardian_packages_are_complete_and_assurance_only() -> None:
    for name in GUARDIANS:
        directory = ROOT / "mods" / "safety" / name
        for relative in (
            "mod.yaml",
            "README.md",
            "instructions/system.md",
            "examples/README.md",
            "evaluations/cases.yaml",
        ):
            assert (directory / relative).is_file(), f"{name} missing {relative}"
        manifest = load_manifest(name)
        assert manifest["role"] == "assurance"
        assert manifest["status"] == "experimental"
        assert manifest["compatible_models"] == []



def test_guardians_own_non_overlapping_invariant_sets() -> None:
    observed_preserve: set[str] = set()
    observed_prohibit: set[str] = set()

    for name, expected in GUARDIANS.items():
        manifest = load_manifest(name)
        preserve = {entry["type"] for entry in manifest["invariants"]["preserve"]}
        prohibit = {entry["type"] for entry in manifest["invariants"]["prohibit"]}
        assert preserve == expected["preserve"]
        assert prohibit == expected["prohibit"]
        assert observed_preserve.isdisjoint(preserve), f"duplicate preserved invariant in {name}"
        assert observed_prohibit.isdisjoint(prohibit), f"duplicate prohibition in {name}"
        observed_preserve.update(preserve)
        observed_prohibit.update(prohibit)



def test_every_guardian_has_independent_evaluation_coverage() -> None:
    for name in GUARDIANS:
        path = ROOT / "mods" / "safety" / name / "evaluations" / "cases.yaml"
        cases = yaml.safe_load(path.read_text(encoding="utf-8"))["cases"]
        assert len(cases) >= 4
        assert all(case.get("expected_behaviours") for case in cases)
        assert all(case.get("failure_indicators") for case in cases)
        assert all(case.get("checks") for case in cases)



def test_flagship_recipe_compiles_transformation_before_guardians(tmp_path: Path) -> None:
    assert compose_recipe(ROOT, "trusted-document-explainer", tmp_path) == 0
    prompt = (tmp_path / "system.md").read_text(encoding="utf-8")
    headings = [
        "Mod: domain/plain-language-explainer",
        "Mod: safety/deadline-guardian",
        "Mod: safety/obligation-guardian",
        "Mod: safety/exception-guardian",
        "Mod: safety/source-grounding-guardian",
    ]
    positions = [prompt.index(heading) for heading in headings]
    assert positions == sorted(positions)



def test_flagship_evaluation_plan_includes_each_guardian() -> None:
    compiled, cases = load_evaluation_cases(ROOT, "trusted-document-explainer")
    assert compiled.references == (
        "domain/plain-language-explainer",
        "safety/deadline-guardian",
        "safety/obligation-guardian",
        "safety/exception-guardian",
        "safety/source-grounding-guardian",
    )
    by_mod = {case.mod for case in cases}
    assert by_mod == set(compiled.references)
    assert len(cases) >= 22
