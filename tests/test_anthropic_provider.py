from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from model_modding.anthropic_provider import (
    DEFAULT_ANTHROPIC_MAX_TOKENS,
    AnthropicProvider,
)
from model_modding.provider import (
    GenerationOptions,
    ProviderConfigurationError,
    ProviderConnectionError,
    ProviderHTTPError,
    ProviderRequest,
    create_provider,
    provider_names,
)


@dataclass
class TextBlock:
    type: str
    text: str


class FakeMessages:
    def __init__(self, response=None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response


class FakeModels:
    def list(self, **kwargs):
        assert kwargs == {"limit": 100}
        return SimpleNamespace(data=[SimpleNamespace(id="claude-sonnet-4-6"), SimpleNamespace(id="claude-haiku-4-5")])


class FakeClient:
    def __init__(self, response=None, error: Exception | None = None) -> None:
        self.messages = FakeMessages(response, error)
        self.models = FakeModels()


def response():
    return SimpleNamespace(
        id="msg_123",
        type="message",
        model="claude-sonnet-4-6",
        content=[TextBlock("text", "A clear answer.")],
        stop_reason="end_turn",
        stop_sequence=None,
        usage=SimpleNamespace(input_tokens=12, output_tokens=4),
    )


def test_anthropic_is_registered_as_builtin() -> None:
    assert "anthropic" in provider_names()


def test_missing_api_key_fails_before_sdk_import() -> None:
    with pytest.raises(ProviderConfigurationError, match="ANTHROPIC_API_KEY"):
        AnthropicProvider(environ={})


def test_factory_receives_key_endpoint_and_timeout() -> None:
    captured = {}
    client = FakeClient(response())

    def factory(**kwargs):
        captured.update(kwargs)
        return client

    provider = AnthropicProvider(
        api_key="secret",
        endpoint="https://example.anthropic.test/",
        client_factory=factory,
    )
    result = provider.generate(ProviderRequest(model="claude-sonnet-4-6", prompt="Hello", timeout=9))

    assert captured == {
        "api_key": "secret",
        "base_url": "https://example.anthropic.test",
        "timeout": 9,
    }
    assert result.text == "A clear answer."


def test_message_payload_maps_system_and_portable_options() -> None:
    client = FakeClient(response())
    provider = AnthropicProvider(api_key="secret", client_factory=lambda **kwargs: client)
    request = ProviderRequest(
        model="claude-sonnet-4-6",
        prompt="Explain this",
        system_prompt="Preserve material meaning",
        options=GenerationOptions(
            temperature=0.2,
            top_p=0.9,
            max_tokens=512,
            stop=("END",),
        ),
    )

    result = provider.generate(request)
    payload = client.messages.calls[0]

    assert payload == {
        "model": "claude-sonnet-4-6",
        "max_tokens": 512,
        "messages": [{"role": "user", "content": "Explain this"}],
        "system": "Preserve material meaning",
        "temperature": 0.2,
        "top_p": 0.9,
        "stop_sequences": ["END"],
    }
    assert result.requested_options["max_tokens"] == 512
    assert result.effective_options["max_tokens"] == 512
    assert result.metadata["max_tokens_defaulted"] is False


def test_required_max_tokens_is_defaulted_and_recorded() -> None:
    client = FakeClient(response())
    provider = AnthropicProvider(api_key="secret", client_factory=lambda **kwargs: client)

    result = provider.generate(ProviderRequest(model="claude-sonnet-4-6", prompt="Hello"))

    assert client.messages.calls[0]["max_tokens"] == DEFAULT_ANTHROPIC_MAX_TOKENS
    assert result.requested_options == {}
    assert result.effective_options == {"max_tokens": DEFAULT_ANTHROPIC_MAX_TOKENS}
    assert result.metadata["max_tokens_defaulted"] is True


def test_usage_finish_reason_and_response_metadata_are_normalised() -> None:
    provider = AnthropicProvider(api_key="secret", client_factory=lambda **kwargs: FakeClient(response()))

    result = provider.generate(ProviderRequest(model="requested-alias", prompt="Hello"))

    assert result.provider == "anthropic"
    assert result.model == "claude-sonnet-4-6"
    assert result.finish_reason == "end_turn"
    assert result.usage.input_tokens == 12
    assert result.usage.output_tokens == 4
    assert result.usage.total_tokens == 16
    assert result.metadata["message_id"] == "msg_123"


def test_seed_is_rejected_before_api_call() -> None:
    client = FakeClient(response())
    provider = AnthropicProvider(api_key="secret", client_factory=lambda **kwargs: client)

    with pytest.raises(ProviderConfigurationError, match="does not support.*seed"):
        provider.generate(
            ProviderRequest(
                model="claude-sonnet-4-6",
                prompt="Hello",
                options=GenerationOptions(seed=7),
            )
        )
    assert client.messages.calls == []


def test_model_discovery_is_normalised() -> None:
    provider = AnthropicProvider(api_key="secret", client_factory=lambda **kwargs: FakeClient(response()))
    assert provider.list_models() == ["claude-sonnet-4-6", "claude-haiku-4-5"]


def test_connection_and_http_errors_are_normalised() -> None:
    APIConnectionError = type("APIConnectionError", (Exception,), {})
    RateLimitError = type("RateLimitError", (Exception,), {"status_code": 429})

    connection = AnthropicProvider(
        api_key="secret",
        client_factory=lambda **kwargs: FakeClient(error=APIConnectionError("offline")),
    )
    with pytest.raises(ProviderConnectionError, match="offline"):
        connection.generate(ProviderRequest(model="claude-sonnet-4-6", prompt="Hello"))

    limited = AnthropicProvider(
        api_key="secret",
        client_factory=lambda **kwargs: FakeClient(error=RateLimitError("slow down")),
    )
    with pytest.raises(ProviderHTTPError, match="429"):
        limited.generate(ProviderRequest(model="claude-sonnet-4-6", prompt="Hello"))


def test_create_provider_uses_environment_authentication() -> None:
    provider = create_provider(
        "anthropic",
        client_factory=lambda **kwargs: FakeClient(response()),
        environ={"ANTHROPIC_API_KEY": "from-env"},
    )
    assert provider.describe()["api_key_configured"] is True
