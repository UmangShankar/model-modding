from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_readme_leads_with_portable_assured_behaviour() -> None:
    readme = read("README.md")

    assert "Package, test and deploy portable AI-agent behaviour." in readme
    assert "meaning-preserving, evidence-backed transformation" in readme
    assert "Trusted Document Explainer product contract" in readme
    assert "machine-readable invariant declarations are implemented" in readme
    assert "four narrow flagship assurance guardians" in readme
    assert "deterministic invariant checks bound to manifest declarations" in readme
    assert "structured source-output comparison" in readme
    assert "does not perform unrestricted semantic extraction" in readme


def test_core_vocabulary_is_documented_without_overclaiming() -> None:
    concepts = read("docs/concepts.md")
    invariants = read("docs/invariants.md")
    source_comparison = read("docs/source-output-comparison-design.md")

    assert "## Invariant" in concepts
    assert "## Evidence bundle" in concepts
    assert "## Agent Behaviour Bill of Materials" in concepts
    assert "implemented in the v0.1.2 development line" in concepts
    assert "planned for v0.1.6" in concepts
    assert "Unknown terms fail schema validation" in invariants
    assert "## Assurance guardians" in invariants
    assert "produce structured severity-aware failures" in invariants
    assert "does not yet perform general semantic extraction" in invariants
    assert "23 typed source facts" in source_comparison
    assert "cannot prove that every source fact was captured" in source_comparison


def test_non_goals_and_flagship_contract_are_explicit() -> None:
    non_goals = read("docs/non-goals.md")
    contract = read("docs/trusted-document-explainer-contract.md")

    assert "Not a universal model leaderboard" in non_goals
    assert "Not a replacement for domain review" in non_goals
    assert "This document defines the target reference product" in contract
    assert "machine-readable invariant declarations" in contract
    assert "four narrow assurance guardians" in contract
    assert "23 typed source facts" in contract
    assert "does not provide unrestricted semantic extraction" in contract
    assert "zero critical failures" in contract


def test_roadmap_preserves_incremental_release_sequence() -> None:
    roadmap = read("docs/roadmap.md")

    expected = [
        "v0.1.1 — Stabilisation and positioning",
        "v0.1.2 — Invariant specification and flagship refactor",
        "v0.1.3 — Provider-neutral runtime",
        "v0.1.4 — Anthropic provider",
        "v0.1.5 — OpenAI provider",
        "v0.1.6 — Reproducible builds, locks and ABOM",
        "v0.1.7 — Evidence comparison and regression gates",
        "v0.2.0 — Portable Assured Behaviour",
    ]

    positions = [roadmap.index(item) for item in expected]
    assert positions == sorted(positions)


def test_package_metadata_matches_v011_positioning() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)["project"]

    assert project["version"] == "0.1.1"
    assert project["description"] == "Package, test and deploy portable AI-agent behaviour with inspectable evidence."
    assert "assurance" in project["keywords"]
    assert "reproducibility" in project["keywords"]
