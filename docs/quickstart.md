# Five-minute quick start

This quick start exercises the current development line using the flagship `trusted-document-explainer` recipe.

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

Ollama and cloud SDKs are optional for repository validation. `doctor` can report release readiness while warning that local or cloud runtimes are not configured.

## 3. Inspect the transformation and assurance contract

```bash
modding inspect plain-language-explainer
modding inspect deadline-guardian
```

Inspection includes roles, capabilities, compatible-model declarations, preserved invariants, prohibited transformations, instruction files and evaluation-case counts.

Windows-style references are accepted:

```powershell
modding inspect domain\plain-language-explainer
```

Generated references remain canonical POSIX paths such as `domain/plain-language-explainer`.

## 4. Compose the flagship recipe

```bash
modding compose trusted-document-explainer
```

Composition writes the compiled prompt and legacy composition metadata under `build/trusted-document-explainer/`.

## 5. Build and lock the flagship recipe

Use an empty output directory for the reproducible bundle:

```bash
modding build trusted-document-explainer --output /tmp/tde-build
```

The build contains:

```text
/tmp/tde-build/
├── system.md
├── recipe.lock.json
├── abom.json
├── abom.md
└── manifest.json
```

It records the build engine, schema versions, ordered behavioural sources, component hashes, declared invariants, source digest, compiled-prompt digest and build digest. No model is called.

Verify it byte-for-byte against the current repository:

```bash
modding verify-build trusted-document-explainer \
  --build-directory /tmp/tde-build
```

A successful verification ends with `Build verified`. Editing an instruction, manifest or generated artifact makes verification fail.

## 6. Run it locally with Ollama

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

Review the response carefully. A valid lock and ABOM prove which behavioural inputs were built; they do not prove that the model followed them.

## 7. Inspect the evaluation plan

```bash
modding evaluate trusted-document-explainer \
  --model llama3.2 \
  --dry-run
```

This lists the 40 cases without calling the model.

## 8. Run the evaluation

```bash
modding evaluate trusted-document-explainer \
  --model llama3.2 \
  --fail-on critical
```

The command writes:

```text
build/evaluations/trusted-document-explainer/
├── report.json
└── report.md
```

The current evaluator includes:

- stock and modded responses;
- legacy deterministic checks;
- manifest-bound invariant checks;
- structured source-output comparisons;
- critical, major and minor failures;
- pipeline status and blocking failures;
- latency and response word counts;
- per-response provider execution metadata on the provider-aware path.

These checks are transparent regression signals. They do not provide unrestricted semantic proof.

## 9. Use another provider

Install cloud extras only when needed:

```bash
python -m pip install -e ".[anthropic,openai]"
```

Then configure the relevant environment variable and supply `--provider` with an exact model identifier. Cloud calls may incur cost. Adapter availability alone is not a compatibility claim.

## 10. Compare installed local models

```bash
modding benchmark trusted-document-explainer \
  --models llama3.2,qwen2.5:3b
```

This writes a local fitment benchmark under:

```text
build/benchmarks/trusted-document-explainer/
```

A result means only that the specified models were evaluated against the identified recipe and cases. It is not a universal model ranking.

## 11. Run the test suite

```bash
pytest
```

Pull-request CI also builds and verifies the flagship bundle from both the editable installation and a clean wheel installation.

You are now ready to read [Reproducible builds, recipe locks and ABOMs](reproducible-builds.md), inspect the [v0.2 roadmap](roadmap.md), review the [flagship product contract](trusted-document-explainer-contract.md), or contribute through the [community hub](../community/README.md).
