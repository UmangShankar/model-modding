from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Protocol


@dataclass(frozen=True)
class GenerationOptions:
    """Provider-neutral generation settings supplied by a caller."""

    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    seed: int | None = None
    stop: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.temperature is not None and self.temperature < 0:
            raise ValueError("temperature must be greater than or equal to zero")
        if self.top_p is not None and not 0 < self.top_p <= 1:
            raise ValueError("top_p must be greater than zero and at most one")
        if self.max_tokens is not None and self.max_tokens <= 0:
            raise ValueError("max_tokens must be greater than zero")
        if any(not item for item in self.stop):
            raise ValueError("stop sequences must not be empty")

    def supplied(self) -> dict[str, Any]:
        values: dict[str, Any] = {}
        if self.temperature is not None:
            values["temperature"] = self.temperature
        if self.top_p is not None:
            values["top_p"] = self.top_p
        if self.max_tokens is not None:
            values["max_tokens"] = self.max_tokens
        if self.seed is not None:
            values["seed"] = self.seed
        if self.stop:
            values["stop"] = list(self.stop)
        return values

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any] | None) -> "GenerationOptions":
        if not values:
            return cls()
        allowed = {"temperature", "top_p", "max_tokens", "seed", "stop"}
        unknown = sorted(set(values) - allowed)
        if unknown:
            raise ValueError(f"Unsupported generation options: {', '.join(unknown)}")
        raw_stop = values.get("stop", ())
        if isinstance(raw_stop, str):
            stop = (raw_stop,)
        elif isinstance(raw_stop, (list, tuple)):
            stop = tuple(str(item) for item in raw_stop)
        else:
            raise ValueError("stop must be a string or list of strings")
        return cls(
            temperature=float(values["temperature"]) if values.get("temperature") is not None else None,
            top_p=float(values["top_p"]) if values.get("top_p") is not None else None,
            max_tokens=int(values["max_tokens"]) if values.get("max_tokens") is not None else None,
            seed=int(values["seed"]) if values.get("seed") is not None else None,
            stop=stop,
        )


@dataclass(frozen=True)
class ProviderRequest:
    model: str
    prompt: str
    system_prompt: str = ""
    options: GenerationOptions = field(default_factory=GenerationOptions)
    timeout: float = 120.0

    def __post_init__(self) -> None:
        if not self.model.strip():
            raise ValueError("model must not be empty")
        if not self.prompt.strip():
            raise ValueError("prompt must not be empty")
        if self.timeout <= 0:
            raise ValueError("timeout must be greater than zero")


@dataclass(frozen=True)
class ProviderUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None

    def as_dict(self) -> dict[str, int | None]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass(frozen=True)
class ProviderResponse:
    provider: str
    model: str
    text: str
    latency_seconds: float
    requested_options: dict[str, Any]
    effective_options: dict[str, Any]
    finish_reason: str | None = None
    usage: ProviderUsage = field(default_factory=ProviderUsage)
    metadata: dict[str, Any] = field(default_factory=dict)

    def execution_metadata(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "requested_options": self.requested_options,
            "effective_options": self.effective_options,
            "finish_reason": self.finish_reason,
            "usage": self.usage.as_dict(),
            "metadata": self.metadata,
        }


class ProviderError(RuntimeError):
    """Base class for normalised provider failures."""


class ProviderConfigurationError(ProviderError):
    pass


class ProviderConnectionError(ProviderError):
    pass


class ProviderHTTPError(ProviderError):
    pass


class ProviderResponseError(ProviderError):
    pass


class ProviderAdapter(Protocol):
    name: str

    def list_models(self, timeout: float = 3.0) -> list[str]: ...

    def generate(
        self,
        request: ProviderRequest,
        on_chunk: Callable[[str], None] | None = None,
    ) -> ProviderResponse: ...

    def describe(self) -> dict[str, Any]: ...


ProviderFactory = Callable[..., ProviderAdapter]
_PROVIDER_FACTORIES: dict[str, ProviderFactory] = {}


def register_provider(name: str, factory: ProviderFactory, *, replace: bool = False) -> None:
    normalized = name.strip().casefold()
    if not normalized:
        raise ValueError("provider name must not be empty")
    if normalized in _PROVIDER_FACTORIES and not replace:
        raise ValueError(f"Provider is already registered: {normalized}")
    _PROVIDER_FACTORIES[normalized] = factory


def _load_builtin(name: str) -> None:
    if name == "ollama" and name not in _PROVIDER_FACTORIES:
        from .ollama_provider import OllamaProvider

        register_provider("ollama", OllamaProvider)
    if name == "anthropic" and name not in _PROVIDER_FACTORIES:
        from .anthropic_provider import AnthropicProvider

        register_provider("anthropic", AnthropicProvider)
    if name == "openai" and name not in _PROVIDER_FACTORIES:
        from .openai_provider import OpenAIProvider

        register_provider("openai", OpenAIProvider)


def provider_names() -> tuple[str, ...]:
    _load_builtin("ollama")
    _load_builtin("anthropic")
    _load_builtin("openai")
    return tuple(sorted(_PROVIDER_FACTORIES))


def create_provider(name: str, **configuration: Any) -> ProviderAdapter:
    normalized = name.strip().casefold()
    _load_builtin(normalized)
    factory = _PROVIDER_FACTORIES.get(normalized)
    if factory is None:
        available = ", ".join(provider_names()) or "none"
        raise ProviderConfigurationError(f"Unknown provider: {name}. Available providers: {available}")
    try:
        return factory(**configuration)
    except ProviderError:
        raise
    except (TypeError, ValueError) as exc:
        raise ProviderConfigurationError(f"Invalid {normalized} provider configuration: {exc}") from exc
