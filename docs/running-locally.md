# Running locally

Model Modding integrates with Ollama using Python's standard HTTP library.

Install Ollama separately, pull a model and start its service:

```bash
ollama pull llama3.2
ollama serve
```

Run a recipe:

```bash
modding run research-learning-companion \
  --model llama3.2 \
  --prompt "Explain compound interest to a beginner"
```

The default host is `http://127.0.0.1:11434`. Non-loopback hosts are rejected unless `--allow-remote-host` is supplied deliberately. Review the endpoint's privacy and authentication before opting in.

For a browser comparison:

```bash
python -m http.server 8000
```

Open `http://localhost:8000/workshop/local.html`. The Local Dyno sends the same prompt to stock and modded configurations and calls only the loopback Ollama endpoint.
