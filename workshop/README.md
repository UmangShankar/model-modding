# Model Modding Workshop

The Workshop now has two browser experiences:

- `workshop/index.html` — a zero-dependency visual prompt-composition demo
- `workshop/local.html` — a real stock-versus-modded comparison using a local Ollama model

Serve the repository locally:

```bash
python -m http.server 8000
```

Then visit:

- `http://localhost:8000/workshop/`
- `http://localhost:8000/workshop/local.html`

## Static Workshop

The main Workshop demonstrates:

- browsing the current reference mods
- selecting ready-made recipes
- assembling a custom build
- seeing installed capabilities and behavioural rules
- live deterministic prompt compilation
- fitment warnings for potentially overlapping behaviours
- copying or downloading the compiled Markdown contract

## Local Dyno

The Local Dyno connects only to `http://127.0.0.1:11434` and provides:

- detection of the local Ollama service
- discovery of installed models
- Product Strategy Copilot and Research Learning Companion builds
- the same prompt sent to stock and modded configurations
- side-by-side response comparison
- no cloud API keys or remote analytics

Install Ollama separately, pull a model, and start its service. For example:

```bash
ollama pull llama3.2
ollama serve
```

Browser access should use the local HTTP server command above rather than opening `local.html` directly from `file://`, because browser security rules may block local API requests from file pages.

## CLI source of truth

The Model Modding CLI remains the production source of truth for composition and local execution:

```bash
modding inspect socratic-teacher
modding compose research-learning-companion
modding run research-learning-companion \
  --model llama3.2 \
  --prompt "Explain compound interest to a beginner"
```

A custom Ollama endpoint can be supplied with `--host`. Non-loopback endpoints are rejected unless `--allow-remote-host` is explicitly provided.

## Current limitation

Workshop recipe data is embedded for a frictionless prototype. A future version should generate its catalogue and local runner contracts from repository manifests so the visual interface and CLI share one automatically generated source.
