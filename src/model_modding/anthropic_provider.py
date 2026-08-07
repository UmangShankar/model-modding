from __future__ import annotations

import importlib
import os
import time
from collections.abc import Mapping
from typing import Any, Callable

_RETRY_ATTEMPTS = 3
_RETRY_BACKOFF = (1.0, 2.0, 4.0)

from .provider import (
    ProviderConfigurationError,
    ProviderConnectionError,
    ProviderHTTPError,
    ProviderRequest,
    ProviderResponse,
    ProviderResponseError,
    ProviderUsage,
)

DEFAULT_ANTHROPIC_ENDPOINT = "https://api.anthropic.com"
DEFAULT_ANTHROPIC_MAX_TOKENS = 1024

# Claude 5-series and later do not accept the temperature parameter.
_NO_TEMPERATURE_MODELS: frozenset[str] = frozenset(
    {"claude-sonnet-5", "claude-opus-5", "claude-fable-5", "claude-haiku-5"}
)


def _value(source: Any, name: str, default: Any = None) -> Any:
    if isinstance(source, Mapping):
        return source.get(name, default)
    return getattr(source, name, default)


def _text_content(message: Any) -> str:
    chunks: list[str] = []
    for block in _value(message, "content", []) or []:
        if _value(block, "type") == "text":
            text = _value(block, "text", "")
            if text:
                chunks.append(str(text))
    return "".join(chunks)


def _normalise_exception(exc: Exception) -> Exception:
    name = type(exc).__name__
    status_code = getattr(exc, "status_code", None)
    if name in {"APIConnectionError", "APITimeoutError"}:
        return ProviderConnectionError(f"Anthropic connection failed: {exc}")
    if name in {"AuthenticationError", "PermissionDeniedError"}:
        return ProviderConfigurationError(f"Anthropic authentication failed: {exc}")
    if status_code is not None or name.endswith("StatusError") or name in {
        "BadRequestError",
        "NotFoundError",
        "RateLimitError",
        "UnprocessableEntityError",
    }:
        return ProviderHTTPError(f"Anthropic returned {status_code or name}: {exc}")
    return ProviderResponseError(f"Invalid Anthropic response: {exc}")


class AnthropicProvider:
    name = "anthropic"

    def __init__(
        self,
        api_key: str | None = None,
        endpoint: str | None = None,
        client_factory: Callable[..., Any] | None = None,
        environ: Mapping[str, str] | None = None,
    ) -> None:
        environment = os.environ if environ is None else environ
        self.api_key = api_key or environment.get("ANTHROPIC_API_KEY")
        self.endpoint = (endpoint or environment.get("ANTHROPIC_BASE_URL") or DEFAULT_ANTHROPIC_ENDPOINT).rstrip("/")
        self._client_factory = client_factory
        if client_factory is None and not self.api_key:
            raise ProviderConfigurationError(
                "Anthropic requires ANTHROPIC_API_KEY. Install the anthropic extra and set the environment variable."
            )
        self._client: Any | None = None

    def _make_client(self, timeout: float | None = None) -> Any:
        if self._client is not None:
            return self._client
        factory = self._client_factory
        if factory is None:
            try:
                factory = importlib.import_module("anthropic").Anthropic
            except (ImportError, AttributeError) as exc:
                raise ProviderConfigurationError(
                    'Anthropic support is optional. Install it with: pip install "model-modding[anthropic]"'
                ) from exc
        kwargs: dict[str, Any] = {"api_key": self.api_key, "base_url": self.endpoint}
        if timeout is not None:
            kwargs["timeout"] = timeout
        try:
            self._client = factory(**kwargs)
        except Exception as exc:
            raise _normalise_exception(exc) from exc
        return self._client

    def describe(self) -> dict[str, Any]:
        return {
            "provider": self.name,
            "endpoint": self.endpoint,
            "authentication": "ANTHROPIC_API_KEY",
            "api_key_configured": bool(self.api_key),
        }

    def list_models(self, timeout: float = 3.0) -> list[str]:
        client = self._make_client(timeout)
        try:
            page = client.models.list(limit=100)
            data = _value(page, "data", page) or []
            return [str(_value(item, "id")) for item in data if _value(item, "id")]
        except Exception as exc:
            raise _normalise_exception(exc) from exc

    @staticmethod
    def _message_arguments(request: ProviderRequest) -> tuple[dict[str, Any], dict[str, Any]]:
        supplied = request.options.supplied()
        if request.options.seed is not None:
            raise ProviderConfigurationError("Anthropic does not support the portable seed option")
        max_tokens = request.options.max_tokens or DEFAULT_ANTHROPIC_MAX_TOKENS
        effective: dict[str, Any] = {**supplied, "max_tokens": max_tokens}
        if request.model in _NO_TEMPERATURE_MODELS:
            effective.pop("temperature", None)
        arguments: dict[str, Any] = {
            "model": request.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": request.prompt}],
        }
        if request.system_prompt:
            arguments["system"] = request.system_prompt
        if request.options.temperature is not None and request.model not in _NO_TEMPERATURE_MODELS:
            arguments["temperature"] = request.options.temperature
        if request.options.top_p is not None:
            arguments["top_p"] = request.options.top_p
        if request.options.stop:
            arguments["stop_sequences"] = list(request.options.stop)
        return arguments, effective

    def generate(
        self,
        request: ProviderRequest,
        on_chunk: Callable[[str], None] | None = None,
    ) -> ProviderResponse:
        arguments, effective = self._message_arguments(request)
        client = self._make_client(request.timeout)
        started = time.monotonic()
        last_exc: Exception | None = None
        for attempt, delay in enumerate((*_RETRY_BACKOFF, None)):
            try:
                message = client.messages.create(**arguments)
            except Exception as exc:
                normalised = _normalise_exception(exc)
                if isinstance(normalised, (ProviderConnectionError, ProviderHTTPError)) and delay is not None:
                    last_exc = normalised
                    time.sleep(delay)
                    continue
                raise normalised from exc
            text = _text_content(message)
            if not text:
                if delay is not None:
                    last_exc = ProviderResponseError("Anthropic response did not contain a text content block")
                    time.sleep(delay)
                    continue
                raise ProviderResponseError("Anthropic response did not contain a text content block")
            break
        else:
            raise last_exc  # type: ignore[misc]
        if on_chunk is not None:
            on_chunk(text)
        usage = _value(message, "usage", {}) or {}
        input_tokens = _value(usage, "input_tokens")
        output_tokens = _value(usage, "output_tokens")
        total_tokens = None
        if isinstance(input_tokens, int) and isinstance(output_tokens, int):
            total_tokens = input_tokens + output_tokens
        return ProviderResponse(
            provider=self.name,
            model=str(_value(message, "model", request.model)),
            text=text,
            latency_seconds=time.monotonic() - started,
            requested_options=request.options.supplied(),
            effective_options=effective,
            finish_reason=str(_value(message, "stop_reason")) if _value(message, "stop_reason") else None,
            usage=ProviderUsage(
                input_tokens=input_tokens if isinstance(input_tokens, int) else None,
                output_tokens=output_tokens if isinstance(output_tokens, int) else None,
                total_tokens=total_tokens,
            ),
            metadata={
                **self.describe(),
                "message_id": _value(message, "id"),
                "response_type": _value(message, "type"),
                "stop_sequence": _value(message, "stop_sequence"),
                "max_tokens_defaulted": request.options.max_tokens is None,
            },
        )
