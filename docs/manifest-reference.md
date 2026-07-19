# Manifest reference

The authoritative contracts are `schemas/mod.schema.json` and `schemas/recipe.schema.json`. This page is a readable guide; validation always follows the schemas.

## Mod manifest

Required fields include:

- `name`: lowercase kebab-case identifier;
- `version`: semantic version;
- `status`: maturity value allowed by the schema;
- `description`: concise purpose;
- `category`: one of personality, domain, workflow, tool, memory, safety, interface or experimental;
- `authors`: contributor records;
- `compatible_models`: documented model families;
- `capabilities`: explicit behavioural or system capabilities;
- `dependencies`: required mod references;
- `conflicts`: incompatible mod references;
- `license`: licence identifier.

Instruction Markdown lives beside the manifest under `instructions/`. Evaluations live under `evaluations/`.

## Recipe manifest

A recipe declares:

- `name` and `version`;
- `description`;
- ordered `mods` references;
- optional composition configuration;
- licence.

Run `modding validate` after every manifest change. Use `modding inspect <mod>` and `modding compose <recipe>` to verify how the declarations resolve in practice.
