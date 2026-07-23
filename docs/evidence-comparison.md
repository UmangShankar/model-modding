# Evidence comparison and compatibility matrices

Model Modding compares durable, verified evidence rather than comparing unbound scores or copied model responses.

## Compare a baseline and candidate

```bash
modding compare-evidence \
  evidence/baseline \
  evidence/candidate \
  --fail-on critical \
  --output build/comparisons/current
```

The command writes:

```text
comparison.json
comparison.md
```

Exit codes are deliberately distinct:

- `0` — comparable evidence with no new or escalated failure at the configured threshold;
- `1` — comparable evidence with a blocking regression;
- `2` — invalid input or evidence that is not comparable under the strict contract.

Supported thresholds are `critical`, `major`, `minor` and `none`.

## Verification before interpretation

Both bundles must pass `modding verify-evidence` before comparison. A tampered response, invalid manifest, broken build identity or unmanaged artifact stops the operation before behavioural deltas are calculated.

## Strict comparability contract

Regression comparison requires exact agreement on:

- bundle type;
- recipe name and version;
- source digest;
- build digest;
- fixture-set digest;
- evaluator contract;
- provider/model target set.

A mismatch produces `not_comparable`. The engine does not pretend that results from different builds, fixtures or evaluator versions are a meaningful regression sequence.

Runtime metadata is compared and reported. Changes in requested options or other runtime details do not by themselves invalidate evidence when the provider/model target set and the strict identity fields still match.

## Failure identity and deltas

Failures use the evaluator's stable failure ID. When a legacy failure has no ID, the engine constructs a deterministic identity from its mod, case, layer, kind, invariant, source-fact ID and description.

The report separates:

- new failures;
- resolved failures;
- unchanged failures;
- severity changes;
- severity escalations.

Only modded failures participate in the regression gate. Stock deltas remain available in the original evidence bundle as context.

A new failure blocks when its severity reaches `--fail-on`. An existing failure also blocks when its candidate severity increases to the configured threshold. For example, a major baseline failure becoming critical is a critical regression even though the failure ID already existed.

## Deterministic comparison identity

`comparison.json` uses schema `0.1` and includes a `comparison_digest`. The digest covers the canonical comparison report apart from the digest field itself.

Canonical output uses UTF-8, sorted JSON keys, no insignificant whitespace and a trailing LF. The Markdown report presents the same comparability checks, pipeline status and target-level deltas.

## Build a compatibility matrix

```bash
modding matrix-evidence \
  evidence/ollama \
  evidence/anthropic \
  evidence/openai \
  --output build/matrices/trusted-document-explainer
```

The command writes:

```text
matrix.json
matrix.md
```

Every input bundle is verified. Matrix inputs must share the same:

- recipe and build identity;
- fixture-set digest;
- evaluator contract.

Each provider/model target must be unique within one matrix.

## Matrix meaning

The matrix aggregates the modded result of every encoded invariant check and structured source comparison by:

- provider;
- exact model;
- invariant kind;
- invariant name;
- severity.

A cell reports how many observations were tested, passed and failed. `passed` means no encoded observation for that invariant failed for that target.

It does not mean:

- the provider or model is universally compatible;
- every semantic failure was detected;
- the model is safe for all documents;
- one target is generally better than another.

A defensible compatibility statement remains narrow:

> This provider and model passed this locked recipe build on this fixture set under this evaluator and recorded configuration.

## Versioned schemas

The output formats are defined by:

- `schemas/evidence-comparison.schema.json`;
- `schemas/compatibility-matrix.schema.json`.

Generated reports are validated before writing.

## CI use

A repository can check in or retrieve a reviewed baseline bundle and compare a candidate bundle with:

```bash
modding compare-evidence \
  evidence/baseline \
  evidence/candidate \
  --fail-on critical
```

The process requires no provider call. Pull-request CI can therefore block a deliberate or accidental new critical failure using already-created evidence.

Protected cloud execution, automatic PR comments and publication of reviewed three-provider evidence remain separate operational work.
