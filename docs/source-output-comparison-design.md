# Structured source-output comparison design

This delivery note defines the narrow second evaluator layer implemented for the Trusted Document Explainer.

## Goal

Compare typed facts from a supplied source with the model output using transparent deterministic matchers.

The comparison layer supplements invariant checks. It does not perform open-ended semantic extraction, use a model judge or infer facts that are absent from a fixture.

## Source fact contract

A case may declare `source_facts`:

```yaml
source_facts:
  - id: submission-period
    invariant: duration
    severity: critical
    source:
      value: 14 calendar days
      context: after the date of the notice
    output:
      any_of:
        - 14 calendar days
        - fourteen calendar days
      context_any_of:
        - date of the notice
        - notice date
      none_of:
        - 14 working days
```

Every source fact requires:

- a case-unique `id`;
- a manifest-declared preserved invariant;
- the same severity as the owning mod declaration;
- a canonical source `value`;
- at least one accepted output form.

Optional context matchers bind a value to its trigger, actor, recipient, condition or qualification. Optional prohibited forms identify known materially wrong transformations.

## Comparison outcomes

For each fact the evaluator records:

- whether an accepted value was found;
- whether required context was found;
- whether a prohibited form appeared;
- the canonical source value;
- the accepted and prohibited forms used for comparison;
- a structured failure when the comparison fails.

Failures join invariant-check failures in the severity gate. A critical source-comparison failure therefore returns a non-zero evaluation exit code under the default threshold.

## Limits

This layer is deterministic and fixture-authored. It can detect missing or explicitly incorrect values covered by the matchers. It cannot prove that every source fact was captured, resolve unrestricted paraphrases or determine legal meaning without an authored comparison contract.
