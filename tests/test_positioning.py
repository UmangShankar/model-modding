from __future__ import annotations

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_readme_leads_with_portable_assured_behaviour() -> None:
    readme = read("README.md")

    assert "Package, test and deploy portable AI-agent behaviour." in readme
    assert "meaning-preserving, evidence-backed transformation" in readme
    assert "Trusted Document Explainer contract" in readme
    assert "machine-readable invariant declarations" in readme
    assert "four narrow flagship assurance guardians" in readme
    assert "deterministic invariant and source-output comparison" in readme
    assert "provider-neutral request, response, usage and generation-option contracts" in readme
    assert "built-in Ollama, Anthropic and OpenAI adapters" in readme
    assert "deterministic `build` and offline `verify-build` commands" in readme
    assert "Agent Behaviour Bills of Materials" in readme
    assert "durable run, evaluation and benchmark evidence bundles" in readme
    assert "versioned evidence schema and offline `verify-evidence` command" in readme
    assert "strict baseline-versus-candidate `compare-evidence` regression gates" in readme
    assert "provider/model-by-invariant `matrix-evidence` summaries" in readme
    assert "repeated-run aggregation and scoped baseline activation" in readme
    assert "automatic pull-request evidence summaries" in readme
    assert "protected and cost-limited provider workflows" in readme
    assert "v0.2 release-readiness and tag-publication gates" in readme
    assert "Prompt text is omitted by default" in readme
    assert "does not perform unrestricted semantic extraction" in readme
    assert "No cloud-provider compatibility claim is implied" in readme
    assert "An ABOM is a build inventory" in readme
    assert "not yet an evidence-backed release claim" in readme
    assert "## Current version status" in readme
    assert "Package version | `0.1.1`" in readme
    assert "Roadmap increments through `v0.1.7` implemented" in readme
    assert "Version and release status" in readme
    assert "Issue #36" in readme


def test_version_status_is_explicit_and_consistent() -> None:
    status = read("docs/version-status.md")
    changelog = read("CHANGELOG.md")
    contributing = read("CONTRIBUTING.md")

    assert "Current package version | `0.1.1`" in status
    assert "Current development state | `main`" in status
    assert "Next evidence-backed release | `v0.2.0`" in status
    assert "implemented machinery is not the same as reviewed provider compatibility evidence" in status
    assert "Issue #36" in status
    assert "Do not change `pyproject.toml` from `0.1.1`" in status

    assert "`0.1.1` remains the current package version" in changelog
    assert "not separate published `0.1.2`–`0.1.7` package releases" in changelog
    assert "next planned evidence-backed package release is `v0.2.0`" in changelog

    assert "## Current version boundary" in contributing
    assert "package version remains `0.1.1`" in contributing
    assert "Do not:" in contributing
    assert "synthetic CI evidence as provider compatibility evidence" in contributing


def test_core_vocabulary_is_documented_without_overclaiming() -> None:
    concepts = read("docs/concepts.md")
    invariants = read("docs/invariants.md")
    source_comparison = read("docs/source-output-comparison-design.md")
    provider_runtime = read("docs/provider-runtime.md")
    builds = read("docs/reproducible-builds.md")
    evidence = read("docs/run-evidence.md")
    comparison = read("docs/evidence-comparison.md")
    release = read("docs/release-pipeline.md")
    reproduction = read("docs/reproduce-v020.md")

    assert "## Invariant" in concepts
    assert "## Reproducible build" in concepts
    assert "## Recipe lock" in concepts
    assert "## Evidence bundle" in concepts
    assert "## Agent Behaviour Bill of Materials" in concepts
    assert "The ABOM is available in machine-readable JSON" in concepts
    assert "An ABOM is a build inventory, not proof" in concepts
    assert "Prompt text is omitted by default" in concepts
    assert "Raw responses remain authoritative" in concepts
    assert "Unknown terms fail schema validation" in invariants
    assert "## Assurance guardians" in invariants
    assert "produce structured severity-aware failures" in invariants
    assert "does not yet perform general semantic extraction" in invariants
    assert "23 typed source facts" in source_comparison
    assert "cannot prove that every source fact was captured" in source_comparison
    assert "ProviderRequest" in provider_runtime
    assert "ProviderResponse" in provider_runtime
    assert "Ollama, Anthropic and OpenAI are built-in providers" in provider_runtime
    assert "ANTHROPIC_API_KEY" in provider_runtime
    assert "OPENAI_API_KEY" in provider_runtime
    assert "OpenAI adapter uses the Responses API contract" in provider_runtime
    assert "rejects `seed` and `stop`" in provider_runtime
    assert "Provider-aware evaluation and benchmark reports use schema `0.4`" in provider_runtime
    assert "Each stock and modded case result contains its own `execution` object" in provider_runtime
    assert "Normal CI never calls cloud providers" in provider_runtime
    assert "## Canonical source hashing" in builds
    assert "independently recomputed" in builds
    assert "No timestamps, absolute checkout paths" in builds
    assert "without a provider call" in builds
    assert "does not prove model compliance" in builds
    assert "responses.jsonl" in evidence
    assert "Prompt text is omitted by default" in evidence
    assert "Raw responses and interpreted evaluation are separate artifacts" in evidence
    assert "modding verify-evidence" in evidence
    assert "does not prove semantic correctness" in evidence
    assert "## Strict comparability contract" in comparison
    assert "new failures" in comparison
    assert "severity escalations" in comparison
    assert "modding compare-evidence" in comparison
    assert "modding matrix-evidence" in comparison
    assert "not a universal model or provider compatibility claim" in comparison
    assert "## Repeated-run aggregation" in release
    assert "## Scoped reviewed baselines" in release
    assert "## Pull-request evidence summaries" in release
    assert "## Protected cloud provider runs" in release
    assert "## Protected Ollama runs" in release
    assert "## v0.2 readiness gate" in release
    assert "Synthetic CI fixtures prove that the machinery works" in release
    assert "Automation cannot truthfully replace" in release
    assert "Independently reproduce the v0.2 flagship evidence" in reproduction
    assert "Do not edit raw responses" in reproduction


def test_build_evidence_comparison_and_release_schemas_are_versioned() -> None:
    expected = {
        "schemas/recipe-lock.schema.json": "Model Modding Recipe Lock",
        "schemas/abom.schema.json": "Agent Behaviour Bill of Materials",
        "schemas/build-manifest.schema.json": "Model Modding Build Manifest",
        "schemas/evidence-bundle.schema.json": "Model Modding Run Evidence Bundle",
        "schemas/evidence-comparison.schema.json": "Model Modding Evidence Comparison",
        "schemas/compatibility-matrix.schema.json": "Model Modding Compatibility Matrix",
        "schemas/repeated-evidence.schema.json": "Model Modding Repeated Evidence Aggregate",
        "schemas/reviewed-baseline.schema.json": "Model Modding Reviewed Baseline",
        "schemas/release-readiness.schema.json": "Model Modding v0.2 Release Readiness",
    }
    for path, title in expected.items():
        schema = json.loads(read(path))
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["title"] == title


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
    assert "## Evidence comparison contract" in contract
    assert "A mismatch must produce `not_comparable`" in contract
    assert "## Compatibility matrix contract" in contract
    assert "## Repeated evidence contract" in contract
    assert "## Reviewed baseline contract" in contract
    assert "## Protected execution contract" in contract
    assert "## Release readiness contract" in contract
    assert "The engineering pipeline enforces these conditions" in contract


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
    assert "## Release state at a glance" in roadmap
    assert "Current package version | `0.1.1`" in roadmap
    assert "Current development state | `main`" in roadmap
    assert "Next evidence-backed release | `v0.2.0`" in roadmap
    assert "Current package release. Delivered" in roadmap
    assert "Implemented on `main` after the `0.1.1` package release" in roadmap
    assert "Status: evidence-gated and not yet released" in roadmap
    assert "provider-neutral request, response, usage and generation-option contracts" in roadmap
    assert "explicit provider selection on `run`, `evaluate` and `benchmark`" in roadmap
    assert "provider-aware report schema `0.4`" in roadmap
    assert "per-response execution metadata including usage and finish reason" in roadmap
    assert "instruction and user-input mapping to the Responses API" in roadmap
    assert "`modding build` for deterministic behavioural bundles" in roadmap
    assert "independently recomputable digest inputs including schema versions" in roadmap
    assert "generated-artifact tamper detection" in roadmap
    assert "The ABOM identifies packaged behavioural inputs" in roadmap
    assert "versioned durable run-evidence bundle schema" in roadmap
    assert "`modding verify-evidence` for offline schema, hash and consistency checks" in roadmap
    assert "`modding compare-evidence` for strict baseline-versus-candidate comparison" in roadmap
    assert "`modding matrix-evidence` for provider/model-by-invariant summaries" in roadmap
    assert "concise automatic pull-request evidence summaries" in roadmap
    assert "protected and cost-limited Anthropic and OpenAI workflows" in roadmap
    assert "v0.2 tag publication blocked unless reviewed evidence passes the gate" in roadmap
    assert "Engineering complete; evidence operations remaining for a v0.2 release" in roadmap
    assert "Reviewed three-provider portability evidence remains a separate" in roadmap
    assert "Issue #36" in roadmap


def test_package_metadata_matches_v011_positioning() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)["project"]

    assert project["version"] == "0.1.1"
    assert project["description"] == "Package, test and deploy portable AI-agent behaviour with inspectable evidence."
    assert "assurance" in project["keywords"]
    assert "reproducibility" in project["keywords"]
    assert "anthropic" in project["optional-dependencies"]
    assert "openai" in project["optional-dependencies"]
