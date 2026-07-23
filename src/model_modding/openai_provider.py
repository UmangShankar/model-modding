from __future__ import annotations

import importlib
import os
import time
from collections.abc import Mapping
from typing import Any, Callable

from .provider import (
    ProviderConfigurationError,
    ProviderConnectionError,
    ProviderHTTPError,
    ProviderRequest,
    ProviderResponse,
    ProviderResponseError,
    ProviderUsage,
)

DEFAULT_OPENAI_ENDPOINT = "https://api.openai.com/v1"


def _value(source: Any, name: str, default: Any = None) -> Any:
    if isinstance(source, Mapping):
        return source.get(name, default)
    return getattr(source, name, default)


def _output_text(response: Any) -> str:
    direct = _value(response, "output_text", "")
    if direct:
        return str(direct)
    chunks: list[str] = []
    for item in _value(response, "output", []) or []:
        for block in _value(item, "content", []) or []:
            if _value(block, "type") == "output_text":
                text = _value(block, "text", "")
                if text:
                    chunks.append(str(text))
    return "".join(chunks)


def _normalise_exception(exc: Exception) -> Exception:
    name = type(exc).__name__
    status_code = getattr(exc, "status_code", None)
    if name in {"APIConnectionError", "APITimeoutError"}:
        return ProviderConnectionError(f"OpenAI connection failed: {exc}")
    if name in {"AuthenticationError", "PermissionDeniedError"}:
        return ProviderConfigurationError(f"OpenAI authentication failed: {exc}")
    if status_code is not None or name.endswith("StatusError") or name in {
        "BadRequestError",
        "ConflictError",
        "InternalServerError",
        "NotFoundError",
        "RateLimitError",
        "UnprocessableEntityError",
    }:
        return ProviderHTTPError(f"OpenAI returned {status_code or name}: {exc}")
    return ProviderResponseError(f"Invalid OpenAI response: {exc}")


class OpenAIProvider:
    name = "openai"

    def __init__(
        self,
        api_key: str | None = None,
        endpoint: str | None = None,
        client_factory: Callable[..., Any] | None = None,
        environ: Mapping[str, str] | None = None,
    ) -> None:
        environment = os.environ if environ is None else environ
        self.api_key = api_key or environment.get("OPENAI_API_KEY")
        self.endpoint = (endpoint or environment.get("OPENAI_BASE_URL") or DEFAULT_OPENAI_ENDPOINT).rstrip("/")
        self._client_factory = client_factory
        if client_factory is None and not self.api_key:
            raise ProviderConfigurationError(
                "OpenAI requires OPENAI_API_KEY. Install the openai extra and set the environment variable."
            )
        self._client: Any | None = None

    def _make_client(self, timeout: float | None = None) -> Any:
        if self._client is not None:
            return self._client
        factory = self._client_factory
        if factory is None:
            try:
                factory = importlib.import_module("openai").OpenAI
            except (ImportError, AttributeError) as exc:
                raise ProviderConfigurationError(
                    'OpenAI support is optional. Install it with: pip install "model-modding[openai]"'
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
            "authentication": "OPENAI_API_KEY",
            "api_key_configured": bool(self.api_key),
            "api_surface": "responses",
        }

    def list_models(self, timeout: float = 3.0) -> list[str]:
        client = self._make_client(timeout)
        try:
            page = client.models.list()
            data = _value(page, "data", page) or []
            return [str(_value(item, "id")) for item in data if _value(item, "id")]
        except Exception as exc:
            raise _normalise_exception(exc) from exc

    @staticmethod
    def _response_arguments(request: ProviderRequest) -> tuple[dict[str, Any], dict[str, Any]]:
        if request.options.seed is not None:
            raise ProviderConfigurationError("OpenAI Responses does not support the portable seed option")
        if request.options.stop:
            raise ProviderConfigurationError("OpenAI Responses does not support the portable stop option")
        supplied = request.options.supplied()
        effective = dict(supplied)
        arguments: dict[str, Any] = {
            "model": request.model,
            "input": request.prompt,
        }
        if request.system_prompt:
            arguments["instructions"] = request.system_prompt
        if request.options.temperature is not None:
            arguments["temperature"] = request.options.temperature
        if request.options.top_p is not None:
            arguments["top_p"] = request.options.top_p
        if request.options.max_tokens is not None:
            arguments["max_output_tokens"] = request.options.max_tokens
        return arguments, effective

    def generate(
        self,
        request: ProviderRequest,
        on_chunk: Callable[[str], None] | None = None,
    ) -> ProviderResponse:
        arguments, effective = self._response_arguments(request)
        client = self._make_client(request.timeout)
        started = time.monotonic()
        try:
            response = client.responses.create(**arguments)
        except Exception as exc:
            raise _normalise_exception(exc) from exc
        text = _output_text(response)
        if not text:
            raise ProviderResponseError("OpenAI response did not contain output text")
        if on_chunk is not None:
            on_chunk(text)
        usage = _value(response, "usage", {}) or {}
        input_tokens = _value(usage, "input_tokens")
        output_tokens = _value(usage, "output_tokens")
        total_tokens = _value(usage, "total_tokens")
        if not isinstance(total_tokens, int) and isinstance(input_tokens, int) and isinstance(output_tokens, int):
            total_tokens = input_tokens + output_tokens
        incomplete = _value(response, "incomplete_details", {}) or {}
        status = _value(response, "status")
        incomplete_reason = _value(incomplete, "reason")
        finish_reason = str(incomplete_reason or status) if (incomplete_reason or status) else None
        output_details = _value(usage, "output_tokens_details", {}) or {}
        return ProviderResponse(
            provider=self.name,
            model=str(_value(response, "model", request.model)),
            text=text,
            latency_seconds=time.monotonic() - started,
            requested_options=request.options.supplied(),
            effective_options=effective,
            finish_reason=finish_reason,
            usage=ProviderUsage(
                input_tokens=input_tokens if isinstance(input_tokens, int) else None,
                output_tokens=output_tokens if isinstance(output_tokens, int) else None,
                total_tokens=total_tokens if isinstance(total_tokens, int) else None,
            ),
            metadata={
                **self.describe(),
                "response_id": _value(response, "id"),
                "response_status": status,
                "created_at": _value(response, "created_at"),
                "incomplete_reason": incomplete_reason,
                "reasoning_tokens": _value(output_details, "reasoning_tokens"),
                "service_tier": _value(response, "service_tier"),
            },
        )
