# Model Modding Workshop

The Workshop is a zero-dependency, zero-API-key visual demonstration of Model Modding.

Open `workshop/index.html` directly in a browser, or serve the repository locally:

```bash
python -m http.server 8000
```

Then visit `http://localhost:8000/workshop/`.

## What it demonstrates

- browsing the current reference mods
- selecting ready-made recipes
- assembling a custom build
- seeing installed capabilities and behavioural rules
- live deterministic prompt compilation
- fitment warnings for potentially overlapping behaviours
- copying or downloading the compiled Markdown contract

The page intentionally does not call a model provider. The Model Modding CLI remains the source of truth for production recipe composition:

```bash
modding inspect socratic-teacher
modding compose research-learning-companion
```

## Current limitation

The Workshop data is embedded in the static page for a frictionless prototype. A future version should generate its catalogue from repository manifests so the visual interface and CLI share one contract automatically.
