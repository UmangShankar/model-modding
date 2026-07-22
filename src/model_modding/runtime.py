from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from .ollama_provider import DEFAULT_OLLAMA_HOST
from .provider import GenerationOptions, ProviderAdapter, ProviderRequest, ProviderResponse, create_provider


@dataclass(frozen=True)
class RuntimeConfig:
    provider: str = "ollama"
    endpoint: str | None = None
    allow_remote: bool = False
    options: GenerationOptions = field(default_factory=GenerationOptions)

    def provider_configuration(self, opener: Callable[..., Any] | None = None) -> dict[str, Any]:
        configuration: dict[str, Any] = {}
        if self.provider.casefold() == "ollama":
            configuration["host"] = self.endpoint or DEFAULT_OLLAMA_HOST
            configuration["allow_remote"] = self.allow_remote
            if opener is not None:
                configuration["opener"] = opener
        elif self.endpoint is not None:
            configuration["endpoint"] = self.endpoint
        return configuration

    def create_adapter(self, opener: Callable[..., Any] | None = None) -> ProviderAdapter:
        return create_provider(self.provider, **self.provider_configuration(opener))

    def as_dict(self, adapter: ProviderAdapter | None = None) -> dict[str, Any]:
        description = adapter.describe() if adapter is not None else {"provider": self.provider.casefold()}
        return {
            **description,
            "requested_options": self.options.supplied(),
        }


def generation_options_from_values(
    *,
    temperature: float | None = None,
    top_p: float | None = None,
    max_tokens: int | None = None,
    seed: int | None = None,
    stop: tuple[str, ...] | list[str] | None = None,
) -> GenerationOptions:
    return GenerationOptions(
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        seed=seed,
        stop=tuple(stop or ()),
    )


def generate_response(
    runtime: RuntimeConfig,
    *,
    model: str,
    prompt: str,
    system_prompt: str = "",
    timeout: float = 120.0,
    opener: Callable[..., Any] | None = None,
    on_chunk: Callable[[str], None] | None = None,
) -> ProviderResponse:
    adapter = runtime.create_adapter(opener)
    return adapter.generate(
        ProviderRequest(
            model=model,
            prompt=prompt,
            system_prompt=system_prompt,
            options=runtime.options,
            timeout=timeout,
        ),
        on_chunk=on_chunk,
    )


def execution_metadata(response: ProviderResponse) -> dict[str, Any]:
    return response.execution_metadata()
