# Model Modding

**An open framework for customising, composing, testing and sharing reusable mods for LLM behaviour, tools, memory, workflows and domain expertise.**

Model Modding explores a simple idea:

> What if customising an AI model felt more like modifying a motorcycle?

You start with a base model, then change how it behaves, what it knows, which tools it can use, how it remembers context, how it completes tasks and how its performance is evaluated.

Instead of rebuilding an assistant from scratch, Model Modding aims to make these modifications reusable, testable, composable and open to collaboration.

## Why Model Modding?

Today, many AI assistants are created through a mix of:

* system prompts
* instructions
* tools
* retrieval systems
* memory
* workflows
* evaluations
* user-interface decisions
* model-specific configuration

These components are often tightly coupled, difficult to compare and hard to reuse across projects.

Model Modding aims to create a shared structure for packaging these changes as independent **mods**.

A mod could make a model:

* more inquisitive
* better at product strategy
* safer when answering medical questions
* capable of conducting cited research
* more suitable for young learners
* connected to external tools
* able to follow a specialist workflow
* better at remembering project context

Mods can then be combined into complete **recipes** for specific use cases.

## What is a mod?

A mod is a portable package that changes one or more aspects of a language-model-powered system.

A mod may contain:

* behavioural instructions
* prompts and examples
* tool definitions
* workflow logic
* memory configuration
* domain knowledge
* compatibility rules
* evaluation scenarios
* safety requirements
* documentation

Example:

```text
mods/
└── inquisitive-strategist/
    ├── mod.yaml
    ├── README.md
    ├── instructions/
    ├── examples/
    ├── evaluations/
    └── compatibility/
```

Each mod should be independently understandable, testable and reusable.

## What is a recipe?

A recipe combines multiple mods into a complete assistant or experience.

For example, a **Product Strategy Copilot** might combine:

```yaml
name: product-strategy-copilot

mods:
  - personality/inquisitive-strategist
  - domains/product-management
  - workflows/deep-research
  - tools/web-search
  - memory/project-context
  - safety/citation-enforcement
```

This allows contributors to improve individual parts without needing to build the entire system.

## Project principles

### Modular

Each contribution should solve a clearly defined problem.

### Composable

Mods should work together through documented dependencies, compatibility rules and conflict handling.

### Model-agnostic

Where possible, mods should work across hosted and local models.

### Testable

A mod should include evaluations that describe the behaviour it is expected to produce.

### Transparent

Instructions, limitations, compatibility and evaluation results should be visible.

### Open to non-developers

Researchers, designers, educators, domain experts and evaluators should be able to contribute without writing production code.

### Responsible

Safety, privacy, uncertainty and misuse risks should be considered as part of the mod itself.

## Planned mod categories

```text
mods/
├── personality/
├── domains/
├── workflows/
├── tools/
├── memory/
├── safety/
├── interfaces/
└── experimental/
```

Examples include:

| Category     | Example              |
| ------------ | -------------------- |
| Personality  | Socratic Teacher     |
| Domain       | Product Management   |
| Workflow     | Deep Research        |
| Tool         | Web Search           |
| Memory       | Project Context      |
| Safety       | Citation Enforcement |
| Interface    | Voice Assistant      |
| Experimental | Multi-Agent Council  |

## Proposed repository structure

```text
model-modding/
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── GOVERNANCE.md
├── ROADMAP.md
├── SECURITY.md
│
├── docs/
├── framework/
├── packages/
├── schemas/
├── mods/
├── recipes/
├── templates/
├── evaluations/
├── examples/
├── playground/
├── registry/
├── research/
├── community/
└── .github/
```

The initial release will be deliberately smaller. The structure will grow as working standards and real contribution patterns emerge.

## Initial scope

The first milestone is to establish a usable Model Modding standard rather than support every possible model or use case.

Version `0.1` is expected to include:

* a standard `mod.yaml` manifest
* a JSON schema for validating mods
* a reusable mod template
* a basic command-line interface
* mod creation and validation commands
* several reference mods
* one composed recipe
* evaluation templates
* automated GitHub checks
* contribution and governance documentation
* clear no-code contribution paths

## Example mod manifest

```yaml
name: inquisitive-strategist
version: 0.1.0
status: experimental

description: >
  Encourages the model to examine assumptions, ask useful questions
  and explore strategic alternatives before recommending a decision.

category: personality

authors:
  - name: Model Modding Community

compatible_models:
  - openai
  - anthropic
  - google
  - ollama

capabilities:
  - assumption-testing
  - strategic-questioning
  - option-comparison

dependencies:
  - uncertainty-signalling

conflicts: []

evaluation:
  minimum_score: 0.75
  suites:
    - strategic-reasoning
    - question-quality

license: Apache-2.0
```

The specification is still being designed and will evolve through community proposals.

## Who can contribute?

Model Modding is intended to support several contributor paths.

### Developers

Build the runtime, CLI, adapters, registry and playground.

### Mod creators

Create reusable behaviours, workflows, tools and domain capabilities.

### Domain experts

Review specialist mods for accuracy, usefulness and risk.

### Evaluators

Create test scenarios, rubrics, benchmarks and regression suites.

### Researchers

Run reproducible experiments and publish findings.

### Designers

Improve onboarding, documentation, interfaces and visual communication.

### Writers and translators

Improve explanations, examples, guides and localisation.

### Community organisers

Run challenges, working groups, demonstrations and collaboration programmes.

## Ways to contribute

Early contributions may include:

* proposing a mod
* creating an example interaction
* writing an evaluation scenario
* reviewing a domain-specific mod
* improving documentation
* testing a mod on another model
* identifying compatibility issues
* designing the playground
* building an adapter
* helping define the mod specification

Look for issues labelled:

```text
good-first-mod
good-first-evaluation
no-code
help-wanted
domain-expert-needed
documentation
research
design
```

## Requests for Mods

The project will use **Requests for Mods**, or RFMs, to describe problems the community can solve.

Examples:

```text
RFM-001: A classroom-safe tutoring mod
RFM-002: A mod for explaining legal documents clearly
RFM-003: A workflow for evaluating product ideas
RFM-004: A reliable citation and source-checking mod
```

An RFM should describe:

* the problem
* intended users
* expected behaviour
* risks and constraints
* acceptance criteria
* evaluation approach
* skills needed

## Mod maturity

Mods may move through the following stages:

| Status              | Meaning                                          |
| ------------------- | ------------------------------------------------ |
| Draft               | Early idea or incomplete implementation          |
| Experimental        | Usable but still under active testing            |
| Community Validated | Reviewed and evaluated by multiple contributors  |
| Stable              | Versioned, maintained and suitable for wider use |
| Archived            | No longer maintained or replaced                 |

A mod should not be considered stable based only on popularity or maintainer opinion. Its limitations and evaluation evidence should be visible.

## Governance

Model Modding will begin with lightweight, transparent governance.

Major changes may be proposed through **Model Modding Proposals**, or MMPs.

Examples:

```text
MMP-001: Standard Mod Manifest
MMP-002: Mod Composition and Conflict Resolution
MMP-003: Evaluation Requirements
MMP-004: Community Governance
```

The goal is to avoid important decisions being hidden in private conversations or controlled by a single contributor.

See `GOVERNANCE.md` once published.

## Roadmap

### Phase 1 — Define the standard

* define the anatomy of a mod
* publish the manifest schema
* create the mod template
* document compatibility and composition

### Phase 2 — Build the foundation

* create the CLI
* validate manifests
* load and inspect mods
* publish reference implementations

### Phase 3 — Establish evaluation

* create evaluation templates
* run regression scenarios
* compare model and mod combinations
* publish evaluation results

### Phase 4 — Open collaboration

* publish contributor pathways
* launch Requests for Mods
* create working groups
* run community challenges

### Phase 5 — Build the ecosystem

* launch a public mod registry
* create a visual playground
* support third-party mod repositories
* enable recipe sharing and remixing

See `ROADMAP.md` for the evolving plan.

## What this project is not

Model Modding is not currently intended to be:

* a new foundation model
* a model-training framework
* a replacement for model-provider SDKs
* a prompt marketplace
* a benchmark claiming one model is universally best
* a guarantee that every mod will work identically across models

It is an attempt to create an open structure around the many layers used to turn a base model into a useful system.

## Current status

**Status: Early concept and foundation stage**

The specification, repository structure and first reference implementations are being developed in the open.

Expect breaking changes during the initial releases.

## Join the workshop

The project is looking for people interested in:

* language models
* open-source systems
* product design
* agent workflows
* evaluations
* responsible AI
* local models
* model behaviour
* domain-specific assistants
* human-computer interaction

You do not need to be an AI engineer to participate.

Open a discussion, propose a mod, review an idea or help define the standards.

## Licence

The project is intended to be released under the **Apache License 2.0**.

Individual datasets, external model integrations or contributed assets may have additional licence requirements. These must be clearly documented within the relevant package or mod.

## Acknowledgement

The name Model Modding comes from the culture of modifying machines: taking a strong base, understanding how it works, changing individual components and learning through experimentation.

The ambition is to bring that same curiosity, craft and openness to language-model-powered systems.

**Build a mod. Test it. Share it. Remix it.**
