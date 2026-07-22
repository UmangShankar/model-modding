# Adversarial and paraphrase fixtures

The Trusted Document Explainer fixture set includes baseline, adversarial and paraphrase cases.

The purpose of an adversarial fixture is not to trick a model with arbitrary wording. It is to test a specific high-risk way that material meaning can be changed, omitted or invented during a transformation.

## Current coverage

The flagship evaluation plan contains exactly 40 cases:

- 22 existing baseline and guardian cases;
- 18 classified adversarial or paraphrase cases;
- 5 new Deadline Guardian cases;
- 5 new Obligation Guardian cases;
- 4 new Exception Guardian cases;
- 4 new Source Grounding Guardian cases.

Every new fixture has at least one manifest-validated invariant check.

## Fixture metadata

Classified fixtures add two fields:

```yaml
fixture_type: adversarial
attack_types: [unit-substitution, instruction-conflict]
```

`fixture_type` is either:

- `adversarial`: the prompt pressures the transformation to change, omit or invent meaning;
- `paraphrase`: the source expresses a material rule in wording that is harder to preserve directly.

`attack_types` records the failure modes exercised by the case. A case may cover more than one attack type.

## Covered attack families

The current controlled test taxonomy covers:

- deadline and duration attacks: unit substitution, trigger shifts, fixed-deadline substitution, deadline invention and boundary omission;
- actor and modality attacks: role swaps, role collapse, passive voice, modality flips and prohibition reversal;
- condition and exception attacks: condition softening, exception erasure, eligibility inflation and sequence collapse;
- grounding attacks: fabrication pressure, citation invention, false premises, certainty inflation and missing evidence;
- cross-cutting attacks: instruction conflict, omission pressure and paraphrase variation.

The taxonomy is enforced by repository tests. New labels must be added deliberately to the allowed set rather than appearing as unreviewed free text.

## Authoring rules

A classified fixture must:

1. identify one primary high-risk behavior;
2. contain non-empty `expected_behaviours` and `failure_indicators`;
3. contain transparent deterministic checks;
4. contain at least one invariant check owned by the mod;
5. use the severity declared in the owning mod manifest;
6. use a unique case name within the recipe;
7. avoid requiring external network access or unpublished source material.

## Interpretation boundary

A larger fixture set improves coverage but does not make deterministic keyword checks equivalent to semantic proof. These cases are authoritative only for the assertions they encode.

Structured source-output comparison and model-assisted review remain later evaluator layers. Human review is still required before making broad legal, medical, safety or compatibility claims.
