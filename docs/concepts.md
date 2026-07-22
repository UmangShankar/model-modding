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
- an optional semantic role;
- optional machine-readable invariant declarations.

A mod can declare `role: transformation` when it primarily changes content or behaviour, or `role: assurance` when it primarily protects a safeguard or detects a prohibited transformation. The role is optional during migration so existing v0.1 manifests remain valid.

## Recipe

A **recipe** selects mods and declares their composition order. Composition produces an inspectable behavioural contract rather than hiding the system instructions inside application code.

A recipe is not only a convenient prompt bundle. Its target role is to provide a stable build unit that can be locked, hashed, executed across providers and linked to evaluation evidence.

## Invariant

An **invariant** is a machine-readable preservation promise or prohibition that applies to a transformation.

Examples include:

- preserve an exact deadline;
- preserve the party responsible for an obligation;
- preserve a condition or exception;
- prohibit an invented deadline;
- prohibit unsupported advice;
- prohibit removal of a material exception.

An invariant is not proof that the model will comply. It is a declared requirement that evaluation and regression tooling can test and report against.

Invariant declarations are implemented in the v0.1.2 development line through a standalone versioned schema referenced by mod manifests. The repository can validate and inspect the declarations today. Semantic extraction, severity-aware scoring and automatic critical-failure enforcement remain later evaluator increments.

See [Invariant declarations](invariants.md) for the vocabulary and migration contract.

## Evidence bundle

An **evidence bundle** is the durable record of one execution and its evaluation context.

The v0.2 evidence model will identify:

- the recipe and exact version;
- installed mods and versions;
- recipe and build digests;
- provider and exact model identifier;
- supplied and effective generation settings;
- source-input and response hashes;
- evaluator version and fixture set;
- critical, major and minor failures;
- source-control commit and dirty-tree status;
- known limitations.

Raw execution evidence and interpreted evaluation results are related but distinct. Re-running an evaluator must not overwrite the original model response.

## Agent Behaviour Bill of Materials

An **Agent Behaviour Bill of Materials**, or **ABOM**, describes the behavioural components contained in a build.

The target ABOM records:

- recipe identity and version;
- installed mods and versions;
- capabilities;
- declared invariants;
- prohibited transformations;
- compatibility declarations;
- known limitations;
- build digest;
- tested providers only when backed by evidence.

ABOM generation is planned for v0.1.6. The term is documented now because it is central to the product contract and evidence model.

## Stock and modded runs

A **stock run** uses the base model without the recipe contract. A **modded run** uses the same model and user request with the compiled behavioural contract.

Comparing both can help isolate the effect of selected mods, but it does not by itself prove that the modded result is correct. Both responses may fail in different ways.

## Evaluation case

An **evaluation case** contains source material or a prompt, expected behaviours, failure indicators and transparent checks.

The current evaluator supports deterministic assertions such as required terms, prohibited terms, question counts and response length. These are useful regression signals, not semantic proof.

The v0.2 evaluation model will add:

1. deterministic invariant checks;
2. structured source-output comparison;
3. optional model-assisted judgement;
4. recorded human review.

A model judge must never be the sole quality gate and must never override an exact critical failure such as a changed deadline, amount, party, obligation or exception.

## Compatibility evidence

Compatibility is always contextual.

A valid compatibility statement has the form:

> This provider and model passed this recipe on this fixture set under this configuration.

It must identify the exact provider, model, recipe digest, evaluator, fixture set, generation configuration, date and limitations.

Model Modding does not treat a single score as evidence that one provider is universally better.

## Maturity

A mod's maturity should reflect evidence and review, not popularity. Current statuses are `draft`, `experimental`, `community-validated`, `stable` and `archived`, as permitted by the manifest schema.

High-stakes maturity claims require appropriate domain review as well as passing technical checks.
