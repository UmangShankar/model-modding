# Trusted Document Explainer product contract

## Status

This document defines the target reference product for Model Modding v0.2.0. It is a product and engineering contract, not a claim that the current development line already satisfies every evidence requirement.

## Purpose

> Rewrite complex official or high-stakes text in plain English while preserving operationally or legally material meaning.

## Intended users

The reference package is intended for people who need to understand notices, policies, clauses, letters or other high-stakes text without losing what must happen, who must act, when action is required and which qualifications apply.

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

- deadlines, dates and durations;
- amounts and percentages;
- named parties, obligations and prohibitions;
- conditions, exceptions and eligibility rules;
- sequence;
- source claims and uncertainty.

The declarations are schema-validated and inspectable. They bind to deterministic invariant checks and to 23 typed source facts that compare canonical source values, required context and prohibited output forms.

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

The combined flagship evaluation plan contains exactly 40 cases. Eighteen are classified adversarial or paraphrase fixtures. Sixteen representative guardian cases declare 23 typed source facts.

This composition is inspectable and deterministically testable for its encoded assertions. The current evaluator does not provide unrestricted semantic extraction or guarantee detection of every paraphrased meaning change.

## Reproducible build contract

```text
modding build trusted-document-explainer
```

The build produces:

```text
build/trusted-document-explainer/
├── system.md
├── recipe.lock.json
├── abom.json
├── abom.md
└── manifest.json
```

The bundle must be deterministic for identical canonical inputs and contain no timestamps, absolute checkout paths, usernames or machine identifiers.

Canonicalisation defines UTF-8, LF line endings, stable JSON, repository-relative POSIX paths, recipe composition order and SHA-256 file, component, source, prompt, artifact and build digests. The initial build engine identity is `model-modding 0.1.0`.

## Recipe lock and ABOM contract

`recipe.lock.json` identifies the build engine and format versions, exact recipe and ordered components, manifests and instruction files, roles, licences, dependencies, conflicts, compatibility declarations, invariants, source digest, compiled-prompt digest, digest inputs and build digest.

Provider, model and generation settings are excluded because they belong to execution evidence.

The Agent Behaviour Bill of Materials is emitted as `abom.json` and `abom.md`. An ABOM is a deterministic build inventory. It does not prove that a provider or model complied with the instructions.

## Offline build verification

```text
modding verify-build trusted-document-explainer
```

Verification reconstructs the expected bundle without a provider call and fails when behavioural sources or schemas change, a generated artifact is edited or missing, an unmanaged path appears or generated JSON is invalid.

## Portability target

The same locked recipe build must run through Ollama, Anthropic and OpenAI without changing mod files.

Adapter availability alone does not establish compatibility. Every reviewed result must identify the provider, exact returned model, supplied and effective generation settings, build digest, evaluator version and fixture set.

## Evaluation authority

Quality gates are ordered as follows:

1. deterministic invariant checks;
2. structured source-output comparison;
3. optional model-assisted judgement;
4. recorded human review.

Evaluator `0.3.0` implements the first two layers. A model judge must never be the sole gate and cannot override an exact deterministic critical failure.

## Severity model

- **Critical** — material meaning changed, invented or removed in a way that could alter action, entitlement, safety or compliance.
- **Major** — important clarity, grounding or qualification failure requiring review.
- **Minor** — presentation or readability weakness with no material meaning change.

A new critical failure must fail the configured evaluation gate regardless of aggregate score.

## Durable evidence contract

Provider-aware `run`, `evaluate` and `benchmark` may emit a versioned evidence bundle through `--evidence`.

An evaluation bundle contains:

```text
manifest.json
responses.jsonl
recipe.lock.json
abom.json
evaluation.json
```

The bundle must embed the exact build identity, preserve exact raw responses and execution metadata, record prompt hashes without copying prompt text by default, keep interpreted evaluation separate, record provider/model/settings/evaluator/fixtures/source control and include independently verifiable hashes and limitations.

Raw execution evidence must remain immutable when an evaluator is rerun.

## Offline evidence verification

```text
modding verify-evidence build/evidence/trusted-document-explainer
```

It verifies manifest validity, evidence-digest reconstruction, artifact hashes and sizes, response hashes, prompt privacy, recipe-lock validity, manifest/lock/ABOM agreement and missing or unmanaged artifacts.

A valid evidence bundle proves internal integrity. It does not prove that the response is correct, that every material failure was detected or that a provider is universally compatible.

## Evidence comparison contract

```text
modding compare-evidence evidence/baseline evidence/candidate --fail-on critical
```

Both bundles must pass offline evidence verification first. Regression comparison requires exact agreement on bundle type, recipe name/version, source/build digests, fixture-set digest, evaluator contract and provider/model target set.

A mismatch must produce `not_comparable`. It must not be converted into a pass, failure delta or aggregate score.

Comparable reports distinguish new, resolved and unchanged failures, severity changes, severity escalations and runtime changes. A new or escalated modded failure at the configured threshold must block. Output is deterministic JSON and Markdown with a canonical comparison digest.

## Compatibility matrix contract

```text
modding matrix-evidence evidence/ollama evidence/anthropic evidence/openai
```

Every input must be verified and share the same recipe/build identity, fixture-set digest and evaluator contract.

The matrix aggregates modded invariant checks and structured source comparisons by exact provider, exact model, invariant kind, invariant and severity. A passed cell applies only to that locked build, fixture set, evaluator and recorded execution context. It is not a universal provider ranking, certification or proof that every semantic failure was detected.

## Repeated evidence contract

```text
modding aggregate-evidence evidence/run-1 evidence/run-2 evidence/run-3 \
  --minimum-repetitions 3 \
  --require-zero-critical \
  --output build/aggregate
```

All bundles must share exact recipe, build, fixture and evaluator identities. The aggregate records repetitions, minimum cases, run outcomes, evidence digests, failure totals and per-invariant observations for every exact target.

Repeated passing runs remain contextual evidence and do not prove universal compatibility.

## Reviewed baseline contract

```text
modding activate-baseline evidence/candidate evidence/baselines/current \
  --reviewer "Reviewer or group" \
  --scope "Exact comparison scope"
```

Activation requires a verified evidence bundle and emits a canonical `baseline.json` plus the embedded evidence. Baseline approval is scoped. It does not establish compatibility outside the exact build, fixtures, evaluator and target.

## Protected execution contract

Real cloud runs use a manual protected workflow with environment approval, provider secrets, exact model allowlists, one to three repetitions, capped output tokens, all 40 cases and durable uploaded evidence.

Ollama release evidence uses an allowlisted self-hosted runner. Untrusted pull requests never receive cloud credentials and do not trigger paid provider execution.

Synthetic pull-request evidence exercises pipeline mechanics only and must be labelled as synthetic. It cannot be copied into reviewed release evidence or used for provider claims.

## Release readiness contract

```text
modding release-check \
  --aggregate build/release-candidate/aggregate/aggregate.json \
  --matrix build/release-candidate/matrix/matrix.json \
  --minimum-repetitions 3 \
  --minimum-cases 40 \
  --output build/release-candidate/readiness
```

The v0.2 gate requires:

- matching recipe, build, fixture-set and evaluator identities;
- Ollama, Anthropic and OpenAI coverage;
- at least three repetitions for every exact release target;
- all 40 cases in every repetition;
- zero critical failures;
- passing compatibility-matrix target status.

A `v0.2*` tag must not publish unless checked-in reviewed evidence satisfies this gate and the package version matches the tag.

## Evidence requirements

Every release result must identify recipe/build/lock/ABOM identity, installed mods and invariants, provider and exact model, requested and effective settings, evaluator and fixtures, case/source-fact counts, failures, evidence/aggregate/matrix/readiness digests, source-control state, privacy behaviour and limitations.

A narrow compatibility statement may state:

> This provider and model passed this locked recipe build on this fixture set under this evaluator and recorded configuration.

It must not state that one provider is universally best.

## Release acceptance

The v0.2.0 proof is complete only when:

- the same locked flagship build runs across all three providers;
- at least 40 cases are included in every release run;
- zero critical failures remain in reviewed release-candidate evidence;
- at least three repetitions are recorded per exact target;
- compatibility claims include exact configuration and limitations;
- one deliberate regression is caught automatically;
- a public case study includes failures and limitations;
- one independent developer reproduces the hero benchmark.

The engineering pipeline enforces these conditions but does not pretend that paid runs, human review or independent reproduction have already occurred.

## Current limitation

The current development line provides machine-readable invariant declarations, four narrow assurance guardians, the 40-case classified fixture set, deterministic invariant checks, 23 typed source facts, structured source-output comparison, severity-aware gates, Ollama/Anthropic/OpenAI adapters, provider execution metadata, deterministic builds, recipe locks, JSON/Markdown ABOMs, durable evidence, strict comparison, compatibility matrices, repeated-run aggregation, reviewed-baseline activation, automatic synthetic PR summaries, protected provider workflows and v0.2 release gates.

It does not provide unrestricted semantic extraction or reviewed three-provider portability evidence by itself. Real provider credentials, reviewed executions, baseline approval, the public case study and independent reproduction remain evidence operations.
