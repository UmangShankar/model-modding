# Invariant declarations

Invariant declarations make a mod's preservation promises and prohibited transformations machine-readable.

They describe requirements. They do not prove that a model will satisfy those requirements. Evaluator v2 can now bind explicit deterministic checks to declarations, record severity-aware failures and block configured thresholds. General semantic comparison remains a later increment.

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

The controlled prohibited-transformation vocabulary contains:

| Type | Meaning |
| --- | --- |
| `invented_deadline` | Adding a deadline not supported by the source. |
| `weakened_obligation` | Turning a required action into an optional or weaker one. |
| `removed_exception` | Omitting a material exception or qualification. |
| `unsupported_advice` | Adding advice or next steps not supported by the source or package contract. |
| `invented_source_claim` | Presenting a claim as source-supported when it does not appear in the supplied material. |
| `fabricated_citation` | Inventing a citation, study, author, quotation, URL or publication detail. |
| `presented_missing_evidence` | Treating a missing section, attachment or fact as though it had been supplied. |

The three source-grounding terms were added with the Source Grounding Guardian because each has a precise failure definition and focused evaluation cases. Future terms require the same level of definition and evidence strategy.

## Severity

Every entry requires one of three severities:

- `critical`: material meaning or safety failure that must fail the pipeline;
- `major`: important failure requiring review or threshold handling;
- `minor`: lower-impact issue that should be recorded but may not block delivery.

Evaluator v2 records all three severities and defaults to failing the command on critical modded failures. `--fail-on major`, `--fail-on minor` and `--fail-on none` allow stricter gates or non-blocking evidence collection. An aggregate score cannot override an exact deterministic critical failure.

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

## Assurance guardians

The flagship recipe now separates four non-overlapping assurance responsibilities:

- `deadline-guardian`: dates, deadlines, durations and invented time limits;
- `obligation-guardian`: named parties, duties, permissions and prohibitions;
- `exception-guardian`: conditions, exceptions, eligibility and sequence;
- `source-grounding-guardian`: source claims, uncertainty, missing evidence, citations and unsupported advice.

Each guardian has an independent manifest, instructions, examples, limitations and evaluation suite. Its cases now identify exact invariant targets and severities. Passing those checks is evidence for the encoded assertions, not proof of complete semantic correctness.

## Migration rules

During the transition period:

1. existing v0.1 manifests without `role` or `invariants` remain schema-valid;
2. newly scaffolded mods declare `role: transformation` by default;
3. contributors add an `invariants` block only for explicit, documented promises;
4. assurance mods should use `role: assurance`;
5. declarations must match instructions, examples, evaluation cases and documented limitations;
6. invariant-aware cases must target a declaration from the owning mod and use the same severity;
7. legacy cases without invariant targets remain supported but cannot create severity-aware failures.

## Current implementation boundary

The repository can validate and inspect invariant declarations, compose the four narrow assurance guardians, execute deterministic invariant checks, produce structured severity-aware failures and block critical regressions. It does not yet perform general semantic extraction, detect every paraphrased meaning change, use a model-assisted judge or compare evidence bundles across commits. Those remain separate increments.
