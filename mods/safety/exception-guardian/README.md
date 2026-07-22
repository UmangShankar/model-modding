# Exception Guardian

Exception Guardian is a narrow assurance mod for preserving qualifications that determine when a general rule applies.

## Purpose

It protects conditions, exceptions, eligibility rules and required sequence. It prevents a transformation from turning a qualified or discretionary rule into an unconditional statement.

## Use it when

- the source uses `if`, `unless`, `except`, `where`, `provided that` or similar wording;
- eligibility depends on several criteria;
- a later step is allowed only after an earlier step;
- removing one qualification could change entitlement, duty or action.

## Limitations

This mod supplies behavioural instructions and declared invariants. The current evaluator does not yet perform complete logical comparison of rule structures. Deterministic cases and human review remain necessary.

It does not own deadlines, actor assignment or source-grounding concerns except where they are part of a condition or exception.
