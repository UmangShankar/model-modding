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

### Changed

- New mod scaffolds declare `role: transformation` by default.
- Legacy v0.1 manifests without role or invariant declarations remain valid during migration.
- Trusted Document Explainer `0.2.0` now composes one transformation mod and four non-overlapping assurance guardians.
- Benchmark tests derive mocked response counts from the live evaluation plan.

### Notes

- This increment validates, exposes and composes invariant declarations and assurance instructions; it does not yet semantically enforce them or add severity-aware regression gates.

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
