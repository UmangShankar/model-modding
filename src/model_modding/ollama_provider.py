from __future__ import annotations

import json
import time
from typing import Any, Callable, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .provider import (
    ProviderConnectionError,
    ProviderHTTPError,
    ProviderRequest,
    ProviderResponse,
    ProviderResponseError,
    ProviderUsage,
)

DEFAULT_OLLAMA_HOST = "http://127.0.0.1:11434"


def validate_ollama_host(host: str, allow_remote: bool = False) -> str:
    normalized = host.rstrip("/")
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Ollama host must be an http(s) URL")
    loopback = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    if not loopback and not allow_remote:
        raise ValueError(
            "Refusing non-loopback Ollama host. Pass --allow-remote-host only when you trust the endpoint."
        )
    return normalized


class OllamaProvider:
    name = "ollama"

    def __init__(
        self,
        host: str = DEFAULT_OLLAMA_HOST,
        allow_remote: bool = False,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        self.host = validate_ollama_host(host, allow_remote)
        self.allow_remote = allow_remote
        self.opener = opener

    def describe(self) -> dict[str, Any]:
        return {
            "provider": self.name,
            "endpoint": self.host,
            "remote_endpoint_allowed": self.allow_remote,
        }

    def list_models(self, timeout: float = 3.0) -> list[str]:
        request = Request(f"{self.host}/api/tags", headers={"Accept": "application/json"})
        try:
            with self.opener(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            raise ProviderHTTPError(
                f"Ollama returned HTTP {exc.code}: {detail or exc.reason}"
            ) from exc
        except (URLError, TimeoutError, ConnectionError, OSError) as exc:
            raise ProviderConnectionError(f"Could not reach Ollama at {self.host}: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise ProviderResponseError(f"Invalid Ollama model-list response: {exc}") from exc
        return [
            item["name"]
            for item in payload.get("models", [])
            if isinstance(item, dict) and item.get("name")
        ]

    @staticmethod
    def _ollama_options(request: ProviderRequest) -> dict[str, Any]:
        supplied = request.options.supplied()
        mapped: dict[str, Any] = {}
        if "temperature" in supplied:
            mapped["temperature"] = supplied["temperature"]
        if "top_p" in supplied:
            mapped["top_p"] = supplied["top_p"]
        if "max_tokens" in supplied:
            mapped["num_predict"] = supplied["max_tokens"]
        if "seed" in supplied:
            mapped["seed"] = supplied["seed"]
        if "stop" in supplied:
            mapped["stop"] = supplied["stop"]
        return mapped

    def _request_payload(self, request: ProviderRequest) -> dict[str, Any]:
        messages: list[dict[str, str]] = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        payload: dict[str, Any] = {
            "model": request.model,
            "stream": True,
            "messages": messages,
        }
        options = self._ollama_options(request)
        if options:
            payload["options"] = options
        return payload

    def iter_events(self, request: ProviderRequest) -> Iterable[dict[str, Any]]:
        body = json.dumps(self._request_payload(request)).encode("utf-8")
        http_request = Request(
            f"{self.host}/api/chat",
            data=body,
            method="POST",
            headers={"Content-Type": "application/json", "Accept": "application/x-ndjson"},
        )
        try:
            with self.opener(http_request, timeout=request.timeout) as response:
                for raw_line in response:
                    if not raw_line.strip():
                        continue
                    event = json.loads(raw_line.decode("utf-8"))
                    if event.get("error"):
                        raise ProviderResponseError(str(event["error"]))
                    yield event
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            raise ProviderHTTPError(
                f"Ollama returned HTTP {exc.code}: {detail or exc.reason}"
            ) from exc
        except (URLError, TimeoutError, ConnectionError, OSError) as exc:
            raise ProviderConnectionError(f"Could not reach Ollama at {self.host}: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise ProviderResponseError(f"Invalid Ollama response: {exc}") from exc

    def stream_text(self, request: ProviderRequest) -> Iterable[str]:
        for event in self.iter_events(request):
            message = event.get("message", {})
            chunk = message.get("content", "") if isinstance(message, dict) else ""
            if chunk:
                yield chunk

    def generate(
        self,
        request: ProviderRequest,
        on_chunk: Callable[[str], None] | None = None,
    ) -> ProviderResponse:
        started = time.monotonic()
        chunks: list[str] = []
        final_event: dict[str, Any] = {}
        for event in self.iter_events(request):
            final_event = event
            message = event.get("message", {})
            chunk = message.get("content", "") if isinstance(message, dict) else ""
            if chunk:
                chunks.append(chunk)
                if on_chunk is not None:
                    on_chunk(chunk)
        input_tokens = final_event.get("prompt_eval_count")
        output_tokens = final_event.get("eval_count")
        total_tokens = None
        if isinstance(input_tokens, int) and isinstance(output_tokens, int):
            total_tokens = input_tokens + output_tokens
        requested = request.options.supplied()
        return ProviderResponse(
            provider=self.name,
            model=request.model,
            text="".join(chunks),
            latency_seconds=time.monotonic() - started,
            requested_options=requested,
            effective_options=requested,
            finish_reason=str(final_event.get("done_reason")) if final_event.get("done_reason") else None,
            usage=ProviderUsage(
                input_tokens=input_tokens if isinstance(input_tokens, int) else None,
                output_tokens=output_tokens if isinstance(output_tokens, int) else None,
                total_tokens=total_tokens,
            ),
            metadata={
                **self.describe(),
                "provider_defaults_not_reported": True,
                "load_duration_ns": final_event.get("load_duration"),
                "prompt_eval_duration_ns": final_event.get("prompt_eval_duration"),
                "eval_duration_ns": final_event.get("eval_duration"),
            },
        )
