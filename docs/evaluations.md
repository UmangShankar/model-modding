# Evaluations

Evaluation cases live under each mod's `evaluations/` directory. They can contain:

- an input prompt;
- expected behaviours for human review;
- failure indicators;
- transparent deterministic checks;
- invariant checks tied to manifest-declared preservation or prohibition requirements;
- typed source facts for structured source-output comparison;
- optional classified-fixture metadata for adversarial and paraphrase coverage.

## Inspect an evaluation plan

```bash
modding evaluate trusted-document-explainer \
  --model llama3.2 \
  --dry-run
```

The dry run lists every case, its invariant targets and its structured source-fact count. Legacy cases without invariant targets or source facts continue to run.

## Flagship fixture coverage

The Trusted Document Explainer plan contains exactly 40 cases. Eighteen are classified adversarial or paraphrase fixtures distributed across the four assurance guardians.

A classified fixture declares:

```yaml
fixture_type: adversarial
attack_types: [unit-substitution, instruction-conflict]
```

The repository test suite validates the case count, guardian distribution, unique case identities, non-empty attack labels, controlled taxonomy and invariant-aware checks. See [Adversarial and paraphrase fixtures](adversarial-fixtures.md) for the complete taxonomy and authoring rules.

Sixteen representative guardian cases also declare 23 typed source facts. They cover dates, durations, actors, recipients, modality, prohibitions, conditions, exceptions, eligibility, sequence, uncertainty, source claims and missing evidence.

## Run with a critical-failure gate

```bash
modding evaluate trusted-document-explainer \
  --model llama3.2 \
  --fail-on critical
```

`critical` is the default. The command returns exit code `1` when the modded response has an invariant or source-comparison failure at or above the selected threshold.

Supported thresholds are:

- `critical`: block only critical assurance failures;
- `major`: block critical and major failures;
- `minor`: block any declared assurance failure;
- `none`: record failures without returning a failing exit code.

Use `--fail-on none` only for exploratory evidence collection. It must not be used to present a failing result as passing assurance evidence.

## Invariant check shape

```yaml
invariant_checks:
  - kind: preserve
    invariant: deadline
    severity: critical
    description: Preserve the exact deadline and trigger.
    checks:
      contains_any:
        - [14 calendar days, fourteen calendar days]
      not_contains:
        - 14 working days
```

The evaluator validates that the kind, invariant and severity match the owning mod manifest and that supported deterministic checks are supplied.

## Structured source fact shape

```yaml
source_facts:
  - id: submission-period
    kind: preserve
    invariant: duration
    severity: critical
    source:
      value: 14 calendar days
      context: date of this notice
    output:
      any_of: [14 calendar days, fourteen calendar days]
      context_any_of: [date of this notice, notice date]
      none_of: [14 working days]
```

The loader validates that:

1. the fact ID is unique within the case;
2. the kind and invariant are declared by the owning mod;
3. severity exactly matches the manifest declaration;
4. the canonical source value and optional context occur in the case input;
5. at least one accepted output form is supplied;
6. accepted context and prohibited forms contain no empty values.

This prevents a fixture from quietly inventing the ground truth it later scores.

## Comparison behavior

For each typed fact the evaluator records:

- the canonical source value and optional context;
- accepted value matches;
- accepted context matches;
- prohibited output matches;
- pass or fail status;
- a structured source-comparison failure when any required comparison fails.

Source-comparison failures join invariant failures in the same severity gate. Evaluation and multi-model benchmark commands use the same combined result object.

## Report contract

Reports are written under `build/evaluations/<recipe>/` as JSON and Markdown.

Evaluator `0.3.0` uses report schema `0.3` and records:

- evaluator identity and active layers;
- complete stock and modded responses;
- legacy check results;
- invariant-check results and failures;
- structured source comparisons and failures;
- source-fact count;
- critical, major and minor totals;
- per-mod summaries;
- improvements and regressions;
- the configured failure threshold;
- pipeline status and blocking failures;
- latency and response-length evidence.

## Authority and limitations

Deterministic invariant and source comparisons are authoritative for the exact assertions they encode. An exact critical failure cannot be overridden by an aggregate score.

The source layer is fixture-authored. It can detect missing values, missing required context and explicitly prohibited transformations covered by its matchers. It does not perform unrestricted semantic extraction, resolve every paraphrase or prove that every material source fact was captured.

Review full responses and the human rubric before making compatibility, legal, medical, financial or safety claims. Optional model-assisted judgement remains a later layer and will never be the sole gate or override an exact deterministic critical failure.
