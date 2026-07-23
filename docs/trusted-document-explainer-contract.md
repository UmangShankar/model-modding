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

The implemented machine-readable invariant declarations include:

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

The declarations are schema-validated and inspectable. They can be bound both to deterministic invariant checks and to typed source facts that compare canonical source values, required context and prohibited output forms.

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

Trusted Document Explainer `0.2.0` separates one transformation mod from four narrow assurance guardians.

Transformation:

- `plain-language-explainer`

Assurance:

- `deadline-guardian`
- `obligation-guardian`
- `exception-guardian`
- `source-grounding-guardian`

Each guardian has one narrow responsibility, focused instructions, machine-readable invariant declarations, examples, limitations and independent baseline, adversarial and paraphrase evaluation coverage.

The combined flagship evaluation plan contains exactly 40 cases. Eighteen are classified adversarial or paraphrase fixtures: five for Deadline Guardian, five for Obligation Guardian, four for Exception Guardian and four for Source Grounding Guardian.

Sixteen representative guardian cases declare 23 typed source facts. These compare source values with accepted output forms, bind facts to actors, triggers or qualifications where required, and detect explicitly prohibited transformations.

This composition makes the behavioural contract inspectable and deterministically testable for its encoded assertions. The current evaluator does not provide unrestricted semantic extraction or guarantee detection of every paraphrased meaning change.

## Reproducible build contract

The implemented command is:

```text
modding build trusted-document-explainer
```

It produces:

```text
build/trusted-document-explainer/
├── system.md
├── recipe.lock.json
├── abom.json
├── abom.md
└── manifest.json
```

The bundle must be deterministic for identical canonical inputs and must contain no timestamps, absolute checkout paths, usernames or machine identifiers.

Canonicalisation defines:

- UTF-8 source and output encoding;
- LF line endings for text hashing and generated text;
- stable JSON key ordering with no insignificant whitespace;
- repository-relative POSIX paths;
- recipe composition order;
- SHA-256 file, component, source, prompt, artifact and build digests;
- versioned recipe-lock, ABOM and build-manifest schemas;
- an independently versioned build engine.

The initial build engine identity is `model-modding 0.1.0`.

## Recipe lock contract

`recipe.lock.json` must identify:

- build engine and format versions;
- recipe identity, version, licence, configuration and manifest hash;
- each ordered mod reference, name, version, role, status and licence;
- each mod manifest and instruction-file path, byte count and SHA-256;
- capabilities, dependencies, conflicts and compatible-model declarations;
- preserved invariants and prohibited transformations;
- component digests;
- source digest;
- compiled system-prompt digest;
- complete canonical inputs used to compute the build digest;
- build digest.

Provider, model and generation settings are intentionally excluded. They vary between executions of the same locked build and belong in execution evidence.

## ABOM contract

The Agent Behaviour Bill of Materials is emitted as `abom.json` and `abom.md`.

It identifies the build engine, recipe, ordered components, roles, licences, declared safeguards, source digest, compiled-prompt digest and build digest. It also states its limitations.

An ABOM is a deterministic build inventory. It does not prove that a provider or model complied with the instructions and must not list a provider as tested unless reviewed execution evidence supports that claim.

## Offline verification

The implemented command is:

```text
modding verify-build trusted-document-explainer
```

Verification reconstructs the expected bundle from the current source tree without a model API call and compares every managed artifact byte-for-byte.

It must fail when:

- a source manifest or instruction changes;
- the build engine or schema-version contract changes;
- a generated artifact is edited or missing;
- an unmanaged path appears in the build directory;
- a generated JSON payload violates its versioned schema.

Equivalent LF and CRLF checkouts must produce the same identity. Any other behavioural source-byte change must invalidate the lock and build.

## Portability target

The same locked recipe build must run through:

- Ollama;
- Anthropic;
- OpenAI.

No mod file may be changed between providers.

Adapter availability alone does not establish compatibility. Every reviewed result must identify the provider, exact returned model, supplied and effective generation settings, build digest, evaluator version and fixture set.

## Evaluation authority

Quality gates are ordered as follows:

1. deterministic invariant checks;
2. structured source-output comparison;
3. optional model-assisted judgement;
4. recorded human review.

Evaluator `0.3.0` implements the first two layers. Guardian cases target manifest-declared invariants, require matching severities and produce structured critical, major and minor failures. Typed source facts must be present in the case input, preventing fixtures from inventing their own ground truth.

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

Provider-aware reports use schema `0.4` and include runtime and per-response provider, model, requested/effective settings, usage and finish metadata alongside evaluator results.

## Evidence requirements

Every release result must identify:

- recipe ID and version;
- recipe lock and build digest;
- build engine and ABOM;
- installed mods and versions;
- declared invariants;
- provider and exact model;
- generation configuration;
- evaluator version;
- case and source-fact counts;
- critical, major and minor failures;
- evidence-bundle location;
- source-control commit and dirty-tree status;
- known limitations.

Sensitive source documents must not be copied into evidence by default.

## Comparison and regression target

The remaining v0.1.7 scope must add:

- durable run evidence bundles linked to a build digest;
- compatibility matrices by invariant;
- baseline-versus-candidate comparison;
- automatic failure for new critical regressions;
- protected, allowlisted and cost-limited cloud workflows;
- concise pull-request summaries.

A comparison may state:

> This provider and model passed this locked recipe build on this fixture set under this configuration.

It must not state that one provider is universally best.

## Release acceptance

The v0.2.0 proof is complete only when:

- the same locked flagship build runs across all three providers;
- at least 40 cases are included;
- zero critical failures remain in the release candidate evidence;
- at least three repetitions are recorded;
- compatibility claims include exact configuration and limitations;
- one deliberate regression is caught automatically;
- one independent developer reproduces the hero benchmark.

The case-count criterion and reproducible-build foundation are complete. They do not count as full release acceptance until the provider, repetition, evidence-comparison and independent-reproduction criteria are satisfied.

## Current limitation

The current development line provides machine-readable invariant declarations, four narrow assurance guardians, the composed flagship recipe, the 40-case classified fixture set, deterministic invariant checks, 23 typed source facts, structured source-output comparison, severity-aware gates, Ollama/Anthropic/OpenAI adapters, provider execution metadata, deterministic recipe locks, build digests and JSON/Markdown ABOMs.

It does not provide unrestricted semantic extraction, durable run evidence bundles, compatibility matrices, evidence-to-evidence regression commands or reviewed three-provider portability evidence. Those capabilities remain the v0.1.7 programme.
