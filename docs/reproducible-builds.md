# Reproducible builds, recipe locks and ABOMs

A Model Modding build turns a recipe and its ordered behavioural inputs into a deterministic, inspectable bundle without calling a model provider.

## Build a recipe

```bash
modding build trusted-document-explainer
```

The default destination is `build/trusted-document-explainer/`. A different empty or previously managed directory can be supplied:

```bash
modding build trusted-document-explainer --output /tmp/tde-build
```

The bundle contains:

- `system.md` — the exact compiled system prompt used by the runtime;
- `recipe.lock.json` — ordered source files, versions, canonical hashes and digest inputs;
- `abom.json` — the machine-readable Agent Behaviour Bill of Materials;
- `abom.md` — the human-readable ABOM;
- `manifest.json` — artifact hashes and bundle identity.

The builder refuses unmanaged files or directories in the destination. This prevents an apparently valid bundle from silently including unrelated material.

## Canonical source hashing

Source records use SHA-256. Repository-relative paths always use POSIX `/` separators.

Text is read as UTF-8 and line endings are normalised to LF before hashing. This means an LF checkout and a CRLF checkout produce the same digest. All other content changes—including a one-character behavioural instruction change—alter the relevant file hash, source digest and build digest.

The source digest covers:

- the recipe manifest file;
- each selected mod manifest file;
- every ordered Markdown instruction file;
- recipe identity, version, licence and configuration;
- component identity, version, role, status and licence;
- capabilities, dependencies, conflicts and compatibility declarations;
- preserved invariants and prohibited transformations;
- recipe composition order.

Evaluation fixtures are not runtime behavioural inputs and are not part of this build digest. They belong to execution and evaluation evidence.

## Build engine identity

Every lock, ABOM and build manifest records the build engine as `model-modding` with an independent semantic version. The initial engine contract is `0.1.0`.

The engine version is separate from the Python package release version. It changes when compilation or canonicalisation semantics change in a way that could affect build identity.

## Build digest

`recipe.lock.json` records a `digest_inputs` object containing:

- build-engine version;
- build-manifest schema version;
- recipe-lock schema version;
- ABOM schema version;
- source digest;
- compiled system-prompt digest.

The build digest is the SHA-256 hash of the canonical JSON encoding of that object. It can therefore be independently recomputed rather than trusted as an opaque value.

Canonical JSON uses:

- UTF-8;
- sorted keys;
- no insignificant whitespace;
- one trailing LF;
- Unicode characters without ASCII escaping.

No timestamps, absolute checkout paths, usernames or machine identifiers are included.

## Recipe lock

The recipe lock identifies exactly which behavioural inputs produced the compiled prompt. It also records the build engine and the complete digest-input object. Components remain in recipe order and include:

- canonical reference;
- name and version;
- semantic role and status;
- licence;
- manifest path, byte count and SHA-256;
- ordered instruction-file paths, byte counts and SHA-256 values;
- capabilities and compatible-model declarations;
- dependencies and conflicts;
- preserved invariants and prohibited transformations;
- component digest.

The lock does not include provider, model or generation settings. Those vary per execution and belong in evidence reports.

## Agent Behaviour Bill of Materials

The ABOM describes what behavioural material is packaged in the build. It includes the build-engine identity, recipe, ordered components, declared safeguards, source digest, build digest and compiled-prompt digest.

An ABOM does not prove model compliance. It is a build inventory, not evidence that a provider obeyed the instructions. Compatibility claims still require reviewed execution evidence tied to an exact provider, model, configuration, fixture set and evaluator version.

## Offline verification

Verify a bundle against the current repository sources:

```bash
modding verify-build trusted-document-explainer
```

For a custom build directory:

```bash
modding verify-build trusted-document-explainer \
  --build-directory /tmp/tde-build
```

Verification reconstructs the expected bundle without a provider call and compares every managed artifact byte-for-byte. It fails when:

- a source manifest or instruction changed;
- the build-engine or schema-version contract changed;
- a generated artifact was edited;
- an artifact is missing;
- an unmanaged artifact is present;
- the generated payload would violate its versioned schema.

## Versioned schemas

The formats are defined by:

- `schemas/recipe-lock.schema.json`;
- `schemas/abom.schema.json`;
- `schemas/build-manifest.schema.json`.

Generated JSON is validated before it is written. The build-engine and schema versions participate in the build digest, so a future compiler or incompatible format change cannot silently retain the same build identity.

## CI use

Pull-request CI builds and verifies the flagship recipe in both the editable development installation and a clean wheel installation. This gate requires no model process, network endpoint or cloud credential.

Evidence comparison, compatibility matrices and baseline-versus-candidate regression gates remain separate v0.1.7 work.
