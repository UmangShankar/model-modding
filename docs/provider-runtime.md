# Provider-neutral runtime

The provider runtime separates behavioural packages from model-vendor transport details.

## Contract

A provider receives a `ProviderRequest` containing:

- the exact model identifier;
- user and compiled system prompts;
- provider-neutral generation options;
- a request timeout.

It returns a `ProviderResponse` containing:

- provider and exact model identifiers;
- complete response text;
- latency;
- requested and effective generation settings;
- normalised token usage;
- finish reason;
- provider-specific metadata kept in a labelled metadata object.

The core types live in `model_modding.provider`.

## Normalised generation options

The initial portable vocabulary is deliberately small:

- `temperature`;
- `top_p`;
- `max_tokens`;
- `seed`;
- `stop` sequences.

Unknown options fail before a provider call. Values are validated by the neutral contract before adapter mapping.

The Ollama adapter maps `max_tokens` to Ollama's `num_predict` field. Other supported settings retain their canonical names.

## Registry

Built-in and extension providers are resolved through:

```python
from model_modding.provider import create_provider, provider_names

print(provider_names())
provider = create_provider("ollama", host="http://127.0.0.1:11434")
```

Third-party adapters can use `register_provider` without changing recipe or mod files.

## Command selection

Provider-aware execution is available on `run`, `evaluate` and `benchmark` by supplying `--provider`. Ollama remains the default registered adapter.

```bash
modding evaluate trusted-document-explainer \
  --provider ollama \
  --model llama3.2 \
  --temperature 0 \
  --seed 7 \
  --fail-on critical
```

The portable settings are available consistently across all three runtime commands:

```text
--temperature
--top-p
--max-tokens
--seed
--stop
```

Existing commands that do not opt into provider selection continue through the legacy compatibility route during the v0.1.3 migration. This preserves established scripts while the provider-aware route is proven.

## Ollama migration

The existing `model_modding.ollama` functions remain as compatibility wrappers. Model discovery, streaming and recipe execution delegate to `OllamaProvider`.

This keeps existing commands and imports working while moving transport ownership behind the provider boundary.

## Execution evidence

Provider-aware evaluation and benchmark reports use schema `0.4` and record:

- selected provider and endpoint;
- exact requested and resolved model identifiers;
- requested and effective generation settings;
- per-response latency;
- finish reason;
- normalised input, output and total token counts;
- labelled provider metadata.

Each stock and modded case result contains its own `execution` object. This prevents a report-level provider label from hiding per-call differences or missing metadata.

## Metadata boundary

Ollama reports token counts and some timing information in its final streaming event. These are normalised into `ProviderUsage` and labelled metadata.

Ollama does not report every effective default. When a setting was not supplied, the adapter does not invent an effective value. The response metadata records `provider_defaults_not_reported: true`.

## Error boundary

Adapters normalise failures into:

- `ProviderConfigurationError`;
- `ProviderConnectionError`;
- `ProviderHTTPError`;
- `ProviderResponseError`.

Unknown providers and invalid portable options fail before a model request.

## Current limitation

Only Ollama is registered as a built-in provider. The runtime contract, selection surfaces and evidence schema are ready for Anthropic and OpenAI adapters, but those implementations, credentials and live tests are separate delivery increments.
