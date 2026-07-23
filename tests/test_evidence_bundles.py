from __future__ import annotations

import json
from pathlib import Path

from model_modding.entry import main
from model_modding.evidence import (
    response_record,
    verify_evidence_bundle,
    write_evidence_bundle,
)
from model_modding.provider import (
    ProviderRequest,
    ProviderResponse,
    ProviderUsage,
    register_provider,
)

ROOT = Path(__file__).resolve().parents[1]
RECIPE = "trusted-document-explainer"


class FakeEvidenceProvider:
    name = "evidence-test"

    def describe(self):
        return {
            "provider": self.name,
            "endpoint": "https://provider.invalid",
            "api_key_configured": True,
        }

    def list_models(self, timeout: float = 3.0):
        return ["evidence-model"]

    def generate(self, request: ProviderRequest, on_chunk=None):
        text = "A durable model response."
        if on_chunk is not None:
            on_chunk(text)
        return ProviderResponse(
            provider=self.name,
            model=request.model,
            text=text,
            latency_seconds=0.25,
            requested_options=request.options.supplied(),
            effective_options=request.options.supplied(),
            finish_reason="completed",
            usage=ProviderUsage(input_tokens=8, output_tokens=5, total_tokens=13),
            metadata={"endpoint": "https://provider.invalid", "request_id": "req_test"},
        )


def fake_response(text: str = "Raw response retained exactly.") -> ProviderResponse:
    return ProviderResponse(
        provider="evidence-test",
        model="evidence-model",
        text=text,
        latency_seconds=0.5,
        requested_options={"temperature": 0},
        effective_options={"temperature": 0},
        finish_reason="completed",
        usage=ProviderUsage(input_tokens=10, output_tokens=6, total_tokens=16),
        metadata={"endpoint": "https://provider.invalid", "request_id": "req_123"},
    )


def runtime() -> dict:
    return {
        "provider": "evidence-test",
        "endpoint": "https://provider.invalid",
        "requested_options": {"temperature": 0},
    }


def test_bundle_preserves_raw_response_but_omits_prompt_text(tmp_path: Path) -> None:
    prompt = "PRIVATE-SOURCE-TEXT-DO-NOT-COPY"
    record = response_record(
        identifier="evaluation:1:modded",
        role="modded",
        prompt=prompt,
        system_prompt="Behavioural instructions",
        response=fake_response(),
        case="deadline-case",
        mod="safety/deadline-guardian",
    )
    report = {
        "schema_version": "0.4",
        "evaluator": {"name": "deterministic-source-invariant-evaluator", "version": "0.3.0"},
        "cases": [
            {
                "case": "deadline-case",
                "prompt": prompt,
                "stock": {"response": "stock raw", "passed": False},
                "modded": {"response": "modded raw", "passed": True},
            }
        ],
    }

    destination = write_evidence_bundle(
        ROOT,
        RECIPE,
        tmp_path / "evidence",
        bundle_type="evaluation",
        runtime=runtime(),
        requested_models=["evidence-model"],
        records=[record],
        evaluation=report,
        created_at="2026-07-23T10:00:00Z",
    )

    manifest = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))
    raw = (destination / "responses.jsonl").read_text(encoding="utf-8")
    interpreted = json.loads((destination / "evaluation.json").read_text(encoding="utf-8"))
    all_text = "\n".join(path.read_text(encoding="utf-8") for path in destination.iterdir())

    assert manifest["privacy"] == {"prompt_text_included": False, "response_text_included": True}
    assert manifest["recipe"]["build_digest"] == json.loads(
        (destination / "recipe.lock.json").read_text(encoding="utf-8")
    )["build_digest"]
    assert "Raw response retained exactly." in raw
    assert prompt not in all_text
    assert "prompt" not in interpreted["cases"][0]
    assert "response" not in interpreted["cases"][0]["stock"]
    assert "response" not in interpreted["cases"][0]["modded"]
    assert verify_evidence_bundle(ROOT, destination) == []


def test_fixed_context_bundles_are_byte_identical(tmp_path: Path) -> None:
    record = response_record(
        identifier="run:modded:1",
        role="modded",
        prompt="private input",
        system_prompt="instructions",
        response=fake_response(),
    )
    first = write_evidence_bundle(
        ROOT,
        RECIPE,
        tmp_path / "first",
        bundle_type="run",
        runtime=runtime(),
        requested_models=["evidence-model"],
        records=[record],
        created_at="2026-07-23T10:00:00Z",
    )
    second = write_evidence_bundle(
        ROOT,
        RECIPE,
        tmp_path / "second",
        bundle_type="run",
        runtime=runtime(),
        requested_models=["evidence-model"],
        records=[record],
        created_at="2026-07-23T10:00:00Z",
    )

    assert {path.name for path in first.iterdir()} == {path.name for path in second.iterdir()}
    for path in first.iterdir():
        assert path.read_bytes() == (second / path.name).read_bytes()


def test_tampered_raw_response_fails_verification(tmp_path: Path) -> None:
    destination = write_evidence_bundle(
        ROOT,
        RECIPE,
        tmp_path / "evidence",
        bundle_type="run",
        runtime=runtime(),
        requested_models=["evidence-model"],
        records=[
            response_record(
                identifier="run:modded:1",
                role="modded",
                prompt="private input",
                system_prompt="instructions",
                response=fake_response(),
            )
        ],
        created_at="2026-07-23T10:00:00Z",
    )
    (destination / "responses.jsonl").write_text("{}\n", encoding="utf-8")

    failures = verify_evidence_bundle(ROOT, destination)

    assert any("responses.jsonl" in failure for failure in failures)
    assert any("response count mismatch" in failure for failure in failures)


def test_provider_run_can_emit_and_verify_evidence(tmp_path: Path, capsys) -> None:
    register_provider("evidence-test", FakeEvidenceProvider, replace=True)
    destination = tmp_path / "run-evidence"

    result = main([
        "run",
        RECIPE,
        "--provider",
        "evidence-test",
        "--model",
        "evidence-model",
        "--prompt",
        "private input",
        "--temperature",
        "0",
        "--evidence",
        str(destination),
        "--root",
        str(ROOT),
    ])

    assert result == 0
    assert (destination / "manifest.json").exists()
    assert "Evidence bundle:" in capsys.readouterr().out
    assert main(["verify-evidence", str(destination), "--root", str(ROOT)]) == 0
