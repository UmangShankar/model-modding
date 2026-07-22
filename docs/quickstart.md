# Five-minute quick start

This quick start exercises the current v0.1.1 foundation using the flagship `trusted-document-explainer` recipe.

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

## 2. Validate and diagnose the repository

```bash
modding validate
modding doctor
```

A healthy repository ends validation with:

```text
All manifests are valid.
```

Ollama is optional for repository validation, so `doctor` can report the release foundation as ready while warning that no local runtime is available.

## 3. Inspect the transformation mod

```bash
modding inspect plain-language-explainer
```

You will see its version, status, capabilities, compatibility declarations, instruction files and evaluation-case count.

Windows-style references are also accepted:

```powershell
modding inspect domain\plain-language-explainer
```

Generated references remain canonical POSIX paths such as `domain/plain-language-explainer`.

## 4. Compose the flagship recipe

```bash
modding compose trusted-document-explainer
```

The current compiler writes:

```text
build/trusted-document-explainer/
├── system.md
└── manifest.json
```

The v0.2 roadmap expands this build into a locked, checksummed package with an ABOM. Those outputs do not exist in v0.1.1 yet.

## 5. Run it locally with Ollama

Install Ollama separately and pull a local model, for example:

```bash
ollama pull llama3.2
```

Then run the recipe:

```bash
modding run trusted-document-explainer \
  --model llama3.2 \
  --prompt "Explain this in plain English without losing deadlines, conditions, exceptions or obligations: The applicant shall submit the requested evidence within 14 calendar days of this notice, except where exceptional circumstances prevent compliance."
```

The default endpoint is `http://127.0.0.1:11434`. Use `--host` for another endpoint. Non-loopback hosts require the explicit `--allow-remote-host` safety flag.

Review the response carefully. The current recipe and evaluator are experimental and the first published benchmark found material meaning and grounding failures.

## 6. Inspect the evaluation plan

```bash
modding evaluate trusted-document-explainer \
  --model llama3.2 \
  --dry-run
```

This lists the cases without calling the model.

## 7. Run the evaluation

```bash
modding evaluate trusted-document-explainer \
  --model llama3.2
```

The command writes:

```text
build/evaluations/trusted-document-explainer/
├── report.json
└── report.md
```

The report includes:

- stock and modded responses;
- deterministic check results;
- latency;
- response word counts;
- improvements and regressions;
- expected behaviours and failure indicators for human review.

Deterministic checks are transparent regression signals. They do not prove that material meaning was preserved.

## 8. Compare installed local models

```bash
modding benchmark trusted-document-explainer \
  --models llama3.2,qwen2.5:3b
```

This writes a local fitment benchmark under:

```text
build/benchmarks/trusted-document-explainer/
```

A result means only that the specified models were evaluated against the same current recipe and cases. It is not a universal model ranking.

## 9. View the local tools

Serve the repository:

```bash
python -m http.server 8000
```

Then open:

- `http://localhost:8000/workshop/`
- `http://localhost:8000/workshop/local.html`
- `http://localhost:8000/workshop/scorecard.html`
- `http://localhost:8000/workshop/fitment.html`

## 10. Run the test suite

```bash
pytest
```

You are now ready to inspect the [v0.2 roadmap](roadmap.md), read the [flagship product contract](trusted-document-explainer-contract.md), or contribute through the [community hub](../community/README.md).
