# Model Modding

**Package, test and deploy portable AI-agent behaviour.**

> One versioned behavioural package. Multiple models. Declared preservation goals. Reproducible evidence.

Model Modding is an open framework for turning important assistant behaviour into inspectable, testable and portable packages rather than leaving it hidden inside application code or an unversioned prompt.

The project is moving toward a focused proposition:

> **Model Modding will be the open packaging and assurance layer for portable AI-agent behaviour.**

The first product wedge is **meaning-preserving, evidence-backed transformation for high-stakes work**. The flagship proof is the `trusted-document-explainer` recipe: explain complex official or high-stakes text in plain English without silently changing deadlines, obligations, conditions, exceptions or uncertainty.

## Why this is more than storing a prompt

A prompt file can contain instructions. A Model Modding package is intended to make the complete behavioural contract inspectable and testable:

1. **Mod** — one versioned behavioural capability or safeguard.
2. **Recipe** — an ordered composition of mods.
3. **Invariant** — a declared property that must be preserved or a transformation that must be prohibited.
4. **Evidence bundle** — the inputs, outputs, configuration and evaluation results for a run.
5. **ABOM** — an Agent Behaviour Bill of Materials describing exactly what behavioural components were built and tested.

Mods, recipes and machine-readable invariant declarations are implemented on current `main`. Evidence bundles and ABOMs remain staged v0.2 deliverables.

## Current working loop

```text
Create → Validate → Inspect → Compose → Run → Evaluate → Publish evidence
```

```bash
python -m pip install -e ".[dev]"
modding validate
modding inspect plain-language-explainer
modding inspect deadline-guardian
modding compose trusted-document-explainer
modding run trusted-document-explainer \
  --model llama3.2 \
  --prompt "Explain this notice in plain English: The applicant shall submit the requested evidence within 14 calendar days of this notice, except where exceptional circumstances prevent compliance."
modding evaluate trusted-document-explainer \
  --model llama3.2
modding benchmark trusted-document-explainer \
  --models llama3.2,qwen2.5:3b
modding doctor
```

Local execution currently uses [Ollama](https://ollama.com/) on `127.0.0.1` by default. No cloud API key is required.

## What current `main` provides

- versioned mod and recipe manifests;
- JSON Schema validation with offline cross-schema references;
- optional `transformation` and `assurance` mod roles;
- machine-readable preserved invariants and prohibited transformations;
- strict reference vocabularies and `critical`, `major` and `minor` severities;
- invariant-aware `modding inspect` output;
- four narrow flagship assurance guardians;
- a 22-case Trusted Document Explainer evaluation plan;
- deterministic recipe composition;
- canonical cross-platform mod references;
- local Ollama execution;
- stock-versus-modded evaluation;
- latency and response-length evidence;
- multi-model local benchmarks;
- a publication protocol for benchmark evidence;
- a validator for published evidence packages;
- reference mods and recipes;
- the static Workshop, Local Dyno, Evaluation Scorecard and Fitment Matrix.

The current evaluator uses transparent deterministic checks. It can validate and display invariant declarations and execute guardian evaluation cases, but it does not yet semantically enforce those declarations. Existing checks remain useful regression signals, not proof of factual correctness, safety, legal meaning or overall model quality.

## The flagship product contract

`trusted-document-explainer` is the reference package for the v0.2 programme.

Its target purpose is:

> Rewrite complex official or high-stakes text in plain English while preserving operationally or legally material meaning.

The current recipe separates one transformation capability from four assurance concerns:

1. `plain-language-explainer` — performs the transformation;
2. `deadline-guardian` — protects dates, durations, units and triggers;
3. `obligation-guardian` — protects actors, duties, permissions and prohibitions;
4. `exception-guardian` — protects conditions, exceptions, eligibility and sequence;
5. `source-grounding-guardian` — protects source claims, uncertainty and missing evidence.

The v0.2 proof must demonstrate the same recipe running through Ollama, Anthropic and OpenAI without changing the mod files, while recording exact models, generation settings, build digests, declared invariants, failures and limitations.

Read the complete [Trusted Document Explainer product contract](docs/trusted-document-explainer-contract.md).

## Evidence before claims

The first published local benchmark is intentionally not presented as a success story. Deterministic scores improved on some cases, but human review found unsupported additions, incorrect interpretations, fabricated source details and instability between runs.

That evidence is the reason v0.2 prioritises invariant-aware evaluation, reproducible builds and regression gates before public cloud-provider comparisons.

Browse published runs under [`evidence/benchmarks/`](evidence/benchmarks/).

## What Model Modding is not

Model Modding is not:

- a foundation-model training or fine-tuning framework;
- a general agent-orchestration platform;
- a prompt marketplace;
- a generic observability product;
- proof that system prompts guarantee behaviour;
- a universal model leaderboard;
- a replacement for human, legal, medical or domain review.

See the complete [non-goals](docs/non-goals.md).

## Reference packages

### Trusted Document Explainer

Combines Plain Language Explainer with Deadline Guardian, Obligation Guardian, Exception Guardian and Source Grounding Guardian. The transformation and assurance responsibilities are versioned and independently inspectable.

### Research Learning Companion

Combines Socratic Teacher with Citation Guardian to guide learning while keeping facts, inference and uncertainty visible.

### Product Strategy Copilot

Uses Inquisitive Strategist to clarify decisions, challenge assumptions and prefer reversible experiments before expensive commitments.

## Join the community build

The project needs developers, evaluators, domain reviewers, technical writers and independent model testers.

- Browse the [community hub](community/README.md).
- Pick an open [Request for Mod](community/rfms/README.md).
- Explore the current [mod and recipe catalogue](community/catalogue.md).
- Review the [v0.2 roadmap](docs/roadmap.md).
- Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

## Try the visual workshop

Serve the repository:

```bash
python -m http.server 8000
```

Then open:

- **Workshop:** `http://localhost:8000/workshop/`
- **Local Dyno:** `http://localhost:8000/workshop/local.html`
- **Evaluation Scorecard:** `http://localhost:8000/workshop/scorecard.html`
- **Model Fitment Matrix:** `http://localhost:8000/workshop/fitment.html`

## Anatomy of a mod

```text
mods/domain/plain-language-explainer/
├── mod.yaml
├── README.md
├── instructions/system.md
├── examples/
└── evaluations/cases.yaml
```

A mod should make one understandable change, document compatibility and limitations, and include evidence for how its behaviour will be assessed.

## Create a mod

```bash
modding create mod my-first-mod \
  --category domain \
  --author "Your Name" \
  --github your-handle
```

Read [Creating mods](docs/creating-mods.md), [Invariant declarations](docs/invariants.md), the [manifest reference](docs/manifest-reference.md), and [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

## Principles

- **Portable:** the behavioural package should not be locked to one provider.
- **Assurable:** important preservation promises must become machine-readable and testable.
- **Modular:** one clearly defined capability or safeguard per mod.
- **Transparent:** instructions, configuration, evidence and limitations remain inspectable.
- **Reproducible:** builds and results should be tied to exact versions and digests.
- **Evidence-led:** compatibility claims must identify the recipe, model, evaluator, fixture set and configuration.
- **Responsible:** high-stakes claims require domain review and honest failure reporting.

## Documentation

- [Core concepts](docs/concepts.md)
- [Invariant declarations](docs/invariants.md)
- [Trusted Document Explainer contract](docs/trusted-document-explainer-contract.md)
- [Non-goals](docs/non-goals.md)
- [Five-minute quick start](docs/quickstart.md)
- [Creating mods](docs/creating-mods.md)
- [Composing recipes](docs/composing-recipes.md)
- [Running locally](docs/running-locally.md)
- [Evaluations](docs/evaluations.md)
- [Manifest reference](docs/manifest-reference.md)
- [Roadmap](docs/roadmap.md)

## Project status

`v0.1.1` is the stabilised foundation and product-direction release. Current `main` has begun the v0.1.2 delivery line with machine-readable invariant declarations and four narrow assurance guardians. It does not yet provide semantic invariant enforcement, cloud-provider portability, ABOMs, recipe locks or severity-aware regression gates.

## Licence

Apache License 2.0. Individual datasets, integrations or contributed assets may carry additional clearly documented terms.

**Package the behaviour. Preserve the meaning. Publish the evidence.**
