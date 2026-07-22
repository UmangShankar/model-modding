# Invariant declarations

Invariant declarations make a mod's preservation promises and prohibited transformations machine-readable.

They describe requirements. They do not prove that a model will satisfy those requirements. Enforcement is added through invariant-aware evaluation and regression tooling in later v0.1.2 and v0.1.7 increments.

The authoritative contract is [`schemas/invariant.schema.json`](../schemas/invariant.schema.json). Mod manifests reference that versioned schema through [`schemas/mod.schema.json`](../schemas/mod.schema.json).

## Semantic role

A mod may declare one of two roles:

```yaml
role: transformation
```

- `transformation`: primarily changes, rewrites or structures behaviour or content;
- `assurance`: primarily protects a declared safeguard or detects a prohibited transformation.

The field is optional during the v0.1-to-v0.2 migration period. Existing manifests without a role remain valid.

## Declaration shape

```yaml
role: transformation

invariants:
  preserve:
    - type: deadline
      severity: critical
    - type: obligation
      severity: critical
    - type: condition
      severity: major
    - type: exception
      severity: critical

  prohibit:
    - type: invented_deadline
      severity: critical
    - type: weakened_obligation
      severity: critical
    - type: removed_exception
      severity: critical
    - type: unsupported_advice
      severity: major
```

An `invariants` object must contain at least one non-empty `preserve` or `prohibit` list. Empty declarations are rejected because they create the appearance of assurance without stating a requirement.

## Preserved invariant vocabulary

The initial reference vocabulary is intentionally small:

| Type | Meaning |
| --- | --- |
| `deadline` | An exact deadline and, where applicable, its trigger. |
| `date` | A stated calendar date. |
| `duration` | A period and its unit, such as calendar or working days. |
| `amount` | A monetary or other exact amount. |
| `percentage` | A stated percentage or rate. |
| `named_party` | The person or organisation to which a statement applies. |
| `obligation` | A required action and its modality. |
| `prohibition` | An action that is forbidden or disallowed. |
| `condition` | A prerequisite, trigger or qualifying condition. |
| `exception` | A qualification or case where the general rule does not apply. |
| `eligibility_rule` | A rule determining who or what qualifies. |
| `sequence` | The required order of actions or events. |
| `source_claim` | A claim explicitly supported by the supplied source. |
| `uncertainty` | Expressed uncertainty, discretion or lack of conclusion. |

Unknown terms fail schema validation. New terms must be added deliberately through a schema change rather than appearing ad hoc in individual mods.

## Prohibited transformation vocabulary

The first prohibited-transformation vocabulary contains:

| Type | Meaning |
| --- | --- |
| `invented_deadline` | Adding a deadline not supported by the source. |
| `weakened_obligation` | Turning a required action into an optional or weaker one. |
| `removed_exception` | Omitting a material exception or qualification. |
| `unsupported_advice` | Adding advice or next steps not supported by the source or package contract. |

This list will expand only when a term has a precise definition and an evaluation strategy.

## Severity

Every entry requires one of three severities:

- `critical`: material meaning or safety failure that must fail the pipeline;
- `major`: important failure requiring review or threshold handling;
- `minor`: lower-impact issue that should be recorded but may not block delivery.

A future aggregate score cannot override an exact critical failure.

## Inspection

Run:

```bash
modding inspect plain-language-explainer
```

or:

```bash
modding inspect plain-language-explainer --json
```

Inspection reports the mod's role, preserved invariants and prohibited transformations. Legacy mods without declarations are shown as `not declared` and `none declared` rather than being assigned inferred promises.

## Migration rules

During the transition period:

1. existing v0.1 manifests without `role` or `invariants` remain schema-valid;
2. newly scaffolded mods declare `role: transformation` by default;
3. contributors add an `invariants` block only for explicit, documented promises;
4. assurance mods should use `role: assurance`;
5. declarations must match instructions, examples, evaluation cases and documented limitations;
6. a declaration must not be treated as evidence that the current evaluator enforces it.

## Current implementation boundary

The repository can now validate and inspect invariant declarations. It does not yet perform semantic extraction, severity-aware scoring or automatic critical-failure enforcement. Those are separate delivery increments so that attractive scores are not produced before the evaluator can detect material meaning changes.
