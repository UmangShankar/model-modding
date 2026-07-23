# Changelog

All notable changes to Model Modding are documented here.

## [Unreleased]

### Added

- A standalone versioned invariant declaration schema.
- Optional `transformation` and `assurance` semantic roles for mods.
- Controlled preservation and prohibited-transformation vocabularies.
- `critical`, `major` and `minor` invariant severities.
- Offline cross-schema validation through a local schema registry.
- Role and invariant output in `modding inspect`, including JSON mode.
- Initial machine-readable declarations for Plain Language Explainer.
- Deadline, Obligation, Exception and Source Grounding Guardians.
- Deterministic invariant evaluator v2 with structured severity-aware failures.
- Exactly 40 flagship cases, including eighteen adversarial or paraphrase fixtures.
- Twenty-three typed source facts across sixteen representative guardian cases.
- Structured source-output comparison for values, required context and prohibited output forms.
- Configurable `--fail-on critical|major|minor|none` pipeline gates.
- Provider-neutral request, response, usage and generation-option contracts.
- An extensible provider registry with normalised configuration and error boundaries.
- A first-class Ollama provider adapter with normalised usage and execution metadata.
- Built-in Anthropic and OpenAI adapters behind the same neutral runtime contract.
- Optional `anthropic` and `openai` dependency groups and authentication diagnostics.
- Mocked provider contract tests and opt-in paid live smoke tests.
- `modding build` and `modding verify-build` for deterministic behavioural bundles.
- Versioned recipe-lock, ABOM and build-manifest schemas.
- Canonical SHA-256 source, component, prompt, artifact and build identities.
- Agent Behaviour Bills of Materials in canonical JSON and human-readable Markdown.
- A versioned durable run-evidence bundle schema.
- `--evidence` support on provider-aware `run`, `evaluate` and `benchmark` commands.
- `modding verify-evidence` for offline evidence schema, digest and artifact verification.
- Raw response preservation in newline-delimited JSON with exact per-call execution metadata.
- Prompt-private evidence records using prompt hashes instead of source text by default.
- Separate interpreted evaluation artifacts without embedded prompt or response text.
- Evidence manifests containing build, lock, ABOM, provider, model, generation, evaluator, fixture-set and source-control context.
- `modding compare-evidence` for strict verified baseline-versus-candidate comparison.
- Distinct clean, regression and `not_comparable` exit codes.
- New, resolved, unchanged, severity-changed and severity-escalated failure reporting.
- `modding matrix-evidence` for provider/model-by-invariant compatibility summaries.
- Versioned evidence-comparison and compatibility-matrix schemas.
- `modding aggregate-evidence` for repeated compatible executions with repetition and zero-critical gates.
- `modding activate-baseline` for scoped reviewed evidence baselines.
- `modding evidence-summary` for concise CI and pull-request reporting.
- `modding release-check` for provider, repetition, case and critical-failure release gates.
- `modding validate-provider-run` for exact model allowlists and cost-bound cloud plans.
- Versioned repeated-evidence, reviewed-baseline and release-readiness schemas.
- Automatic pull-request evidence summaries using clearly labelled synthetic contract evidence.
- Protected Anthropic/OpenAI workflow with environment approval, exact model allowlists, capped repetitions and capped output tokens.
- Protected self-hosted Ollama workflow with exact model allowlists.
- Release-candidate evidence assembly and deterministic release summaries.
- Independent v0.2 reproduction documentation.
- Tests covering aggregation, baseline activation, release readiness, summaries and provider-run validation.

### Changed

- New mod scaffolds declare `role: transformation` by default.
- Legacy v0.1 manifests without role or invariant declarations remain valid during migration.
- Trusted Document Explainer `0.2.0` composes one transformation mod and four non-overlapping assurance guardians.
- Guardian fixtures bind deterministic assertions to manifest-declared invariants and matching severities.
- Multi-model benchmarks use the same combined invariant and source-comparison result as `modding evaluate`.
- The flagship evaluation plan contains exactly 40 cases rather than 22.
- Ollama execution delegates to the provider adapter while preserving existing imports and commands.
- Provider-aware run, evaluation and benchmark reports record provider, endpoint, exact model, requested/effective settings, usage and finish reason.
- Anthropic rejects unsupported seed requests and records a deliberate `max_tokens` default of 1024 when omitted.
- OpenAI maps neutral `max_tokens` to `max_output_tokens` and rejects unsupported seed and stop requests.
- `modding doctor` requires reproducible-build, evidence, comparison, matrix, repeated-evidence, baseline and release-readiness schemas.
- CI gates evidence integrity, strict comparison, matrix generation, repeated aggregation, release readiness, the behavioural suite and clean-wheel command availability.
- Pull requests receive one updateable synthetic evidence summary and downloadable contract artifact.
- The package release workflow verifies tag/package-version agreement.
- `v0.2*` tags are blocked unless checked-in reviewed evidence covers Ollama, Anthropic and OpenAI, includes at least three 40-case repetitions per target, has zero critical failures and passes the matrix gate.

### Notes

- Deterministic invariant and structured source comparisons block configured severity thresholds and cannot be overridden by aggregate scores.
- The 40-case threshold is satisfied, but the evaluator does not perform unrestricted semantic extraction or guarantee detection of every paraphrased meaning change.
- Existing published benchmark evidence remains immutable and does not retroactively include expanded fixtures, evaluator layers, cloud providers, build identities, durable evidence or comparison formats.
- Ollama, Anthropic and OpenAI are built-in providers.
- Normal pull-request CI does not call Anthropic or OpenAI. Cloud compatibility claims require reviewed evidence from explicit protected runs.
- Adapter availability, a valid bundle, a passing comparison, repeated synthetic runs, a matrix cell or a single score does not establish universal cross-provider compatibility.
- A recipe lock and ABOM identify packaged behavioural inputs; they do not prove provider or model compliance.
- Prompt hashes reduce accidental source copying but are not a substitute for access controls or the original source during human review.
- Synthetic CI evidence validates pipeline mechanics only and must never be committed as reviewed provider evidence.
- The engineering pipeline is complete, but v0.2 remains intentionally unreleased until real reviewed three-provider evidence, baseline approval, a public case study and independent reproduction are supplied.

## [0.1.1] - 2026-07-22

### Added

- Portable assured behaviour as the project's primary product direction.
- Core vocabulary for invariants, evidence bundles and Agent Behaviour Bills of Materials.
- A formal Trusted Document Explainer product contract for the v0.2 programme.
- Explicit product non-goals and deferred scope.
- Evaluation latency and response-length evidence in JSON, Markdown and console output.
- Regression tests for Windows and POSIX mod references, unified CLI help, report encoding and repository filename hygiene.

### Changed

- Mod references accept both `/` and `\` input separators and emit canonical POSIX references.
- `doctor` and `benchmark` use the primary CLI parser and appear in top-level help.
- Evaluation and benchmark reports are written as UTF-8 with LF line endings.
- The README and quick start lead with the flagship meaning-preservation use case and distinguish current features from v0.2 targets.

### Removed

- The case-colliding uppercase pull request template; the canonical lowercase template remains.

### Notes

- This release does not yet implement machine-readable invariants, cloud providers, ABOM generation, recipe locks, compatibility matrices or semantic regression gates.
- The first published benchmark remains immutable and documents material behavioural and evaluator limitations that drive the v0.2 roadmap.

## [0.1.0] - 2026-07-19

### Added

- JSON schemas for mod and recipe manifests.
- `modding validate` repository validation.
- `modding create mod` scaffolding with schema-aligned categories.
- `modding inspect` for capabilities, compatibility, dependencies and evaluation coverage.
- `modding compose` for deterministic recipe compilation and conflict detection.
- The browser-based Model Modding Workshop.
- Local Ollama execution through `modding run`.
- A Local Dyno for stock-versus-modded comparison.
- `modding evaluate` with dry-run plans, deterministic checks, Markdown/JSON reports and regression detection.
- A visual Evaluation Scorecard.
- Reference mods: Inquisitive Strategist, Socratic Teacher and Citation Guardian.
- Reference recipes: Product Strategy Copilot and Research Learning Companion.
- Release-readiness diagnostics through `modding doctor`.

### Notes

This is the first public foundation release. Manifest and report formats may evolve before 1.0 as the project learns from real-world contributions.
