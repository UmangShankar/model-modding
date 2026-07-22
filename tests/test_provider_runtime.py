from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import pytest

from model_modding.ollama_provider import OllamaProvider
from model_modding.provider import (
    GenerationOptions,
    ProviderConfigurationError,
    ProviderRequest,
    ProviderResponse,
    ProviderUsage,
    create_provider,
    provider_names,
    register_provider,
)


class FakeResponse:
    def __init__(self, body: bytes = b"", lines: list[bytes] | None = None) -> None:
        self.body = body
        self.lines = lines or []

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body

    def __iter__(self):
        return iter(self.lines)


def test_generation_options_validate_and_emit_only_supplied_values() -> None:
    options = GenerationOptions(
        temperature=0.2,
        top_p=0.9,
        max_tokens=256,
        seed=7,
        stop=("END",),
    )

    assert options.supplied() == {
        "temperature": 0.2,
        "top_p": 0.9,
        "max_tokens": 256,
        "seed": 7,
        "stop": ["END"],
    }
    assert GenerationOptions.from_mapping(options.supplied()) == options

    with pytest.raises(ValueError, match="top_p"):
        GenerationOptions(top_p=0)
    with pytest.raises(ValueError, match="max_tokens"):
        GenerationOptions(max_tokens=0)
    with pytest.raises(ValueError, match="Unsupported generation options"):
        GenerationOptions.from_mapping({"frequency_penalty": 1})


def test_provider_registry_loads_ollama_and_rejects_unknown_provider() -> None:
    assert "ollama" in provider_names()
    provider = create_provider("OLLAMA", host="http://127.0.0.1:11434")
    assert provider.name == "ollama"

    with pytest.raises(ProviderConfigurationError, match="Unknown provider"):
        create_provider("missing-provider")


def test_provider_registry_accepts_extension_factories() -> None:
    @dataclass
    class ExampleProvider:
        name: str = "example-test-provider"

        def list_models(self, timeout: float = 3.0) -> list[str]:
            return ["example-model"]

        def generate(self, request: ProviderRequest, on_chunk=None) -> ProviderResponse:
            if on_chunk is not None:
                on_chunk("ok")
            return ProviderResponse(
                provider=self.name,
                model=request.model,
                text="ok",
                latency_seconds=0.0,
                requested_options=request.options.supplied(),
                effective_options=request.options.supplied(),
                usage=ProviderUsage(),
            )

        def describe(self) -> dict[str, Any]:
            return {"provider": self.name}

    register_provider("example-test-provider", ExampleProvider, replace=True)
    provider = create_provider("example-test-provider")
    assert provider.list_models() == ["example-model"]


def test_ollama_adapter_maps_neutral_options_and_normalises_metadata() -> None:
    events = [
        json.dumps({"message": {"content": "Hello"}, "done": False}).encode() + b"\n",
        json.dumps(
            {
                "message": {"content": " world"},
                "done": True,
                "done_reason": "stop",
                "prompt_eval_count": 11,
                "eval_count": 2,
                "load_duration": 10,
                "prompt_eval_duration": 20,
                "eval_duration": 30,
            }
        ).encode()
        + b"\n",
    ]
    captured_payload: dict[str, Any] = {}

    def opener(request, timeout):
        captured_payload.update(json.loads(request.data.decode("utf-8")))
        assert timeout == 9.0
        return FakeResponse(lines=events)

    provider = OllamaProvider(opener=opener)
    chunks: list[str] = []
    request = ProviderRequest(
        model="llama3.2",
        prompt="Explain this",
        system_prompt="Preserve meaning",
        options=GenerationOptions(
            temperature=0.1,
            top_p=0.8,
            max_tokens=128,
            seed=42,
            stop=("DONE",),
        ),
        timeout=9.0,
    )
    response = provider.generate(request, on_chunk=chunks.append)

    assert captured_payload["model"] == "llama3.2"
    assert captured_payload["messages"] == [
        {"role": "system", "content": "Preserve meaning"},
        {"role": "user", "content": "Explain this"},
    ]
    assert captured_payload["options"] == {
        "temperature": 0.1,
        "top_p": 0.8,
        "num_predict": 128,
        "seed": 42,
        "stop": ["DONE"],
    }
    assert chunks == ["Hello", " world"]
    assert response.text == "Hello world"
    assert response.provider == "ollama"
    assert response.finish_reason == "stop"
    assert response.usage.as_dict() == {
        "input_tokens": 11,
        "output_tokens": 2,
        "total_tokens": 13,
    }
    assert response.requested_options["max_tokens"] == 128
    assert response.effective_options == response.requested_options
    assert response.metadata["endpoint"] == "http://127.0.0.1:11434"
    assert response.metadata["provider_defaults_not_reported"] is True


def test_ollama_adapter_omits_unsupplied_options_and_empty_system_message() -> None:
    events = [json.dumps({"message": {"content": "ok"}, "done": True}).encode() + b"\n"]
    captured_payload: dict[str, Any] = {}

    def opener(request, timeout):
        captured_payload.update(json.loads(request.data.decode("utf-8")))
        return FakeResponse(lines=events)

    response = OllamaProvider(opener=opener).generate(
        ProviderRequest(model="llama3.2", prompt="Hi")
    )

    assert captured_payload["messages"] == [{"role": "user", "content": "Hi"}]
    assert "options" not in captured_payload
    assert response.requested_options == {}
    assert response.finish_reason is None
