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
- finish reason or response status;
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

The Ollama adapter maps `max_tokens` to `num_predict`. The Anthropic adapter maps stop sequences to `stop_sequences`, rejects `seed`, and applies a documented `max_tokens` value of 1024 when the caller omits the required field. The OpenAI Responses adapter maps `max_tokens` to `max_output_tokens` and rejects `seed` and `stop` before execution because that adapter cannot guarantee those portable controls through the selected API surface.

## Registry

Ollama, Anthropic and OpenAI are built-in providers:

```python
from model_modding.provider import create_provider, provider_names

print(provider_names())
ollama = create_provider("ollama", host="http://127.0.0.1:11434")
anthropic = create_provider("anthropic")
openai = create_provider("openai")
```

Third-party adapters can use `register_provider` without changing recipe or mod files.

## Command selection

Provider-aware execution is available on `run`, `evaluate` and `benchmark` by supplying `--provider`.

```bash
python -m pip install -e ".[anthropic,openai]"
export ANTHROPIC_API_KEY="..."
export OPENAI_API_KEY="..."

modding evaluate trusted-document-explainer \
  --provider openai \
  --model gpt-5.2 \
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

Provider-specific capability differences remain explicit. Unsupported options fail before a paid request rather than being silently ignored.

Existing commands that do not opt into provider selection continue through the Ollama compatibility route during migration.

## Cloud authentication and SDKs

Anthropic and OpenAI support are optional:

```bash
python -m pip install -e ".[anthropic,openai]"
```

The Anthropic adapter reads `ANTHROPIC_API_KEY` and optional `ANTHROPIC_BASE_URL`. The OpenAI adapter reads `OPENAI_API_KEY` and optional `OPENAI_BASE_URL`. API keys are never included in runtime metadata or reports.

`modding doctor` reports the SDK and API-key state for each cloud provider as optional readiness checks. Missing cloud credentials do not make local release readiness fail.

## Anthropic request and response mapping

The Anthropic adapter uses the Messages API contract:

- compiled recipe instructions map to the top-level `system` field;
- the case or user input maps to one user message;
- text content blocks are joined into the normalised response text;
- returned model, message ID and stop sequence are retained as labelled metadata;
- input and output token counts are normalised into `ProviderUsage`;
- `stop_reason` becomes the provider-neutral finish reason.

## OpenAI request and response mapping

The OpenAI adapter uses the Responses API contract:

- compiled recipe instructions map to `instructions`;
- the case or user input maps to `input`;
- `max_tokens` maps to `max_output_tokens`;
- `output_text` is preferred, with a deterministic fallback that joins `output_text` content blocks;
- returned model, response ID, status, service tier and incomplete reason are retained as labelled metadata;
- input, output and total token counts are normalised into `ProviderUsage`;
- an incomplete reason becomes the provider-neutral finish reason, otherwise response status is recorded.

Both cloud adapters normalise authentication, connection, timeout, HTTP and malformed-response failures into the shared provider error hierarchy.

## Execution evidence

Provider-aware evaluation and benchmark reports use schema `0.4` and record:

- selected provider and endpoint;
- exact requested and returned model identifiers;
- requested and effective generation settings;
- per-response latency;
- finish reason or response status;
- normalised input, output and total token counts;
- labelled provider metadata.

Each stock and modded case result contains its own `execution` object. This prevents a report-level provider label from hiding per-call differences or missing metadata.

## Live smoke tests

Normal CI never calls cloud providers. Mocked tests cover request mapping, usage, status or finish reasons, model discovery and error normalisation.

Paid smoke tests are opt-in only:

```bash
export MODEL_MODDING_LIVE_ANTHROPIC=1
export ANTHROPIC_API_KEY="..."
export ANTHROPIC_SMOKE_MODEL="claude-sonnet-4-6"
pytest tests/test_anthropic_live.py

export MODEL_MODDING_LIVE_OPENAI=1
export OPENAI_API_KEY="..."
export OPENAI_SMOKE_MODEL="gpt-5.2"
pytest tests/test_openai_live.py
```

Use explicit allowed models and protected environments with cost limits.

## Current limitation

Ollama, Anthropic and OpenAI adapters are built in. Adapter availability is not a compatibility claim. No three-provider benchmark claim should be published until actual evidence bundles have been generated, validated and reviewed for exact models and settings.
