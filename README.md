# Model Modding

**An open framework for packaging, combining, running and evaluating reusable behavioural modifications for language models.**

> Start with a stock model. Install transparent mods. Inspect the build. Run it locally. Measure what changed.

Model Modding treats assistant behaviour like a configurable machine: individual parts are versioned as **mods**, complete configurations are assembled as **recipes**, and their effects are tested with visible evaluation cases.

## The core loop

```text
Create → Validate → Inspect → Compose → Run → Evaluate
```

```bash
python -m pip install -e ".[dev]"
modding validate
modding inspect socratic-teacher
modding compose research-learning-companion
modding run research-learning-companion \
  --model llama3.2 \
  --prompt "Explain compound interest to a beginner"
modding evaluate research-learning-companion \
  --model llama3.2
modding doctor
```

Local execution uses [Ollama](https://ollama.com/) on `127.0.0.1` by default. No cloud API key is required.

## What is included in v0.1.0

- JSON schemas for mod and recipe manifests
- a Python CLI and mod scaffolding command
- deterministic composition with dependency and conflict checks
- inspection of capabilities, instructions and evaluation coverage
- local Ollama execution with loopback safety controls
- stock-versus-modded evaluation reports and regression detection
- three reference mods and two reference recipes
- a static Workshop, Local Dyno and Evaluation Scorecard

## Join the community build

The next phase is about real contribution patterns: new mods, independent evaluation, domain review and cross-model testing.

- Browse the [community hub](community/README.md).
- Pick an open [Request for Mod](community/rfms/README.md).
- Explore the current [mod and recipe catalogue](community/catalogue.md).
- Use the **Request for Mod** issue template to propose another unmet need.

The first requests include beginner-friendly and specialist opportunities across document explanation, child-safe learning, meeting decisions, health information and product discovery.

## Try the visual workshop

Serve the repository:

```bash
python -m http.server 8000
```

Then open:

- **Workshop:** `http://localhost:8000/workshop/`
- **Local Dyno:** `http://localhost:8000/workshop/local.html`
- **Evaluation Scorecard:** `http://localhost:8000/workshop/scorecard.html`

## Anatomy of a mod

```text
mods/personality/socratic-teacher/
├── mod.yaml
├── README.md
├── instructions/system.md
├── examples/
└── evaluations/cases.yaml
```

A mod should make one understandable change, document compatibility and limitations, and include evidence for how its behaviour will be assessed.

## Create a mod

```bash
modding create mod my-first-mod \
  --category personality \
  --author "Your Name" \
  --github your-handle
```

Read [Creating mods](docs/creating-mods.md), the [manifest reference](docs/manifest-reference.md), and [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

## Reference builds

### Research Learning Companion

Combines **Socratic Teacher** with **Citation Guardian** to guide learning while keeping facts, inference and uncertainty visible.

### Product Strategy Copilot

Uses **Inquisitive Strategist** to clarify decisions, challenge assumptions and prefer reversible experiments before expensive commitments.

## Principles

- **Modular:** one clearly defined change per mod
- **Composable:** dependencies, order and conflicts are explicit
- **Transparent:** instructions and evaluation evidence remain inspectable
- **Model-aware, not model-locked:** compatibility is documented rather than assumed
- **Measurable:** claims of improvement should be backed by repeatable cases
- **Open to non-developers:** domain experts, educators, researchers and designers can contribute
- **Responsible:** safety, privacy, uncertainty and misuse risks belong in the package

## Documentation

- [Concepts](docs/concepts.md)
- [Creating mods](docs/creating-mods.md)
- [Composing recipes](docs/composing-recipes.md)
- [Running locally](docs/running-locally.md)
- [Evaluations](docs/evaluations.md)
- [Manifest reference](docs/manifest-reference.md)
- [Roadmap](docs/roadmap.md)
- [Five-minute quick start](docs/quickstart.md)

## Project status

`v0.1.0` is the first public foundation release. The formats and CLI are usable, but breaking changes remain possible while real contribution patterns emerge.

This project is not a foundation model, training framework, prompt marketplace or claim that one model is universally best. It is an open structure for the layers that turn a base model into a useful, testable system.

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), and [SECURITY.md](SECURITY.md).

## Licence

Apache License 2.0. Individual datasets, integrations or contributed assets may carry additional clearly documented terms.

**Build a mod. Test it. Share it. Remix it.**
