from __future__ import annotations

from collections import Counter
from pathlib import Path

import yaml

from model_modding.evaluation import load_evaluation_cases

ROOT = Path(__file__).resolve().parents[1]
GUARDIANS = (
    "deadline-guardian",
    "obligation-guardian",
    "exception-guardian",
    "source-grounding-guardian",
)
EXPECTED_COUNTS = {
    "deadline-guardian": 5,
    "obligation-guardian": 5,
    "exception-guardian": 4,
    "source-grounding-guardian": 4,
}
ALLOWED_FIXTURE_TYPES = {"adversarial", "paraphrase"}
ALLOWED_ATTACK_TYPES = {
    "boundary-omission",
    "certainty-inflation",
    "citation-invention",
    "condition-softening",
    "deadline-invention",
    "deadline-substitution",
    "eligibility-inflation",
    "exception-erasure",
    "fabrication-pressure",
    "false-premise",
    "instruction-conflict",
    "missing-evidence",
    "modality-flip",
    "omission-pressure",
    "paraphrase",
    "passive-voice",
    "prohibition-reversal",
    "role-collapse",
    "role-swap",
    "sequence-collapse",
    "trigger-shift",
    "unit-substitution",
}


def load_adversarial_cases() -> list[tuple[str, dict]]:
    loaded: list[tuple[str, dict]] = []
    for guardian in GUARDIANS:
        path = ROOT / "mods" / "safety" / guardian / "evaluations" / "adversarial.yaml"
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert isinstance(payload, dict)
        cases = payload.get("cases")
        assert isinstance(cases, list)
        loaded.extend((guardian, case) for case in cases)
    return loaded


def test_flagship_reaches_forty_cases() -> None:
    _, cases = load_evaluation_cases(ROOT, "trusted-document-explainer")

    assert len(cases) == 40
    identities = [(case.mod, case.name) for case in cases]
    assert len(identities) == len(set(identities))


def test_adversarial_case_distribution_is_balanced() -> None:
    cases = load_adversarial_cases()
    counts = Counter(guardian for guardian, _ in cases)

    assert len(cases) == 18
    assert counts == EXPECTED_COUNTS
    assert sum(case["fixture_type"] == "paraphrase" for _, case in cases) >= 5
    assert sum(case["fixture_type"] == "adversarial" for _, case in cases) >= 13


def test_every_new_fixture_is_classified_and_invariant_aware() -> None:
    cases = load_adversarial_cases()

    for guardian, case in cases:
        assert isinstance(case, dict)
        assert case["fixture_type"] in ALLOWED_FIXTURE_TYPES
        attack_types = case.get("attack_types")
        assert isinstance(attack_types, list) and attack_types
        assert set(attack_types).issubset(ALLOWED_ATTACK_TYPES)
        assert isinstance(case.get("expected_behaviours"), list) and case["expected_behaviours"]
        assert isinstance(case.get("failure_indicators"), list) and case["failure_indicators"]
        assert isinstance(case.get("checks"), dict) and case["checks"]
        invariant_checks = case.get("invariant_checks")
        assert isinstance(invariant_checks, list) and invariant_checks, f"{guardian}:{case.get('name')}"
        for target in invariant_checks:
            assert target["kind"] in {"preserve", "prohibit"}
            assert target["severity"] in {"critical", "major", "minor"}
            assert isinstance(target.get("checks"), dict) and target["checks"]


def test_attack_taxonomy_covers_high_risk_failure_modes() -> None:
    attack_types = {
        attack
        for _, case in load_adversarial_cases()
        for attack in case["attack_types"]
    }

    required = {
        "unit-substitution",
        "trigger-shift",
        "deadline-invention",
        "role-swap",
        "modality-flip",
        "prohibition-reversal",
        "exception-erasure",
        "sequence-collapse",
        "fabrication-pressure",
        "false-premise",
        "certainty-inflation",
        "missing-evidence",
    }
    assert required.issubset(attack_types)
    assert len(attack_types) >= 18
