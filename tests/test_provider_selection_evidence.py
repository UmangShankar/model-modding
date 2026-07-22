from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from model_modding.entry import main
from model_modding.evaluation import EvaluationCase
from model_modding.provider import ProviderRequest, ProviderResponse, ProviderUsage, register_provider

ROOT = Path(__file__).resolve().parents[1]


class FakeProvider:
    name = "fake"

    def __init__(self, endpoint: str | None = None) -> None:
        self.endpoint = endpoint or "memory://fake"

    def describe(self):
        return {"provider": self.name, "endpoint": self.endpoint}

    def list_models(self, timeout: float = 3.0):
        return ["fake-model"]

    def generate(self, request: ProviderRequest, on_chunk=None):
        text = f"fake response for {request.prompt}"
        if on_chunk is not None:
            on_chunk(text)
        return ProviderResponse(
            provider=self.name,
            model=request.model,
            text=text,
            latency_seconds=0.01,
            requested_options=request.options.supplied(),
            effective_options=request.options.supplied(),
            finish_reason="stop",
            usage=ProviderUsage(input_tokens=3, output_tokens=4, total_tokens=7),
            metadata={"endpoint": self.endpoint},
        )


def register_fake() -> None:
    register_provider("fake", FakeProvider, replace=True)


def test_run_accepts_provider_and_generation_options(capsys) -> None:
    register_fake()
    result = main([
        "--root", str(ROOT), "run", "research-learning-companion",
        "--provider", "fake", "--model", "fake-model", "--prompt", "Explain gravity",
        "--temperature", "0.2", "--top-p", "0.9", "--max-tokens", "120", "--seed", "7",
        "--stop", "END",
    ])
    output = capsys.readouterr().out
    assert result == 0
    assert "Provider: fake" in output
    assert '"max_tokens": 120' in output
    assert "Finish reason: stop" in output


def test_unknown_provider_fails_before_model_call(capsys) -> None:
    result = main([
        "--root", str(ROOT), "run", "research-learning-companion",
        "--provider", "missing", "--model", "x", "--prompt", "Hello",
    ])
    assert result == 1
    assert "Unknown provider" in capsys.readouterr().err


def test_evaluation_report_records_provider_execution(monkeypatch, tmp_path: Path) -> None:
    register_fake()
    case = EvaluationCase(
        mod="domain/example",
        name="provider-evidence",
        prompt="Source text",
        expected_behaviours=(),
        failure_indicators=(),
        checks={"contains_any": [["fake response"]]},
    )
    monkeypatch.setattr(
        "model_modding.provider_commands.load_evaluation_cases",
        lambda root, name: (SimpleNamespace(system_prompt="instructions"), [case]),
    )

    result = main([
        "evaluate", "trusted-document-explainer", "--root", str(ROOT),
        "--provider", "fake", "--host", "memory://evaluator", "--model", "fake-model",
        "--temperature", "0.1", "--output", str(tmp_path), "--fail-on", "none",
    ])
    assert result == 0
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert report["schema_version"] == "0.4"
    assert report["runtime"]["provider"] == "fake"
    assert report["runtime"]["endpoint"] == "memory://evaluator"
    assert report["runtime"]["requested_options"] == {"temperature": 0.1}
    execution = report["cases"][0]["modded"]["execution"]
    assert execution["provider"] == "fake"
    assert execution["model"] == "fake-model"
    assert execution["usage"]["total_tokens"] == 7


def test_benchmark_report_records_provider_and_resolved_model(monkeypatch, tmp_path: Path) -> None:
    register_fake()
    case = EvaluationCase(
        mod="domain/example",
        name="benchmark-provider-evidence",
        prompt="Source text",
        expected_behaviours=(),
        failure_indicators=(),
        checks={"contains_any": [["fake response"]]},
    )
    monkeypatch.setattr(
        "model_modding.provider_commands.load_evaluation_cases",
        lambda root, name: (SimpleNamespace(system_prompt="instructions"), [case]),
    )

    result = main([
        "benchmark", "trusted-document-explainer", "--root", str(ROOT),
        "--provider", "fake", "--models", "fake-model", "--output", str(tmp_path),
    ])
    assert result == 0
    report = json.loads((tmp_path / "benchmark.json").read_text(encoding="utf-8"))
    assert report["schema_version"] == "0.4"
    assert report["runtime"]["provider"] == "fake"
    assert report["models"][0]["resolved_model"] == "fake-model"
    assert report["models"][0]["execution"]["provider"] == "fake"
