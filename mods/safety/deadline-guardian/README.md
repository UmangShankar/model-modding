# Deadline Guardian

Deadline Guardian is a narrow assurance mod for transformations involving official, contractual or other high-stakes text.

## Purpose

It protects exact dates, deadlines, durations, units and triggering events. It also prevents a transformation from adding a time limit that the supplied source does not contain.

## Use it when

- a source contains an exact date or time;
- a deadline runs from a named trigger;
- calendar days, working days or another unit matters;
- omission or invention of a deadline could change required action.

## Limitations

This mod supplies behavioural instructions and declared invariants. The current evaluator does not yet semantically prove that every time constraint was preserved. Deterministic cases and human review remain necessary.

It does not own obligations, conditions, exceptions or source-grounding concerns except where they are needed to identify the deadline trigger.
