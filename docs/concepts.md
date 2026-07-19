# Core concepts

A **mod** is a versioned package that makes a defined change to an LLM-powered system. It may include instructions, examples, compatibility declarations, dependencies, conflicts and evaluation cases.

A **recipe** selects mods and declares their composition order. Composition produces an inspectable system contract rather than hiding behaviour in application code.

A **stock run** uses the base model without the recipe contract. A **modded run** uses the same model and user prompt with the compiled contract. Comparing both helps isolate the effect of the selected mods.

An **evaluation case** contains a prompt, expected behaviours, failure indicators and optional deterministic checks. Deterministic results are regression signals, not proof of universal quality.

A mod's maturity should reflect evidence and review, not popularity. Current statuses are draft, experimental, community-validated, stable and archived as permitted by the manifest schema.
