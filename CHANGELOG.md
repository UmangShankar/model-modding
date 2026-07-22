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
- Invariant vocabulary, migration and authoring documentation.
- Deadline Guardian for dates, durations, units, triggers and invented time limits.
- Obligation Guardian for named parties, duties, permissions and prohibitions.
- Exception Guardian for conditions, exceptions, eligibility rules and sequence.
- Source Grounding Guardian for source claims, uncertainty, missing evidence and fabricated citations.
- Sixteen independent guardian evaluation cases.
- Source-grounding prohibitions for invented claims, fabricated citations and presented missing evidence.
- Deterministic invariant evaluator v2 with structured failure records.
- Severity totals for stock and modded responses in evaluation and benchmark reports.
- Configurable `--fail-on critical|major|minor|none` pipeline gates.
- Deliberate regression tests proving that critical invariant failures return a non-zero exit code.
- Eighteen classified adversarial and paraphrase fixtures across the four assurance guardians.
- A controlled attack taxonomy covering deadline, actor, modality, exception, sequence and grounding failures.
- Repository gates enforcing exactly 40 flagship cases, balanced distribution, unique identities and invariant-aware fixture definitions.
- Authoring documentation for adversarial and paraphrase fixtures.
- Twenty-three typed source facts across sixteen representative guardian cases.
- Structured source-output comparison for accepted values, required context and prohibited output forms.
- Loader validation proving canonical source facts and context occur in the fixture input.
- Report schema `0.3` with explicit evaluator layers and source-comparison failures.
- Tests proving critical source-comparison failures enter the existing severity gate.
- Provider-neutral request, response, usage and generation-option contracts.
- An extensible provider registry with normalised configuration and error boundaries.
- Portable generation settings for temperature, top-p, token limits, seeds and stop sequences.
- A first-class Ollama provider adapter with normalised token usage, finish reason and timing metadata.
- Provider-registry diagnostics in `modding doctor`.
- Explicit `--provider` selection for `run`, `evaluate` and `benchmark`.
- Shared runtime configuration for provider endpoints and portable generation settings.
- Provider-aware report schema `0.4` with exact runtime and per-response execution metadata.
- Regression tests covering unknown providers, model resolution, token usage and provider evidence.

### Changed

- New mod scaffolds declare `role: transformation` by default.
- Legacy v0.1 manifests without role or invariant declarations remain valid during migration.
- Trusted Document Explainer `0.2.0` now composes one transformation mod and four non-overlapping assurance guardians.
- Guardian fixtures bind deterministic assertions to manifest-declared invariants and matching severities.
- Multi-model benchmarks use the same combined invariant and source-comparison result as `modding evaluate`.
- Benchmark tests derive mocked response counts from the live evaluation plan.
- The flagship evaluation plan now contains exactly 40 cases rather than 22.
- Ollama model discovery, streaming and recipe execution now delegate to the provider adapter while preserving existing imports and commands.
- `modding run` now reports provider identity, endpoint, requested generation settings, finish reason and token usage when available.
- Provider-aware evaluation and benchmark runs now record provider, endpoint, exact model, requested and effective settings, usage and finish reason.
- Provider dispatch remains opt-in during v0.1.3 so existing default Ollama scripts and direct Python APIs continue to behave as before.

### Notes

- Deterministic invariant and structured source comparisons block configured severity thresholds and cannot be overridden by aggregate scores.
- The 40-case threshold is satisfied, but the evaluator does not perform unrestricted semantic extraction or guarantee detection of every paraphrased meaning change.
- Existing published benchmark evidence remains immutable and does not retroactively include the expanded fixture or evaluator layers.
- Only Ollama is registered as a built-in provider in this increment. Anthropic and OpenAI remain separate adapters.
- Ollama defaults that are not reported by the API are not invented as effective settings.

## [0.1.1] - 2026-07-22

### Added

- Portable assured behaviour as the project's primary product direction.
- Core vocabulary for invariants, evidence bundles and Agent Behaviour Bills of Materials.
- A formal Trusted Document Explainer product contract for the v0.2 programme.
- Explicit product non-goals and deferred scope.
- Evaluation latency and response-length evidence in JSON, Markdown and console output.
- Regression tests for Windows and POSIX mod references, unified CLI help, report encoding and repository filename hygiene.

### Changed

- Mod references now accept both `/` and `\` input separators and emit canonical POSIX references.
- `doctor` and `benchmark` now use the primary CLI parser and appear in top-level help.
- Evaluation and benchmark reports are written as UTF-8 with LF line endings.
- The README and quick start now lead with the flagship meaning-preservation use case and distinguish current features from v0.2 targets.

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
