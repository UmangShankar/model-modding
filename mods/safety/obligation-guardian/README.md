# Obligation Guardian

Obligation Guardian is a narrow assurance mod for preserving who must, may or must not act.

## Purpose

It protects named parties, required actions, permissions and prohibitions. It prevents a transformation from weakening a duty, strengthening a permission or assigning an action to the wrong party.

## Use it when

- a source uses `must`, `shall`, `may`, `must not` or equivalent language;
- more than one party appears;
- the difference between a duty, permission and prohibition matters;
- changing the actor or modality could alter compliance or entitlement.

## Limitations

This mod supplies behavioural instructions and declared invariants. The current evaluator does not yet perform full semantic actor-action comparison. Deterministic cases and human review remain necessary.

It does not own deadlines, exceptions or source-grounding concerns except where they qualify an obligation.
