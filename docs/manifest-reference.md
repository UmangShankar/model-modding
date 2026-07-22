# Manifest reference

The authoritative contracts are:

- `schemas/mod.schema.json`;
- `schemas/invariant.schema.json`;
- `schemas/recipe.schema.json`.

This page is a readable guide; validation always follows the schemas.

## Mod manifest

Required fields are:

- `name`: lowercase kebab-case identifier;
- `version`: semantic version;
- `status`: maturity value allowed by the schema;
- `description`: concise purpose;
- `category`: one of personality, domain, workflow, tool, memory, safety, interface or experimental;
- `authors`: contributor records;
- `license`: licence identifier.

Optional fields include:

- `role`: `transformation` or `assurance`;
- `invariants`: machine-readable preservation promises and prohibited transformations;
- `compatible_models`: documented model families;
- `capabilities`: explicit behavioural or system capabilities;
- `dependencies`: required mod references;
- `conflicts`: incompatible mod references;
- `evaluation`: evaluation suites and the legacy minimum-score declaration.

Instruction Markdown lives beside the manifest under `instructions/`. Evaluations live under `evaluations/`.

### Invariant example

```yaml
role: assurance

invariants:
  preserve:
    - type: deadline
      severity: critical
    - type: exception
      severity: critical
  prohibit:
    - type: invented_deadline
      severity: critical
    - type: removed_exception
      severity: critical
```

Unknown invariant terms, unknown roles and severities outside `critical`, `major` and `minor` fail validation.

`role` and `invariants` remain optional during the migration period, so existing v0.1 manifests stay valid. See [Invariant declarations](invariants.md) for the complete vocabulary, severity definitions and migration rules.

## Recipe manifest

A recipe declares:

- `name` and `version`;
- `description`;
- ordered `mods` references;
- optional composition configuration;
- licence.

Run `modding validate` after every manifest change. Use `modding inspect <mod>` and `modding compose <recipe>` to verify how the declarations resolve in practice.
