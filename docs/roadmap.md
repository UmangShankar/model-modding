# Roadmap

## Product direction

Model Modding is becoming the open packaging and assurance layer for portable AI-agent behaviour.

The first market wedge is:

> Meaning-preserving, evidence-backed transformations for high-stakes work.

The flagship proof is one exceptional `trusted-document-explainer` recipe that can run across Ollama, Anthropic and OpenAI while preserving declared invariants, producing reproducible evidence and failing CI when material meaning changes.

The objective is not to create a universal model leaderboard. The objective is to prove that the same versioned behavioural package can be executed, inspected, evaluated and governed across different models.

## v0.1.0 — Foundation

Delivered:

- manifest schemas and validation;
- mod scaffolding;
- inspection and deterministic composition;
- static Workshop experiences;
- local Ollama execution;
- stock-versus-modded evaluations and scorecards;
- multi-model local benchmarks;
- benchmark evidence publication and validation;
- release and contribution foundations.

## v0.1.1 — Stabilisation and positioning

Delivered:

- Windows and POSIX mod-reference compatibility;
- canonical POSIX references in generated metadata;
- unified CLI routing and complete top-level help;
- evaluation latency and response-length evidence;
- portable UTF-8 and LF report output;
- repository filename hygiene;
- portable assured behaviour positioning;
- invariant, evidence-bundle and ABOM vocabulary;
- explicit product non-goals;
- the Trusted Document Explainer product contract.

## v0.1.2 — Invariant specification and flagship refactor

Delivered on the development line:

- a controlled invariant reference vocabulary;
- machine-readable preserve and prohibit declarations;
- critical, major and minor severity levels;
- transformation and assurance semantic roles;
- backward-compatible schema migration;
- separate deadline, obligation, exception and source-grounding guardians;
- a composed Trusted Document Explainer reference recipe;
- deterministic invariant evaluator gates;
- exactly 40 meaning-preservation cases;
- classified adversarial and paraphrase coverage;
- 23 typed source facts across 16 representative cases;
- structured source-output comparison for values, context and prohibited transformations;
- report schema `0.3` with combined assurance failures.

## v0.1.3 — Provider-neutral runtime

Delivered on the development line:

- provider-neutral request, response, usage and generation-option contracts;
- validation for `temperature`, `top_p`, `max_tokens`, `seed` and stop sequences;
- an extensible provider registry and configuration boundary;
- normalised provider configuration, connection, HTTP and response errors;
- Ollama transport migrated behind the provider boundary;
- normalised Ollama token usage, latency and finish reason;
- requested and adapter-effective generation settings;
- backward-compatible Ollama imports and local commands;
- provider-registry diagnostics in `modding doctor`;
- explicit provider selection on `run`, `evaluate` and `benchmark`;
- shared provider configuration across runtime commands;
- exact provider, endpoint, model and generation metadata in evaluation and benchmark reports;
- per-response execution metadata including usage and finish reason;
- provider-aware report schema `0.4`;
- opt-in migration that preserves existing default Ollama scripts.

## v0.1.4 — Anthropic provider

Planned:

- optional dependency group;
- authentication diagnostics;
- system and user instruction mapping;
- usage, latency and finish-reason normalisation;
- mocked tests and opt-in live smoke tests.

## v0.1.5 — OpenAI provider

Planned:

- the same provider contract and test suite as Anthropic;
- provider-specific error normalisation;
- exact model identifiers and generation settings;
- three-provider portability evidence only after evaluator v2 is credible.

## v0.1.6 — Reproducible builds, locks and ABOM

Planned:

- `modding build`;
- canonical cross-platform digests;
- recipe lock files;
- ABOM JSON and Markdown output;
- build verification without a model API call;
- byte-level invalidation tests.

## v0.1.7 — Evidence comparison and regression gates

Planned:

- run evidence bundles;
- compatibility matrices by invariant;
- baseline-versus-candidate comparison;
- critical-failure regression gates;
- PR summaries;
- protected and cost-limited cloud workflows.

## v0.2.0 — Portable Assured Behaviour

Definition of done:

- one versioned flagship recipe;
- four narrow assurance mods;
- at least 40 benchmark cases;
- Ollama, Anthropic and OpenAI execution;
- invariant-aware evaluation;
- reproducible builds and digests;
- recipe locks and ABOMs;
- validated evidence bundles;
- compatibility matrices;
- automated regression detection;
- CI failure when material meaning changes;
- a public case study that includes failures and limitations;
- one independent developer reproducing the hero benchmark.

## CI model

Every pull request should run:

1. schema validation;
2. unit tests;
3. deterministic fixture tests;
4. recipe build and ABOM verification when available;
5. checked-in regression comparison when available.

Cloud evaluation will not be mandatory for untrusted fork pull requests. Full provider benchmarks will use trusted branch events, protected environments, explicit model allowlists and cost limits.

## Explicitly deferred

The v0.2 programme does not include:

- additional personality mods;
- hosted SaaS;
- a registry marketplace;
- a visual recipe builder;
- Bedrock or Vertex adapters;
- broad agent orchestration;
- fine-tuning;
- user accounts or billing;
- an enterprise dashboard;
- a universal model leaderboard;
- formal certification;
- automated prompt optimisation.

## Prioritisation rule

A feature belongs in the v0.2 programme only when it materially improves at least one of:

- portability;
- inspectability;
- preservation measurement;
- reproducibility;
- reusable compatibility evidence.

Otherwise it is deferred.
