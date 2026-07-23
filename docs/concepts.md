# Core concepts

Model Modding packages assistant behaviour as a versioned, inspectable and testable system contract.

## Mod

A **mod** is a versioned package that makes one defined behavioural change. A mod may provide a transformation capability, an assurance safeguard, workflow behaviour, tool guidance or another bounded concern.

A mod can include:

- instructions;
- examples;
- compatibility declarations;
- dependencies and conflicts;
- evaluation cases;
- documented limitations;
- a semantic role;
- machine-readable invariant declarations.

A mod can declare `role: transformation` when it primarily changes content or behaviour, or `role: assurance` when it primarily protects a safeguard or detects a prohibited transformation. The role remains optional for legacy v0.1 manifests.

## Recipe

A **recipe** selects mods and declares their composition order. Composition produces an inspectable behavioural contract rather than hiding system instructions inside application code.

A recipe is the stable build unit that can be locked, hashed, executed across providers and linked to evaluation evidence.

## Invariant

An **invariant** is a machine-readable preservation promise or prohibition that applies to a transformation.

Examples include:

- preserve an exact deadline;
- preserve the party responsible for an obligation;
- preserve a condition or exception;
- prohibit an invented deadline;
- prohibit unsupported advice;
- prohibit removal of a material exception.

An invariant is not proof that the model will comply. It is a declared requirement that deterministic source comparison, evaluation and regression tooling can test and report against.

The controlled invariant vocabulary, severity levels, guardian declarations and deterministic enforcement are implemented on the development line. The evaluator does not perform unrestricted semantic extraction or guarantee detection of every paraphrased meaning change.

See [Invariant declarations](invariants.md) for the vocabulary and migration contract.

## Reproducible build

A **reproducible build** is a deterministic compilation of a recipe and its ordered behavioural inputs.

`modding build` produces the same managed artifact bytes when the same canonical sources are supplied. Text line endings are normalised to LF for cross-platform stability; every other behavioural source change alters the relevant source hash and build identity.

A build contains:

- the compiled system prompt;
- a recipe lock;
- a JSON and Markdown ABOM;
- an artifact manifest.

No provider or model call is required. See [Reproducible builds, recipe locks and ABOMs](reproducible-builds.md).

## Recipe lock

A **recipe lock** records the exact ordered inputs that created a behavioural build:

- recipe identity, version, licence and manifest hash;
- selected mod references and versions;
- semantic roles and declared invariants;
- manifest and instruction-file hashes;
- dependencies, conflicts and compatibility declarations;
- source, compiled-prompt and build digests;
- the exact schema-version inputs used to calculate the build digest.

The lock does not contain provider, model or generation settings. Those belong to execution evidence because they can change between runs of the same build.

## Agent Behaviour Bill of Materials

An **Agent Behaviour Bill of Materials**, or **ABOM**, describes the behavioural components contained in a build.

The implemented ABOM records:

- recipe identity and version;
- ordered mods and versions;
- roles, capabilities and licences;
- dependencies and conflicts;
- declared invariants and prohibited transformations;
- compatibility declarations;
- source and build digests;
- compiled-prompt digest;
- explicit limitations.

The ABOM is available in machine-readable JSON and human-readable Markdown. It deliberately contains no timestamps, absolute checkout paths or machine identifiers, because those would make an otherwise identical build differ.

An ABOM is a build inventory, not proof that a model complied with the package. Tested-provider claims belong only in reviewed execution evidence.

## Evidence bundle

An **evidence bundle** is the durable record of one execution and its evaluation context.

The implemented bundle identifies:

- recipe, source, lock, ABOM and build digests;
- provider and requested model identifiers;
- supplied and effective generation settings;
- prompt, system-prompt and response hashes;
- exact raw response text and per-call execution metadata;
- evaluator version and fixture-set digest where applicable;
- source-control commit and dirty-tree status when available;
- artifact byte counts and SHA-256 values;
- privacy declarations and known limitations.

Prompt text is omitted by default to reduce accidental copying of sensitive source documents. Raw responses remain authoritative in `responses.jsonl`. Interpreted evaluation is stored separately without prompt or response text, so re-running an evaluator does not overwrite the original model output.

`modding verify-evidence` checks the manifest schema, evidence digest, artifact hashes, response hashes, build identity and unexpected files without calling a provider.

A valid bundle proves internal integrity, not semantic correctness or universal compatibility. See [Durable run evidence bundles](run-evidence.md).

## Stock and modded runs

A **stock run** uses the base model without the recipe contract. A **modded run** uses the same model and user request with the compiled behavioural contract.

Comparing both can help isolate the effect of selected mods, but it does not by itself prove that the modded result is correct. Both responses may fail in different ways.

## Evaluation case

An **evaluation case** contains source material or a prompt, expected behaviours, failure indicators and transparent checks.

The current evaluator supports deterministic legacy checks, manifest-bound invariant checks and structured source-output comparisons. These are useful regression signals, not semantic proof.

A future model-assisted judge must never be the sole quality gate and must never override an exact critical failure such as a changed deadline, amount, party, obligation or exception.

## Compatibility evidence

Compatibility is always contextual.

A valid compatibility statement has the form:

> This provider and model passed this locked recipe build on this fixture set under this configuration.

It must identify the exact provider, model, build digest, evaluator, fixture set, generation configuration, date and limitations.

Model Modding does not treat adapter availability, a valid evidence bundle or a single score as evidence that one provider is universally better.

## Maturity

A mod's maturity should reflect evidence and review, not popularity. Current statuses are `draft`, `experimental`, `community-validated`, `stable` and `archived`, as permitted by the manifest schema.

High-stakes maturity claims require appropriate domain review as well as passing technical checks.
