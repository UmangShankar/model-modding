from __future__ import annotations

from types import SimpleNamespace

import pytest

from model_modding.openai_provider import OpenAIProvider
from model_modding.provider import (
    GenerationOptions,
    ProviderConfigurationError,
    ProviderConnectionError,
    ProviderHTTPError,
    ProviderRequest,
    ProviderResponseError,
    create_provider,
    provider_names,
)


class FakeResponses:
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
    def list(self):
        return SimpleNamespace(data=[SimpleNamespace(id="gpt-5.2"), SimpleNamespace(id="gpt-5-mini")])


class FakeClient:
    def __init__(self, response=None, error: Exception | None = None) -> None:
        self.responses = FakeResponses(response, error)
        self.models = FakeModels()


def response(output_text: str = "A clear answer."):
    return SimpleNamespace(
        id="resp_123",
        model="gpt-5.2",
        output_text=output_text,
        output=[],
        status="completed",
        incomplete_details=None,
        created_at=1784740000,
        service_tier="default",
        usage=SimpleNamespace(
            input_tokens=11,
            output_tokens=4,
            total_tokens=15,
            output_tokens_details=SimpleNamespace(reasoning_tokens=2),
        ),
    )


def test_openai_is_registered_as_builtin() -> None:
    assert "openai" in provider_names()


def test_missing_api_key_fails_before_sdk_import() -> None:
    with pytest.raises(ProviderConfigurationError, match="OPENAI_API_KEY"):
        OpenAIProvider(environ={})


def test_factory_receives_key_endpoint_and_timeout() -> None:
    captured = {}
    client = FakeClient(response())

    def factory(**kwargs):
        captured.update(kwargs)
        return client

    provider = OpenAIProvider(
        api_key="secret",
        endpoint="https://example.openai.test/v1/",
        client_factory=factory,
    )
    result = provider.generate(ProviderRequest(model="gpt-5.2", prompt="Hello", timeout=9))

    assert captured == {
        "api_key": "secret",
        "base_url": "https://example.openai.test/v1",
        "timeout": 9,
    }
    assert result.text == "A clear answer."


def test_responses_payload_maps_instructions_and_portable_options() -> None:
    client = FakeClient(response())
    provider = OpenAIProvider(api_key="secret", client_factory=lambda **kwargs: client)
    request = ProviderRequest(
        model="gpt-5.2",
        prompt="Explain this",
        system_prompt="Preserve material meaning",
        options=GenerationOptions(
            temperature=0.2,
            top_p=0.9,
            max_tokens=512,
        ),
    )

    result = provider.generate(request)
    payload = client.responses.calls[0]

    assert payload == {
        "model": "gpt-5.2",
        "input": "Explain this",
        "instructions": "Preserve material meaning",
        "temperature": 0.2,
        "top_p": 0.9,
        "max_output_tokens": 512,
    }
    assert result.requested_options == {
        "temperature": 0.2,
        "top_p": 0.9,
        "max_tokens": 512,
    }
    assert result.effective_options == result.requested_options


def test_usage_status_and_response_metadata_are_normalised() -> None:
    provider = OpenAIProvider(api_key="secret", client_factory=lambda **kwargs: FakeClient(response()))

    result = provider.generate(ProviderRequest(model="requested-alias", prompt="Hello"))

    assert result.provider == "openai"
    assert result.model == "gpt-5.2"
    assert result.finish_reason == "completed"
    assert result.usage.input_tokens == 11
    assert result.usage.output_tokens == 4
    assert result.usage.total_tokens == 15
    assert result.metadata["response_id"] == "resp_123"
    assert result.metadata["response_status"] == "completed"
    assert result.metadata["reasoning_tokens"] == 2
    assert result.metadata["api_surface"] == "responses"


def test_incomplete_reason_becomes_finish_reason() -> None:
    incomplete = response()
    incomplete.status = "incomplete"
    incomplete.incomplete_details = SimpleNamespace(reason="max_output_tokens")
    provider = OpenAIProvider(api_key="secret", client_factory=lambda **kwargs: FakeClient(incomplete))

    result = provider.generate(ProviderRequest(model="gpt-5.2", prompt="Hello"))

    assert result.finish_reason == "max_output_tokens"
    assert result.metadata["incomplete_reason"] == "max_output_tokens"


@pytest.mark.parametrize(
    ("options", "message"),
    [
        (GenerationOptions(seed=7), "seed"),
        (GenerationOptions(stop=("END",)), "stop"),
    ],
)
def test_unsupported_options_are_rejected_before_api_call(options, message) -> None:
    client = FakeClient(response())
    provider = OpenAIProvider(api_key="secret", client_factory=lambda **kwargs: client)

    with pytest.raises(ProviderConfigurationError, match=message):
        provider.generate(
            ProviderRequest(
                model="gpt-5.2",
                prompt="Hello",
                options=options,
            )
        )
    assert client.responses.calls == []


def test_output_text_falls_back_to_response_blocks() -> None:
    fallback = response(output_text="")
    fallback.output = [
        SimpleNamespace(
            content=[
                SimpleNamespace(type="output_text", text="First "),
                SimpleNamespace(type="output_text", text="second."),
            ]
        )
    ]
    provider = OpenAIProvider(api_key="secret", client_factory=lambda **kwargs: FakeClient(fallback))

    result = provider.generate(ProviderRequest(model="gpt-5.2", prompt="Hello"))

    assert result.text == "First second."


def test_missing_output_text_is_a_response_error() -> None:
    empty = response(output_text="")
    provider = OpenAIProvider(api_key="secret", client_factory=lambda **kwargs: FakeClient(empty))

    with pytest.raises(ProviderResponseError, match="output text"):
        provider.generate(ProviderRequest(model="gpt-5.2", prompt="Hello"))


def test_model_discovery_is_normalised() -> None:
    provider = OpenAIProvider(api_key="secret", client_factory=lambda **kwargs: FakeClient(response()))
    assert provider.list_models() == ["gpt-5.2", "gpt-5-mini"]


def test_connection_and_http_errors_are_normalised() -> None:
    APIConnectionError = type("APIConnectionError", (Exception,), {})
    RateLimitError = type("RateLimitError", (Exception,), {"status_code": 429})

    connection = OpenAIProvider(
        api_key="secret",
        client_factory=lambda **kwargs: FakeClient(error=APIConnectionError("offline")),
    )
    with pytest.raises(ProviderConnectionError, match="offline"):
        connection.generate(ProviderRequest(model="gpt-5.2", prompt="Hello"))

    limited = OpenAIProvider(
        api_key="secret",
        client_factory=lambda **kwargs: FakeClient(error=RateLimitError("slow down")),
    )
    with pytest.raises(ProviderHTTPError, match="429"):
        limited.generate(ProviderRequest(model="gpt-5.2", prompt="Hello"))


def test_create_provider_uses_environment_authentication() -> None:
    provider = create_provider(
        "openai",
        client_factory=lambda **kwargs: FakeClient(response()),
        environ={"OPENAI_API_KEY": "from-env"},
    )
    assert provider.describe()["api_key_configured"] is True
