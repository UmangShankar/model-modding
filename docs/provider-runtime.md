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

The Ollama adapter maps `max_tokens` to `num_predict`. The Anthropic adapter maps stop sequences to `stop_sequences`, rejects `seed` because the Messages API does not support it, and applies a documented `max_tokens` value of 1024 when the caller omits the required setting. The applied value is recorded in `effective_options` and `metadata.max_tokens_defaulted`.

## Registry

Ollama and Anthropic are built-in providers:

```python
from model_modding.provider import create_provider, provider_names

print(provider_names())
ollama = create_provider("ollama", host="http://127.0.0.1:11434")
anthropic = create_provider("anthropic")
```

Third-party adapters can use `register_provider` without changing recipe or mod files.

## Command selection

Provider-aware execution is available on `run`, `evaluate` and `benchmark` by supplying `--provider`.

```bash
python -m pip install -e ".[anthropic]"
export ANTHROPIC_API_KEY="..."

modding evaluate trusted-document-explainer \
  --provider anthropic \
  --model claude-sonnet-4-6 \
  --temperature 0 \
  --max-tokens 1024 \
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

Provider-specific capability differences remain explicit. Anthropic rejects `--seed` before a paid request rather than silently ignoring it.

Existing commands that do not opt into provider selection continue through the Ollama compatibility route during migration.

## Anthropic authentication and SDK

Anthropic support is optional. Install it with:

```bash
python -m pip install -e ".[anthropic]"
```

The adapter reads `ANTHROPIC_API_KEY`. `ANTHROPIC_BASE_URL` may override the default API endpoint for compatible gateways or controlled testing. API keys are never included in runtime metadata or reports.

`modding doctor` reports the Anthropic SDK and API-key state as an optional readiness check. Missing cloud credentials do not make local release readiness fail.

## Anthropic request and response mapping

The adapter uses Anthropic's Messages API contract:

- compiled recipe instructions map to the top-level `system` field;
- the case or user input maps to one user message;
- text content blocks are joined into the normalised response text;
- returned model, message ID and stop sequence are retained as labelled metadata;
- input and output token counts are normalised into `ProviderUsage`;
- `stop_reason` becomes the provider-neutral finish reason.

The adapter normalises authentication, connection, timeout, HTTP and malformed-response failures into the shared provider error hierarchy.

## Execution evidence

Provider-aware evaluation and benchmark reports use schema `0.4` and record:

- selected provider and endpoint;
- exact requested and returned model identifiers;
- requested and effective generation settings;
- per-response latency;
- finish reason;
- normalised input, output and total token counts;
- labelled provider metadata.

Each stock and modded case result contains its own `execution` object. This prevents a report-level provider label from hiding per-call differences or missing metadata.

## Live smoke tests

Normal CI never calls Anthropic. Mocked tests cover request mapping, usage, finish reasons, model discovery and error normalisation.

The paid smoke test is opt-in only:

```bash
export MODEL_MODDING_LIVE_ANTHROPIC=1
export ANTHROPIC_API_KEY="..."
export ANTHROPIC_SMOKE_MODEL="claude-sonnet-4-6"
pytest tests/test_anthropic_live.py
```

Use an explicit allowed model and a protected environment with cost limits.

## Current limitation

Ollama and Anthropic are built in. OpenAI remains the next provider adapter. No cloud benchmark claim should be published until an actual evidence bundle has been generated, validated and reviewed.