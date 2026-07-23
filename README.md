# Model Modding

**Package, test and deploy portable AI-agent behaviour.**

> One versioned behavioural package. Multiple models. Declared preservation goals. Reproducible evidence.

Model Modding is an open framework for turning important assistant behaviour into inspectable, testable and portable packages rather than leaving it hidden inside application code or an unversioned prompt.

> **Model Modding will be the open packaging and assurance layer for portable AI-agent behaviour.**

The first product wedge is **meaning-preserving, evidence-backed transformation for high-stakes work**. The flagship proof is the `trusted-document-explainer` recipe: explain complex official or high-stakes text in plain English without silently changing deadlines, obligations, conditions, exceptions or uncertainty.

## Core concepts

1. **Mod** — one versioned behavioural capability or safeguard.
2. **Recipe** — an ordered composition of mods.
3. **Invariant** — a declared property that must be preserved or a transformation that must be prohibited.
4. **Evidence bundle** — the inputs, outputs, configuration and evaluation results for a run.
5. **ABOM** — an Agent Behaviour Bill of Materials describing exactly what behavioural components were built and tested.

Mods, recipes, machine-readable invariant declarations, deterministic assurance gates and the provider-neutral runtime are implemented. Evidence bundles, ABOMs and evidence-to-evidence comparison remain staged v0.2 deliverables.

## Current working loop

```text
Create → Validate → Inspect → Compose → Run → Evaluate → Publish evidence
```

```bash
python -m pip install -e ".[dev]"
modding validate
modding inspect plain-language-explainer
modding compose trusted-document-explainer
modding run trusted-document-explainer \
  --model llama3.2 \
  --prompt "Explain this notice in plain English: The applicant shall submit the requested evidence within 14 calendar days of this notice."
modding evaluate trusted-document-explainer \
  --model llama3.2 \
  --fail-on critical
modding doctor
```

Ollama remains the local default and requires no cloud API key.

## Provider-aware execution

Ollama, Anthropic and OpenAI are built-in providers behind the same neutral request and response contract.

Install cloud-provider support:

```bash
python -m pip install -e ".[anthropic,openai]"
export ANTHROPIC_API_KEY="..."
export OPENAI_API_KEY="..."
```

Run the same recipe through Anthropic:

```bash
modding evaluate trusted-document-explainer \
  --provider anthropic \
  --model claude-sonnet-4-6 \
  --temperature 0 \
  --max-tokens 1024 \
  --fail-on critical
```

Run it through OpenAI's Responses API:

```bash
modding evaluate trusted-document-explainer \
  --provider openai \
  --model gpt-5.2 \
  --max-tokens 1024 \
  --fail-on critical
```

Portable runtime options are shared across `run`, `evaluate` and `benchmark`:

```text
--temperature
--top-p
--max-tokens
--seed
--stop
```

Capability differences remain explicit. Anthropic rejects `seed` and applies a recorded `max_tokens` default of 1024 when the required field is omitted. The OpenAI Responses adapter maps `max_tokens` to `max_output_tokens` and rejects `seed` and `stop` before a paid request rather than silently ignoring them.

## What current `main` provides

- versioned mod and recipe manifests;
- JSON Schema validation with offline references;
- transformation and assurance mod roles;
- machine-readable preserved invariants and prohibited transformations;
- critical, major and minor severities;
- four narrow flagship assurance guardians;
- exactly 40 Trusted Document Explainer cases;
- 18 classified adversarial and paraphrase fixtures;
- 23 typed source facts across 16 representative cases;
- deterministic invariant and source-output comparison;
- configurable evaluation gates with critical failures blocking by default;
- provider-neutral request, response, usage and generation-option contracts;
- built-in Ollama, Anthropic and OpenAI adapters;
- provider selection across `run`, `evaluate` and `benchmark`;
- schema `0.4` execution evidence with per-response provider, model, settings, usage and finish reason;
- backward-compatible Ollama commands and imports;
- optional Anthropic and OpenAI SDKs with authentication diagnostics;
- mocked cloud-provider tests and opt-in paid smoke-test scaffolding;
- deterministic recipe composition and cross-platform references;
- local benchmarks and evidence-publication validation.

The evaluator is authoritative only for the exact deterministic assertions encoded by each case. It does not perform unrestricted semantic extraction or guarantee detection of every paraphrased meaning change. Passing checks is evidence for the tested assertions, not proof of factual correctness, safety, legal meaning or overall model quality.

No cloud-provider compatibility claim is implied merely because an adapter exists. Claims require an actual reviewed evidence bundle tied to an exact provider, model, configuration, fixture set and evaluator version.

## Flagship product contract

`trusted-document-explainer` combines:

1. `plain-language-explainer` — performs the transformation;
2. `deadline-guardian` — protects dates, durations, units and triggers;
3. `obligation-guardian` — protects actors, duties, permissions and prohibitions;
4. `exception-guardian` — protects conditions, exceptions, eligibility and sequence;
5. `source-grounding-guardian` — protects source claims, uncertainty and missing evidence.

The v0.2 proof must demonstrate the same recipe through Ollama, Anthropic and OpenAI without changing mod files, while recording exact models, settings, build digests, declared invariants, failures and limitations.

Read the [Trusted Document Explainer contract](docs/trusted-document-explainer-contract.md).

## What Model Modding is not

Model Modding is not:

- a foundation-model training or fine-tuning framework;
- a general agent-orchestration platform;
- a prompt marketplace;
- a generic observability product;
- proof that system prompts guarantee behaviour;
- a universal model leaderboard;
- a replacement for human, legal, medical or domain review.

## Documentation

- [Core concepts](docs/concepts.md)
- [Invariant declarations](docs/invariants.md)
- [Adversarial fixtures](docs/adversarial-fixtures.md)
- [Structured source-output comparison](docs/source-output-comparison-design.md)
- [Provider-neutral runtime](docs/provider-runtime.md)
- [Trusted Document Explainer contract](docs/trusted-document-explainer-contract.md)
- [Running locally](docs/running-locally.md)
- [Evaluations](docs/evaluations.md)
- [Roadmap](docs/roadmap.md)
- [Contributing](CONTRIBUTING.md)

## Project status

`v0.1.1` is the stabilised foundation release. The development line has completed the v0.1.2 flagship evaluator scope, v0.1.3 provider-neutral runtime, v0.1.4 Anthropic adapter and v0.1.5 OpenAI adapter. Reproducible builds, recipe locks, ABOMs, evidence comparison and reviewed three-provider benchmark evidence remain future increments.

## Licence

Apache License 2.0. Individual datasets, integrations or contributed assets may carry additional clearly documented terms.

**Package the behaviour. Preserve the meaning. Publish the evidence.**
