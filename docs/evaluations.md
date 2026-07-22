# Evaluations

Evaluation cases live under each mod's `evaluations/` directory. They can contain:

- an input prompt;
- expected behaviours for human review;
- failure indicators;
- transparent deterministic checks;
- invariant checks tied to manifest-declared preservation or prohibition requirements;
- optional classified-fixture metadata for adversarial and paraphrase coverage.

## Inspect an evaluation plan

```bash
modding evaluate trusted-document-explainer \
  --model llama3.2 \
  --dry-run
```

The dry run lists every case and shows its invariant target, kind and severity. Legacy cases without invariant targets continue to run as legacy deterministic checks.

## Flagship fixture coverage

The Trusted Document Explainer plan contains exactly 40 cases. Eighteen are classified adversarial or paraphrase fixtures distributed across the four assurance guardians.

A classified fixture declares:

```yaml
fixture_type: adversarial
attack_types: [unit-substitution, instruction-conflict]
```

The repository test suite validates the case count, guardian distribution, unique case identities, non-empty attack labels, controlled taxonomy and invariant-aware checks. See [Adversarial and paraphrase fixtures](adversarial-fixtures.md) for the complete taxonomy and authoring rules.

## Run with a critical-failure gate

```bash
modding evaluate trusted-document-explainer \
  --model llama3.2 \
  --fail-on critical
```

`critical` is the default. The command returns exit code `1` when the modded response has a deterministic invariant failure at or above the selected threshold.

Supported thresholds are:

- `critical`: block only critical invariant failures;
- `major`: block critical and major failures;
- `minor`: block any declared invariant failure;
- `none`: record failures without returning a failing exit code.

Use `--fail-on none` only for exploratory evidence collection. It must not be used to present a failing result as passing assurance evidence.

## Invariant check shape

An evaluation case may include:

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

The evaluator validates that:

1. `kind` is `preserve` or `prohibit`;
2. the invariant is declared by that mod's manifest;
3. the case severity exactly matches the manifest severity;
4. at least one supported deterministic check is supplied.

A malformed or undeclared target stops the evaluation plan before a model is called.

## Report contract

Reports are written under `build/evaluations/<recipe>/` as JSON and Markdown.

Evaluator v2 uses report schema `0.2` and records:

- evaluator name and version;
- complete stock and modded responses;
- legacy per-check results;
- invariant-check results;
- structured invariant failures;
- critical, major and minor totals for stock and modded runs;
- per-mod severity summaries;
- improvements and regressions;
- the configured failure threshold;
- pipeline status and blocking failures;
- latency and response-length evidence.

Each structured failure identifies the mod, case, invariant kind, invariant type, severity, description and exact deterministic checks that failed.

Multi-model benchmarks use the same evaluator function and include invariant-failure counts, preventing evaluation and benchmark scoring from diverging.

## Authority and limitations

Deterministic invariant checks are authoritative for the exact assertions they encode. An exact critical failure cannot be overridden by an aggregate score.

They do not yet perform general semantic extraction or prove that every material fact was preserved. Keyword, phrase, question-count and length checks can miss paraphrases or subtle meaning changes. Review full responses and the human rubric before making compatibility, legal, medical, financial or safety claims.

Structured source-output comparison and optional model-assisted judgement remain separate later increments. A model judge will never be the sole gate and will not override an exact deterministic critical failure.
