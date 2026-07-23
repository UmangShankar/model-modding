from __future__ import annotations

import json
from pathlib import Path

import pytest

from model_modding.evidence import response_record, verify_evidence_bundle, write_evidence_bundle
from model_modding.evidence_comparison import build_compatibility_matrix
from model_modding.provider import ProviderResponse, ProviderUsage
from model_modding.release_pipeline import (
    activate_baseline,
    aggregate_evidence,
    build_pr_summary,
    check_release_readiness,
    validate_provider_run_plan,
)
from scripts.assemble_release_evidence import validate_release_bundle

ROOT = Path(__file__).resolve().parents[1]
RECIPE = "trusted-document-explainer"
MOD = "safety/deadline-guardian"
CASE_PREFIX = "deadline-case"


def _response(provider: str, model: str) -> ProviderResponse:
    return ProviderResponse(
        provider=provider,
        model=model,
        text="The response is due within 14 calendar days.",
        latency_seconds=0.1,
        requested_options={"temperature": 0},
        effective_options={"temperature": 0},
        finish_reason="completed",
        usage=ProviderUsage(input_tokens=8, output_tokens=8, total_tokens=16),
        metadata={"endpoint": f"https://{provider}.invalid"},
    )


def _failure(case: str) -> dict:
    return {
        "id": f"{MOD}:{case}:invariant:preserve:deadline:1",
        "layer": "invariant_check",
        "mod": MOD,
        "case": case,
        "kind": "preserve",
        "invariant": "deadline",
        "severity": "critical",
        "description": "Preserve the exact deadline.",
        "failed_checks": [],
    }


def _result(*, passed: bool, case: str) -> dict:
    failures = [] if passed else [_failure(case)]
    return {
        "passed": passed,
        "checks": [],
        "invariant_checks": [
            {
                "kind": "preserve",
                "invariant": "deadline",
                "severity": "critical",
                "description": "Preserve the exact deadline.",
                "passed": passed,
                "checks": [],
            }
        ],
        "invariant_failures": failures,
        "source_comparisons": [],
        "source_comparison_failures": [],
        "failures": failures,
    }


def _report(model: str, *, passed: bool, cases: int = 40, reported_cases: int | None = None) -> dict:
    rows = []
    failures = []
    for index in range(1, cases + 1):
        case = f"{CASE_PREFIX}-{index:02d}"
        case_passed = passed or index != 1
        modded = _result(passed=case_passed, case=case)
        stock = _result(passed=True, case=case)
        rows.append(
            {
                "mod": MOD,
                "case": case,
                "prompt": "The response is due within 14 calendar days.",
                "stock": stock,
                "modded": modded,
            }
        )
        failures.extend(modded["failures"])
    return {
        "schema_version": "0.4",
        "evaluator": {
            "name": "deterministic-source-invariant-evaluator",
            "version": "0.3.0",
            "layers": ["legacy_checks", "invariant_checks", "source_comparison"],
        },
        "recipe": RECIPE,
        "model": model,
        "summary": {
            "cases": cases if reported_cases is None else reported_cases,
            "stock_passed": cases,
            "modded_passed": cases if passed else cases - 1,
            "stock_failures": {"critical": 0, "major": 0, "minor": 0},
            "modded_failures": {"critical": int(not passed), "major": 0, "minor": 0},
        },
        "pipeline": {
            "status": "passed" if passed else "failed",
            "fail_on": "critical",
            "blocking_failure_count": len(failures),
            "blocking_failures": failures,
        },
        "failures": {"stock": [], "modded": failures},
        "cases": rows,
    }


def _write_bundle(
    tmp_path: Path,
    name: str,
    provider: str,
    model: str,
    repetition: int,
    *,
    passed: bool = True,
    requested_model: str | None = None,
    cases: int = 40,
    reported_cases: int | None = None,
) -> Path:
    response = _response(provider, model)
    prompt = "The response is due within 14 calendar days."
    records = []
    for index in range(1, cases + 1):
        case = f"{CASE_PREFIX}-{index:02d}"
        records.extend(
            [
                response_record(
                    identifier=f"evaluation:{index}:stock",
                    role="stock",
                    prompt=prompt,
                    system_prompt="",
                    response=response,
                    case=case,
                    mod=MOD,
                ),
                response_record(
                    identifier=f"evaluation:{index}:modded",
                    role="modded",
                    prompt=prompt,
                    system_prompt="instructions",
                    response=response,
                    case=case,
                    mod=MOD,
                ),
            ]
        )
    return write_evidence_bundle(
        ROOT,
        RECIPE,
        tmp_path / name,
        bundle_type="evaluation",
        runtime={"provider": provider, "endpoint": f"https://{provider}.invalid", "requested_options": {"temperature": 0}},
        requested_models=[requested_model or model],
        records=records,
        evaluation=_report(model, passed=passed, cases=cases, reported_cases=reported_cases),
        created_at=f"2026-07-23T12:00:0{repetition}Z",
    )


def test_repeated_evidence_aggregate_requires_repetitions_and_zero_critical(tmp_path: Path) -> None:
    bundles = [_write_bundle(tmp_path, f"run-{index}", "ollama", "model-a", index) for index in range(1, 4)]
    report = aggregate_evidence(ROOT, bundles, minimum_repetitions=3, require_zero_critical=True)
    assert report["pipeline"]["status"] == "passed"
    assert report["targets"][0]["repetitions"] == 3
    assert report["targets"][0]["minimum_cases"] == 40

    failed = _write_bundle(tmp_path, "failed", "ollama", "model-a", 4, passed=False)
    report = aggregate_evidence(ROOT, bundles + [failed], minimum_repetitions=3, require_zero_critical=True)
    assert report["pipeline"]["status"] == "failed"
    assert report["pipeline"]["critical_failure_targets"] == ["ollama/model-a"]


def test_baseline_activation_preserves_verified_bundle(tmp_path: Path) -> None:
    source = _write_bundle(tmp_path, "source", "ollama", "model-a", 1)
    destination = activate_baseline(ROOT, source, tmp_path / "baseline", reviewer="Maintainers", scope="CI regression", notes="Synthetic contract baseline")
    baseline = json.loads((destination / "baseline.json").read_text(encoding="utf-8"))
    assert baseline["scope"] == "CI regression"
    assert verify_evidence_bundle(ROOT, destination / "evidence") == []


def test_release_bundle_requires_actual_cases_and_exact_returned_model(tmp_path: Path) -> None:
    valid = _write_bundle(tmp_path, "valid", "openai", "exact-model", 1)
    descriptor = validate_release_bundle(ROOT, valid, minimum_cases=40)
    assert descriptor["cases"] == 40
    assert descriptor["target_key"] == "openai/exact-model"

    mismatched_count = _write_bundle(
        tmp_path,
        "mismatched-count",
        "openai",
        "exact-model",
        2,
        reported_cases=41,
    )
    with pytest.raises(ValueError, match="case count mismatch"):
        validate_release_bundle(ROOT, mismatched_count, minimum_cases=40)

    aliased = _write_bundle(
        tmp_path,
        "aliased",
        "openai",
        "returned-model",
        3,
        requested_model="model-alias",
    )
    with pytest.raises(ValueError, match="exact returned model ID"):
        validate_release_bundle(ROOT, aliased, minimum_cases=40)


def test_release_readiness_requires_three_providers_three_runs_and_full_cases(tmp_path: Path) -> None:
    bundles = []
    first_by_provider = []
    for provider in ("ollama", "anthropic", "openai"):
        for repetition in range(1, 4):
            bundle = _write_bundle(tmp_path, f"{provider}-{repetition}", provider, f"{provider}-model", repetition)
            bundles.append(bundle)
            if repetition == 1:
                first_by_provider.append(bundle)
    aggregate = aggregate_evidence(ROOT, bundles, minimum_repetitions=3, require_zero_critical=True)
    matrix = build_compatibility_matrix(ROOT, first_by_provider)
    aggregate_path = tmp_path / "aggregate.json"
    matrix_path = tmp_path / "matrix.json"
    aggregate_path.write_text(json.dumps(aggregate), encoding="utf-8")
    matrix_path.write_text(json.dumps(matrix), encoding="utf-8")
    readiness = check_release_readiness(ROOT, aggregate_path, matrix_path)
    assert readiness["status"] == "ready"
    assert all(check["passed"] for check in readiness["checks"])


def test_summary_and_protected_run_plan_are_explicit() -> None:
    summary = build_pr_summary()
    assert "model-modding-evidence-summary" in summary
    assert "No evidence report was supplied" in summary
    plan = validate_provider_run_plan(provider="openai", model="model-a", repetitions=3, max_tokens=1024, case_limit=40, allowlist="model-a,model-b")
    assert plan["case_limit"] == 40
    with pytest.raises(ValueError, match="not in"):
        validate_provider_run_plan(provider="openai", model="other", repetitions=3, max_tokens=1024, case_limit=40, allowlist="model-a")
