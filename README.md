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
4. **Recipe lock** — the canonical source inventory and digest inputs for one behavioural build.
5. **ABOM** — an Agent Behaviour Bill of Materials describing what behavioural components were built.
6. **Evidence bundle** — durable raw responses, execution context, build identity and interpreted results for one run.
7. **Evidence comparison** — a strict baseline-versus-candidate delta over verified comparable evidence.
8. **Compatibility matrix** — a contextual provider/model-by-invariant summary.
9. **Repeated evidence aggregate** — multiple executions of the same locked build grouped by exact target.
10. **Release readiness** — an explicit gate over provider coverage, repetitions, cases and critical failures.

## Working loop

```text
Create → Validate → Inspect → Compose → Build → Verify → Execute → Evaluate
→ Verify evidence → Compare → Aggregate → Matrix → Review baseline → Release check
```

```bash
python -m pip install -e ".[dev]"
modding validate
modding inspect plain-language-explainer
modding compose trusted-document-explainer
modding build trusted-document-explainer
modding verify-build trusted-document-explainer
modding evaluate trusted-document-explainer \
  --provider ollama \
  --model llama3.2 \
  --fail-on critical \
  --evidence build/evidence/evaluation-run
modding verify-evidence build/evidence/evaluation-run
modding compare-evidence evidence/baseline evidence/candidate --fail-on critical
modding matrix-evidence evidence/ollama evidence/anthropic evidence/openai
modding aggregate-evidence evidence/run-1 evidence/run-2 evidence/run-3 \
  --minimum-repetitions 3 \
  --require-zero-critical \
  --output build/aggregate
```

Ollama remains the local default and requires no cloud API key.

## Behavioural build identity

`modding build` creates a deterministic bundle:

```text
build/trusted-document-explainer/
├── system.md
├── recipe.lock.json
├── abom.json
├── abom.md
└── manifest.json
```

The deterministic `build` and offline `verify-build` commands record ordered components, versions, roles, licences, machine-readable invariant declarations, source hashes, the compiled-prompt digest and an independently recomputable build digest.

Line endings are normalised for equivalent Windows and POSIX checkouts. Every other behavioural source change invalidates the identity. An ABOM is a build inventory; it is not evidence that a model complied. Agent Behaviour Bills of Materials are available in JSON and Markdown.

## Assurance evaluator

The flagship contains four narrow flagship assurance guardians for deadlines, obligations, exceptions and source grounding. It has exactly 40 cases, including adversarial and paraphrase fixtures, and 23 typed source facts.

The deterministic invariant and source-output comparison creates structured critical, major and minor failures. The evaluator does not perform unrestricted semantic extraction or guarantee detection of every paraphrased meaning change.

## Provider-neutral execution

The runtime exposes provider-neutral request, response, usage and generation-option contracts. It includes built-in Ollama, Anthropic and OpenAI adapters.

```bash
python -m pip install -e ".[anthropic,openai]"
export ANTHROPIC_API_KEY="..."
export OPENAI_API_KEY="..."
```

Capability differences remain explicit. Anthropic rejects unsupported `seed`; OpenAI's Responses adapter rejects unsupported `seed` and `stop`; unsupported options fail before a paid request.

## Durable evidence

Provider-aware `run`, `evaluate` and `benchmark` can emit durable run, evaluation and benchmark evidence bundles.

```text
manifest.json
responses.jsonl
recipe.lock.json
abom.json
evaluation.json    # evaluation and benchmark bundles
```

Prompt text is omitted by default and represented by a SHA-256 value. Exact raw responses remain separate from interpreted evaluation. The versioned evidence schema and offline `verify-evidence` command detect tampering, missing artifacts, broken build identities and unexpected files.

A valid evidence bundle proves internal file and hash agreement. It does not prove semantic correctness.

## Regression comparison and matrices

`modding compare-evidence` provides strict baseline-versus-candidate `compare-evidence` regression gates. Bundle type, recipe identity, build digest, fixture-set digest, evaluator and target set must match before behavioural deltas are calculated.

The report separates new, resolved and unchanged failures, severity changes and escalations. New or escalated failures at the configured threshold return exit code `1`; invalid or non-comparable evidence returns `2`.

`modding matrix-evidence` creates provider/model-by-invariant `matrix-evidence` summaries. Cells record tested, passed and failed encoded observations for one exact build, fixture set, evaluator and configuration. They are not universal provider rankings.

## Repeated evidence, baselines and release readiness

Aggregate repeated compatible runs:

```bash
modding aggregate-evidence evidence/run-1 evidence/run-2 evidence/run-3 \
  --minimum-repetitions 3 \
  --require-zero-critical \
  --output build/aggregate
```

Activate a scoped reviewed baseline:

```bash
modding activate-baseline evidence/candidate evidence/baselines/current \
  --reviewer "Review group" \
  --scope "Exact comparison scope"
```

Create a concise CI or pull-request summary:

```bash
modding evidence-summary \
  --comparison build/comparison/comparison.json \
  --matrix build/matrix/matrix.json \
  --aggregate build/aggregate/aggregate.json \
  --output build/evidence-summary.md
```

The v0.2 release gate requires:

- the same locked recipe, fixture set and evaluator;
- Ollama, Anthropic and OpenAI evidence;
- at least three repetitions per exact target;
- all 40 cases in every repetition;
- zero critical failures;
- passing compatibility-matrix target status.

```bash
modding release-check \
  --aggregate build/release-candidate/aggregate/aggregate.json \
  --matrix build/release-candidate/matrix/matrix.json \
  --minimum-repetitions 3 \
  --minimum-cases 40 \
  --output build/release-candidate/readiness
```

## Protected workflows

The repository includes:

- `evidence-pr-summary.yml` — automatic pull-request summaries from clearly labelled synthetic contract evidence;
- `provider-evidence.yml` — manual, environment-protected Anthropic or OpenAI runs with exact model allowlists, capped repetitions and capped output tokens;
- `ollama-evidence.yml` — manual execution on an allowlisted self-hosted Ollama runner;
- `release-evidence.yml` — assembly and validation of checked-in reviewed release evidence;
- `release.yml` — package publication, with v0.2 tags blocked unless reviewed evidence passes the release gate.

Synthetic CI evidence validates pipeline mechanics only. It is never a cloud-provider compatibility claim.

Read [the complete v0.2 release pipeline](docs/release-pipeline.md) and [the independent reproduction guide](docs/reproduce-v020.md).

## What current `main` provides

- versioned mod and recipe manifests;
- machine-readable invariant declarations;
- four narrow assurance guardians;
- exactly 40 flagship cases and 23 typed source facts;
- deterministic invariant and source-output comparison;
- provider-neutral request, response, usage and generation-option contracts;
- built-in Ollama, Anthropic and OpenAI adapters;
- deterministic `build` and offline `verify-build` commands;
- recipe locks and Agent Behaviour Bills of Materials;
- durable run, evaluation and benchmark evidence bundles;
- versioned evidence schema and offline `verify-evidence` command;
- strict baseline-versus-candidate `compare-evidence` regression gates;
- provider/model-by-invariant `matrix-evidence` summaries;
- repeated-run aggregation and scoped baseline activation;
- automatic pull-request evidence summaries;
- protected and cost-limited provider workflows;
- v0.2 release-readiness and tag-publication gates.

No cloud-provider compatibility claim is implied merely because an adapter, workflow, evidence format, comparison, aggregate or matrix exists. Claims require actual reviewed evidence tied to an exact provider, model, build digest, configuration, fixture set and evaluator version.

## Flagship product contract

`trusted-document-explainer` combines one transformation mod with deadline, obligation, exception and source-grounding guardians. The [Trusted Document Explainer contract](docs/trusted-document-explainer-contract.md) defines its acceptance criteria and interpretation boundaries.

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
- [Structured source-output comparison](docs/source-output-comparison-design.md)
- [Provider-neutral runtime](docs/provider-runtime.md)
- [Reproducible builds, recipe locks and ABOMs](docs/reproducible-builds.md)
- [Durable run evidence bundles](docs/run-evidence.md)
- [Evidence comparison and compatibility matrices](docs/evidence-comparison.md)
- [v0.2 release evidence pipeline](docs/release-pipeline.md)
- [Independent v0.2 reproduction](docs/reproduce-v020.md)
- [Trusted Document Explainer contract](docs/trusted-document-explainer-contract.md)
- [Roadmap](docs/roadmap.md)
- [Contributing](CONTRIBUTING.md)

## Project status

The complete v0.1.7 engineering pipeline is implemented. v0.2.0 is **not yet an evidence-backed release claim**: reviewed three-provider runs, baseline approval and independent reproduction must still be supplied through the enforced pipeline.

## Licence

Apache License 2.0. Individual datasets, integrations or contributed assets may carry additional clearly documented terms.

**Package the behaviour. Preserve the meaning. Publish the evidence.**
