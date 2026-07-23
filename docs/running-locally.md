# Running locally

Ollama is the default local provider and uses Python's standard HTTP library. Reproducible recipe builds require no model process or network access.

## Install and diagnose

```bash
python -m pip install -e ".[dev]"
modding validate
modding doctor
```

## Build before execution

Create a deterministic bundle for the recipe:

```bash
modding build trusted-document-explainer --output /tmp/tde-build
modding verify-build trusted-document-explainer \
  --build-directory /tmp/tde-build
```

The bundle contains the runtime-equivalent compiled system prompt, recipe lock, JSON and Markdown ABOM, and artifact manifest. Verification is offline and compares every managed artifact byte-for-byte.

The lock identifies the ordered behavioural sources and build engine that produced the prompt. It does not identify a provider or prove that a model will comply.

## Start Ollama

Install Ollama separately, pull a model and start its service:

```bash
ollama pull llama3.2
ollama serve
```

Run a recipe:

```bash
modding run trusted-document-explainer \
  --model llama3.2 \
  --prompt "Explain this notice without changing its deadline or exception."
```

The default host is `http://127.0.0.1:11434`. Non-loopback hosts are rejected unless `--allow-remote-host` is supplied deliberately. Review the endpoint's privacy and authentication before opting in.

## Evaluate locally

```bash
modding evaluate trusted-document-explainer \
  --model llama3.2 \
  --fail-on critical
```

The evaluator applies the encoded deterministic invariant and source-comparison checks. It does not perform unrestricted semantic extraction, so high-stakes outputs still require appropriate review.

## Browser comparison

```bash
python -m http.server 8000
```

Open `http://localhost:8000/workshop/local.html`. The Local Dyno sends the same prompt to stock and modded configurations and calls only the loopback Ollama endpoint.

See [Reproducible builds, recipe locks and ABOMs](reproducible-builds.md) for canonicalisation, digest and verification details.
