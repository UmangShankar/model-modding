# Trusted Document Explainer product contract

## Status

This document defines the target reference product for Model Modding v0.2.0. It is a product and engineering contract, not a claim that the current development line already satisfies every requirement.

## Purpose

> Rewrite complex official or high-stakes text in plain English while preserving operationally or legally material meaning.

## Intended users

The reference package is intended for people who need to understand notices, policies, clauses, letters or other high-stakes text without losing the details that determine what must happen, who must act, when action is required and which qualifications apply.

## Required transformation behaviour

The package should:

- simplify language and sentence structure;
- explain essential technical or legal terms rather than silently deleting them;
- distinguish source statements from interpretation;
- retain uncertainty and discretion;
- request missing evidence rather than inventing it;
- avoid adding advice or next steps that are not supported by the source.

## Material meaning to preserve

The implemented initial invariant vocabulary includes:

- deadlines;
- dates and durations;
- amounts and percentages;
- named parties;
- obligations;
- prohibitions;
- conditions;
- exceptions;
- eligibility rules;
- sequence;
- source claims;
- uncertainty.

These declarations are schema-validated, inspectable and can be bound to explicit deterministic evaluator checks. General semantic comparison remains a later evaluator capability.

## Prohibited transformations

The package must detect and report material failures such as:

- changing an exact deadline or its trigger;
- converting calendar days to working days or the reverse;
- changing the responsible party;
- weakening, strengthening or reversing an obligation;
- removing or reversing a condition or exception;
- inventing an entitlement, duty, action or notification requirement;
- inventing medical or legal advice;
- inventing a study, quotation, source or citation;
- treating system instructions as user-provided evidence;
- removing a material technical distinction;
- presenting missing evidence as supplied evidence.

## Current composition

Trusted Document Explainer `0.2.0` separates transformation from assurance.

Transformation:

- `plain-language-explainer`

Assurance:

- `deadline-guardian`
- `obligation-guardian`
- `exception-guardian`
- `source-grounding-guardian`

Each guardian has one narrow responsibility, machine-readable invariants, focused instructions, examples, limitations and an independent four-case evaluation suite. The combined flagship evaluation plan contains at least 22 cases.

This composition makes the behavioural contract inspectable and deterministically testable for its encoded assertions. It does not prove semantic compliance with every declared invariant.

## Portability target

The same recipe build must run through:

- Ollama;
- Anthropic;
- OpenAI.

No mod file may be changed between providers.

Every result must record the provider, exact model identifier, supplied and effective generation settings, recipe digest, evaluator version and fixture set.

## Evaluation authority

Quality gates are ordered as follows:

1. deterministic invariant checks;
2. structured source-output comparison;
3. optional model-assisted judgement;
4. recorded human review.

Evaluator v2 implements the first layer. Guardian cases target manifest-declared invariants, require matching severities and produce structured critical, major and minor failures. The default command gate fails on critical modded failures.

A model judge must never be the sole gate and cannot override an exact deterministic critical failure.

## Severity model

- **Critical** — material meaning changed, invented or removed in a way that could alter action, entitlement, safety or compliance.
- **Major** — important clarity, grounding or qualification failure that requires review but does not meet the critical definition.
- **Minor** — presentation or readability weakness with no material meaning change.

A new critical failure must fail the configured evaluation gate regardless of aggregate score.

## Current evaluation command

```text
modding evaluate trusted-document-explainer \
  --model llama3.2 \
  --fail-on critical
```

Supported thresholds are `critical`, `major`, `minor` and `none`. The `none` setting records failures without blocking and is intended for exploratory evidence collection only.

Evaluation reports use schema `0.2` and include evaluator identity, structured failures, severity totals, per-mod summaries, pipeline status and blocking failures. Multi-model benchmarks use the same invariant-scoring path.

## Build target

The target command is:

```text
modding build trusted-document-explainer
```

The build should produce:

```text
build/trusted-document-explainer/
├── compiled-instructions.md
├── recipe.lock.yaml
├── abom.json
├── abom.md
├── build-manifest.json
└── build.sha256
```

Canonicalisation must define UTF-8 encoding, LF line endings, stable ordering, relative POSIX paths, schema versions and compiler version.

## Execution target

```text
modding run trusted-document-explainer \
  --provider ollama \
  --model llama3.2 \
  --input notice.txt \
  --evidence evidence/
```

The same recipe must execute through configured Anthropic and OpenAI targets.

## Comparison target

```text
modding matrix trusted-document-explainer \
  --targets ollama/llama3.2,anthropic/<exact-model>,openai/<exact-model>
```

The output may state:

> This provider and model passed this recipe on this fixture set under this configuration.

It must not state that one provider is universally best.

## Regression target

```text
modding regress \
  --baseline evidence/baseline.json \
  --candidate evidence/current.json \
  --fail-on critical
```

The command must fail when a new critical failure appears or when strict comparison requirements are not met.

## Evidence requirements

Every release result must identify:

- recipe ID and version;
- recipe and build digests;
- installed mods and versions;
- declared invariants;
- provider and exact model;
- generation configuration;
- evaluator version;
- case count;
- critical, major and minor failures;
- evidence-bundle location;
- ABOM digest;
- source-control commit;
- dirty-tree status;
- known limitations.

Sensitive source documents must not be copied into evidence by default.

## Release acceptance

The v0.2.0 proof is complete only when:

- the flagship recipe runs across all three providers;
- at least 40 cases are included;
- zero critical failures remain in the release candidate evidence;
- at least three repetitions are recorded;
- compatibility claims include exact configuration and limitations;
- one deliberate regression is caught automatically;
- one independent developer reproduces the hero benchmark.

## Current limitation

The current development line provides machine-readable invariant declarations, four narrow assurance guardians, the composed flagship recipe, deterministic invariant checks, structured severity-aware failures and critical pipeline gates. It does not yet provide general semantic extraction comparison, cloud providers, ABOMs, recipe locks, build digests, matrices or the evidence-to-evidence regression command described above.

Those capabilities are delivered incrementally through the published roadmap.
