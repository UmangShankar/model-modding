# Roadmap

## Product direction

Model Modding is becoming the open packaging and assurance layer for portable AI-agent behaviour.

The first market wedge is:

> Meaning-preserving, evidence-backed transformations for high-stakes work.

The flagship proof is one exceptional `trusted-document-explainer` recipe that can run across Ollama, Anthropic and OpenAI while preserving declared invariants, producing reproducible evidence and failing CI when material meaning changes.

The objective is not to create a universal model leaderboard. The objective is to prove that the same versioned behavioural package can be built, locked, executed, inspected, evaluated and governed across different models.

## Release state at a glance

| State | Version or branch | Status |
| --- | --- | --- |
| Current package version | `0.1.1` | Published version identifier and current `pyproject.toml` version. |
| Current development state | `main` | Engineering increments `v0.1.2` through `v0.1.7` are implemented but are not represented as separately published package releases. |
| Next evidence-backed release | `v0.2.0` | Blocked until reviewed three-provider evidence, baseline approval, the public case study and independent reproduction pass the enforced release contract. |

The repository deliberately remains at package version `0.1.1` while the evidence operations are completed. See [Version and release status](version-status.md) for the canonical wording.

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

Current package release. Delivered:

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

Implemented on `main` after the `0.1.1` package release:

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

Implemented on `main` after the `0.1.1` package release:

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

Implemented on `main` after the `0.1.1` package release:

- an optional `anthropic` dependency group;
- `ANTHROPIC_API_KEY` and SDK readiness diagnostics;
- system and user instruction mapping to the Messages API;
- portable temperature, top-p, token-limit and stop-sequence mapping;
- explicit rejection of unsupported seed requests before API execution;
- a recorded Anthropic-required `max_tokens` default when omitted;
- exact returned model, message and stop metadata;
- normalised usage, latency and finish reason;
- model discovery through the provider contract;
- normalised authentication, connection, HTTP and response errors;
- mocked contract tests and an opt-in paid live smoke test;
- no mandatory cloud call in pull-request CI.

## v0.1.5 — OpenAI provider

Implemented on `main` after the `0.1.1` package release:

- an optional `openai` dependency group;
- `OPENAI_API_KEY` and SDK readiness diagnostics;
- instruction and user-input mapping to the Responses API;
- neutral `max_tokens` mapping to `max_output_tokens`;
- explicit rejection of unsupported seed and stop requests before API execution;
- exact returned model, response ID, status, service-tier and incomplete-reason metadata;
- normalised input, output and total token usage;
- response status or incomplete reason mapped to the provider-neutral finish field;
- model discovery through the provider contract;
- normalised authentication, connection, HTTP and malformed-response errors;
- mocked contract tests and an opt-in paid live smoke test;
- no mandatory cloud call in pull-request CI.

Reviewed three-provider portability evidence remains a separate evidence publication step. Adapter delivery alone does not establish compatibility.

## v0.1.6 — Reproducible builds, locks and ABOM

Implemented on `main` after the `0.1.1` package release:

- `modding build` for deterministic behavioural bundles;
- `modding verify-build` for offline byte-level verification;
- runtime-equivalent compiled system prompts;
- UTF-8 and LF canonicalisation for cross-platform source hashing;
- canonical POSIX repository-relative paths;
- SHA-256 records for recipe manifests, mod manifests and ordered instruction files;
- transparent source and build digests;
- independently recomputable digest inputs including schema versions;
- versioned recipe-lock, ABOM and build-manifest schemas;
- ordered recipe lock files with component digests;
- Agent Behaviour Bills of Materials in JSON and Markdown;
- roles, licences, dependencies, conflicts, compatibility declarations and invariants in the ABOM;
- deterministic output without timestamps, absolute paths or machine identifiers;
- refusal to mix unmanaged paths into a build directory;
- line-ending stability tests;
- behavioural byte-change invalidation tests;
- generated-artifact tamper detection;
- flagship build and verification gates in editable and clean-wheel CI.

The ABOM identifies packaged behavioural inputs. It does not establish provider or model compliance.

## v0.1.7 — Evidence comparison and regression gates

Engineering complete on `main` after the `0.1.1` package release:

- versioned durable run-evidence bundle schema;
- `--evidence` support for provider-aware `run`, `evaluate` and `benchmark`;
- exact recipe source, build, lock and ABOM identities in every bundle;
- raw responses preserved as newline-delimited JSON with per-call execution metadata;
- prompt text omitted by default and represented by SHA-256;
- interpreted evaluation stored separately from raw responses;
- evaluator, fixture-set, provider, model, generation and source-control context;
- artifact, response and evidence digests;
- `modding verify-evidence` for offline schema, hash and consistency checks;
- unmanaged-artifact and tamper detection;
- deterministic fixed-context and mocked provider tests without cloud calls;
- `modding compare-evidence` for strict baseline-versus-candidate comparison;
- verified-input and `not_comparable` gates before behavioural interpretation;
- exact recipe, build, fixture, evaluator and target-set comparability checks;
- new, resolved, unchanged and severity-changed failure reporting;
- configurable blocking of new and escalated critical, major or minor failures;
- deterministic JSON and Markdown comparison reports with canonical digests;
- `modding matrix-evidence` for provider/model-by-invariant summaries;
- tested, passed and failed invariant/source observations per exact target;
- repeated-run aggregation through `modding aggregate-evidence`;
- scoped reviewed-baseline activation through `modding activate-baseline`;
- concise automatic pull-request evidence summaries;
- protected and cost-limited Anthropic and OpenAI workflows;
- an allowlisted self-hosted Ollama workflow;
- release-candidate evidence assembly and v0.2 readiness checks;
- v0.2 tag publication blocked unless reviewed evidence passes the gate;
- versioned evidence-comparison, compatibility-matrix, repeated-evidence, reviewed-baseline and release-readiness schemas;
- dedicated build, evidence, comparison, aggregation, matrix, release and clean-wheel gates in CI.

Engineering complete; evidence operations remaining for a v0.2 release:

- configure protected GitHub environments, secrets, exact model allowlists and the self-hosted Ollama runner;
- execute and review three complete runs for selected Ollama, Anthropic and OpenAI targets;
- approve the first authoritative checked-in baseline;
- commit reviewed release-candidate evidence;
- publish the case study with failures and limitations;
- complete one independent reproduction using the documented guide.

The operational checklist is tracked in [Issue #36](https://github.com/UmangShankar/model-modding/issues/36).

## v0.2.0 — Portable Assured Behaviour

Status: evidence-gated and not yet released.

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
- at least three repetitions for every release target;
- zero critical failures in reviewed release evidence;
- a public case study that includes failures and limitations;
- one independent developer reproducing the hero benchmark.

## CI and evidence model

Every pull request runs:

1. schema and manifest validation;
2. deterministic flagship recipe build and ABOM verification;
3. evidence privacy, integrity and command tests;
4. strict comparison and compatibility-matrix contract tests;
5. repeated-evidence and release-readiness contract tests;
6. a clearly labelled synthetic end-to-end evidence-pipeline exercise;
7. existing unit and fixture regression tests;
8. Python distribution build;
9. clean-wheel installation and command verification.

Synthetic CI evidence validates machinery only. It must never be published as provider compatibility evidence.

Real provider runs use manual protected workflows, explicit exact-model allowlists, capped repetitions, capped output tokens, complete 40-case evaluations and durable uploaded artifacts. Cloud evaluation is not mandatory for untrusted pull requests.

A `v0.2*` tag cannot be released unless checked-in reviewed evidence covers all three providers, contains at least three repetitions and 40 cases per exact target, has zero critical failures and passes the compatibility-matrix gate.

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
