from __future__ import annotations

import json
from pathlib import Path

from model_modding.entry import main
from model_modding.evidence import response_record, write_evidence_bundle
from model_modding.evidence_comparison import (
    build_compatibility_matrix,
    compare_evidence,
)
from model_modding.provider import ProviderResponse, ProviderUsage

ROOT = Path(__file__).resolve().parents[1]
RECIPE = "trusted-document-explainer"
MOD = "safety/deadline-guardian"
CASE = "deadline-case"
FAILURE_ID = f"{MOD}:{CASE}:invariant:preserve:deadline:1"


def fake_response(provider: str, model: str, text: str) -> ProviderResponse:
    return ProviderResponse(
        provider=provider,
        model=model,
        text=text,
        latency_seconds=0.25,
        requested_options={"temperature": 0},
        effective_options={"temperature": 0},
        finish_reason="completed",
        usage=ProviderUsage(input_tokens=10, output_tokens=6, total_tokens=16),
        metadata={"endpoint": f"https://{provider}.invalid", "request_id": "req_test"},
    )


def invariant_result(*, passed: bool, severity: str = "critical") -> dict:
    return {
        "kind": "preserve",
        "invariant": "deadline",
        "severity": severity,
        "description": "Preserve the exact deadline.",
        "passed": passed,
        "checks": [],
    }


def failure(*, severity: str = "critical") -> dict:
    return {
        "id": FAILURE_ID,
        "layer": "invariant_check",
        "mod": MOD,
        "case": CASE,
        "kind": "preserve",
        "invariant": "deadline",
        "severity": severity,
        "description": "Preserve the exact deadline.",
        "failed_checks": [],
    }


def evaluation_report(
    *,
    model: str,
    passed: bool,
    severity: str = "critical",
    evaluator_version: str = "0.3.0",
) -> dict:
    failures = [] if passed else [failure(severity=severity)]
    modded = {
        "passed": passed,
        "checks": [],
        "invariant_checks": [invariant_result(passed=passed, severity=severity)],
        "invariant_failures": failures,
        "source_comparisons": [],
        "source_comparison_failures": [],
        "failures": failures,
    }
    stock = {
        "passed": True,
        "checks": [],
        "invariant_checks": [invariant_result(passed=True, severity=severity)],
        "invariant_failures": [],
        "source_comparisons": [],
        "source_comparison_failures": [],
        "failures": [],
    }
    return {
        "schema_version": "0.4",
        "evaluator": {
            "name": "deterministic-source-invariant-evaluator",
            "version": evaluator_version,
            "layers": ["legacy_checks", "invariant_checks", "source_comparison"],
        },
        "recipe": RECIPE,
        "model": model,
        "summary": {
            "cases": 1,
            "stock_passed": 1,
            "modded_passed": int(passed),
            "stock_failures": {"critical": 0, "major": 0, "minor": 0},
            "modded_failures": {
                "critical": int(not passed and severity == "critical"),
                "major": int(not passed and severity == "major"),
                "minor": int(not passed and severity == "minor"),
            },
        },
        "pipeline": {
            "status": "passed" if passed else "failed",
            "fail_on": "critical",
            "blocking_failure_count": len(failures),
            "blocking_failures": failures,
        },
        "failures": {"stock": [], "modded": failures},
        "cases": [
            {
                "mod": MOD,
                "case": CASE,
                "prompt": "The response is due within 14 calendar days.",
                "stock": stock,
                "modded": modded,
            }
        ],
    }


def write_evaluation(
    tmp_path: Path,
    name: str,
    *,
    provider: str = "provider-a",
    model: str = "model-a",
    passed: bool = True,
    severity: str = "critical",
    prompt: str = "The response is due within 14 calendar days.",
    evaluator_version: str = "0.3.0",
) -> Path:
    stock = fake_response(provider, model, "Stock response")
    modded = fake_response(provider, model, "Modded response")
    records = [
        response_record(
            identifier=f"evaluation:1:stock",
            role="stock",
            prompt=prompt,
            system_prompt="",
            response=stock,
            case=CASE,
            mod=MOD,
        ),
        response_record(
            identifier=f"evaluation:1:modded",
            role="modded",
            prompt=prompt,
            system_prompt="Behavioural instructions",
            response=modded,
            case=CASE,
            mod=MOD,
        ),
    ]
    return write_evidence_bundle(
        ROOT,
        RECIPE,
        tmp_path / name,
        bundle_type="evaluation",
        runtime={
            "provider": provider,
            "endpoint": f"https://{provider}.invalid",
            "requested_options": {"temperature": 0},
        },
        requested_models=[model],
        records=records,
        evaluation=evaluation_report(
            model=model,
            passed=passed,
            severity=severity,
            evaluator_version=evaluator_version,
        ),
        created_at="2026-07-23T12:00:00Z",
    )


def test_equal_verified_evidence_passes_comparison(tmp_path: Path) -> None:
    baseline = write_evaluation(tmp_path, "baseline")
    candidate = write_evaluation(tmp_path, "candidate")

    report = compare_evidence(ROOT, baseline, candidate)

    assert report["comparability"]["status"] == "comparable"
    assert report["pipeline"]["status"] == "passed"
    assert report["summary"]["new_failures"] == {
        "critical": 0,
        "major": 0,
        "minor": 0,
    }
    assert len(report["comparison_digest"]) == 64


def test_new_critical_failure_blocks_comparison_command(tmp_path: Path) -> None:
    baseline = write_evaluation(tmp_path, "baseline")
    candidate = write_evaluation(tmp_path, "candidate", passed=False)
    output = tmp_path / "comparison"

    result = main(
        [
            "compare-evidence",
            str(baseline),
            str(candidate),
            "--output",
            str(output),
            "--root",
            str(ROOT),
        ]
    )
    report = json.loads((output / "comparison.json").read_text(encoding="utf-8"))

    assert result == 1
    assert report["pipeline"]["status"] == "failed"
    assert report["summary"]["new_failures"]["critical"] == 1
    assert report["pipeline"]["blocking_failure_count"] == 1
    assert "NEW CRITICAL" in (output / "comparison.md").read_text(encoding="utf-8")


def test_severity_escalation_blocks_at_candidate_severity(tmp_path: Path) -> None:
    baseline = write_evaluation(tmp_path, "baseline", passed=False, severity="major")
    candidate = write_evaluation(tmp_path, "candidate", passed=False, severity="critical")

    report = compare_evidence(ROOT, baseline, candidate, fail_on="critical")

    assert report["pipeline"]["status"] == "failed"
    assert report["summary"]["new_failures"]["critical"] == 0
    assert report["summary"]["severity_escalations"] == 1
    assert report["pipeline"]["blocking_failure_count"] == 1


def test_fixture_or_evaluator_mismatch_is_not_comparable(tmp_path: Path) -> None:
    baseline = write_evaluation(tmp_path, "baseline")
    candidate = write_evaluation(
        tmp_path,
        "candidate",
        prompt="A different fixture input.",
        evaluator_version="0.4.0",
    )
    output = tmp_path / "comparison"

    result = main(
        [
            "compare-evidence",
            str(baseline),
            str(candidate),
            "--output",
            str(output),
            "--root",
            str(ROOT),
        ]
    )
    report = json.loads((output / "comparison.json").read_text(encoding="utf-8"))
    mismatches = {
        check["field"]
        for check in report["comparability"]["checks"]
        if not check["matched"]
    }

    assert result == 2
    assert report["pipeline"]["status"] == "not_comparable"
    assert {"fixture_set_digest", "evaluator"}.issubset(mismatches)


def test_matrix_reports_each_provider_model_by_invariant(tmp_path: Path) -> None:
    first = write_evaluation(
        tmp_path,
        "first",
        provider="provider-a",
        model="model-a",
        passed=True,
    )
    second = write_evaluation(
        tmp_path,
        "second",
        provider="provider-b",
        model="model-b",
        passed=False,
    )

    report = build_compatibility_matrix(ROOT, [first, second])
    deadline = next(row for row in report["invariants"] if row["invariant"] == "deadline")

    assert report["target_count"] == 2
    assert {target["key"] for target in report["targets"]} == {
        "provider-a/model-a",
        "provider-b/model-b",
    }
    assert deadline["targets"]["provider-a/model-a"]["status"] == "passed"
    assert deadline["targets"]["provider-b/model-b"]["status"] == "failed"
    assert len(report["matrix_digest"]) == 64


def test_matrix_command_writes_json_and_markdown(tmp_path: Path) -> None:
    first = write_evaluation(tmp_path, "first", provider="provider-a", model="model-a")
    second = write_evaluation(tmp_path, "second", provider="provider-b", model="model-b")
    output = tmp_path / "matrix"

    result = main(
        [
            "matrix-evidence",
            str(first),
            str(second),
            "--output",
            str(output),
            "--root",
            str(ROOT),
        ]
    )

    assert result == 0
    assert (output / "matrix.json").exists()
    assert "provider-a/model-a" in (output / "matrix.md").read_text(encoding="utf-8")


def test_top_level_help_mentions_comparison_commands(capsys) -> None:
    try:
        main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0
    output = capsys.readouterr().out
    assert "compare-evidence" in output
    assert "matrix-evidence" in output
