# Five-minute quick start

## 1. Clone and install

```bash
git clone https://github.com/UmangShankar/model-modding.git
cd model-modding
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

## 2. Validate the repository

```bash
modding validate
```

A healthy repository ends with:

```text
All manifests are valid.
```

## 3. Inspect and compose a build

```bash
modding inspect socratic-teacher
modding compose research-learning-companion
```

The compiled system contract and manifest are written under `build/research-learning-companion/`.

## 4. Run it locally with Ollama

Install Ollama separately and pull a local model, for example:

```bash
ollama pull llama3.2
```

Then run the recipe:

```bash
modding run research-learning-companion \
  --model llama3.2 \
  --prompt "Explain compound interest to a beginner"
```

The default endpoint is `http://127.0.0.1:11434`. Use `--host` for another endpoint. Non-loopback hosts require the explicit `--allow-remote-host` safety flag.

For a visual stock-versus-modded comparison, serve the repository and open the Local Dyno:

```bash
python -m http.server 8000
```

Visit `http://localhost:8000/workshop/local.html`.

## 5. Create your first mod

```bash
modding create mod my-first-mod \
  --category personality \
  --author "Your Name" \
  --github your-github-username
```

This creates:

```text
mods/personality/my-first-mod/
├── mod.yaml
├── README.md
├── instructions/system.md
├── examples/README.md
└── evaluations/cases.yaml
```

The command refuses invalid names and will not overwrite an existing mod.

## 6. Edit and validate

Describe the mod in `mod.yaml`, add its reusable instructions and write evaluation cases. Then run:

```bash
modding validate
```

## 7. Run the test suite

```bash
pytest
```

You are now ready to open a pull request.
