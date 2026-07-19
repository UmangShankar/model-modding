# Model Modding Workshop

The Workshop now has four browser experiences:

- `workshop/index.html` — a zero-dependency visual prompt-composition demo
- `workshop/local.html` — a real stock-versus-modded comparison using a local Ollama model
- `workshop/scorecard.html` — a local visualiser for CLI-generated evaluation reports
- `workshop/fitment.html` — a local model-by-model compatibility matrix

Serve the repository locally:

```bash
python -m http.server 8000
```

Then visit:

- `http://localhost:8000/workshop/`
- `http://localhost:8000/workshop/local.html`
- `http://localhost:8000/workshop/scorecard.html`
- `http://localhost:8000/workshop/fitment.html`

## Static Workshop

The main Workshop demonstrates browsing mods, selecting recipes, assembling a build, inspecting behavioural rules and downloading compiled contracts.

## Local Dyno

The Local Dyno connects only to `http://127.0.0.1:11434`, discovers installed models and sends the same prompt to stock and modded configurations. It uses no cloud API keys or analytics.

## Dyno Scorecard

Generate an evaluation report:

```bash
modding evaluate research-learning-companion --model llama3.2
```

Load `build/evaluations/research-learning-companion/report.json` in `scorecard.html`.

## Model Fitment Matrix

Run the same recipe and evaluation suite across multiple installed Ollama models:

```bash
modding benchmark trusted-document-explainer \
  --models llama3.2,qwen2.5:3b,mistral
```

The command writes:

```text
build/benchmarks/trusted-document-explainer/
├── benchmark.json
└── benchmark.md
```

Load `benchmark.json` in `fitment.html`. The matrix shows availability, stock and modded pass rates, improvement, regressions and average latency. Reports remain local to the browser.

## CLI source of truth

```bash
modding inspect socratic-teacher
modding compose research-learning-companion
modding run research-learning-companion --model llama3.2 --prompt "Explain compound interest"
modding evaluate research-learning-companion --model llama3.2
modding benchmark trusted-document-explainer --models llama3.2,qwen2.5:3b
```

Custom Ollama endpoints require `--allow-remote-host` when they are not loopback addresses.
