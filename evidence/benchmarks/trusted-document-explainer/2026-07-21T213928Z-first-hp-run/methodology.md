# Trusted Document Explainer benchmark methodology

## Purpose

This run evaluates whether the trusted-document-explainer recipe improves two small local Ollama models across the repository's eleven evaluation cases.

It compares stock and modded responses while also testing local execution, deterministic checks, latency capture, evidence generation and repeatability. It does not establish universal model quality.

## Recipe and cases

- Recipe: `trusted-document-explainer`
- Mods: `domain/plain-language-explainer` and `safety/citation-guardian`
- Evaluation cases per model: 11
- Stock and modded calls per model: 22
- Total completed model calls: 44
- Model Modding commit: `3ec2db8a91b411f12b490a6656461148bc917a5d`
- Windows patch fingerprint: `8754901ddb7fa23965fcccc19673d78c7dbeda82`
- Benchmark date: 21 July 2026

The benchmark used the recorded commit plus an uncommitted Windows path-normalisation patch in `src/model_modding/cli.py`. Without the patch, evaluation failed when backslash-separated mod references were resolved on Windows.

The working tree was not clean. It also contained a case-collision-related change to `.github/pull_request_template.md` and generated build, benchmark, cache and editable-install artefacts.

## Models

| Requested selector | Resolved tag | Ollama ID | Size |
| --- | --- | --- | --- |
| `llama3.2` | `llama3.2:latest` | `a80c4f17acd5` | 2.0 GB |
| `qwen2.5:3b` | `qwen2.5:3b` | `357c53fb659c` | 1.9 GB |

Mistral was not benchmarked because human review found material accuracy and hallucination problems in both initial models.

## Procedure

1. Confirm the repository location, branch, remote and full commit SHA.
2. Create and activate a repository-local virtual environment.
3. Install the package in editable mode with development dependencies.
4. Run the test suite. The patched tree completed 59 tests successfully.
5. Run repository validation, doctor, recipe inspection and composition.
6. Confirm Ollama availability and exact installed model tags.
7. Run a basic generation test with each model.
8. Run standalone stock-versus-modded evaluations.
9. Review complete responses against expected behaviours and failure indicators.
10. Run the two-model benchmark without editing the recipe or cases between models.
11. Preserve the generated benchmark JSON and Markdown reports unchanged.
12. Verify that all 44 result records contain responses, outcomes, checks, latency and word counts.
13. Record operating system, hardware, runtime and model metadata.

Benchmark command:

`modding benchmark trusted-document-explainer --models "llama3.2,qwen2.5:3b" --output "evidence\benchmarks\trusted-document-explainer\first-hp-run"`

## Human review

The deterministic benchmark reported 5/11 stock and 7/11 modded for Llama 3.2, and 5/11 stock and 6/11 modded for Qwen 2.5 3B.

Several deterministic results were misleading.

For Llama 3.2, incomplete-source was a credible improvement. The legal-jargon result was a false improvement because the response retained required keywords while incorrectly explaining several liability. The fact-versus-inference result was also a false improvement because the model treated system instructions as user evidence. The conflicting-sources case was a genuine regression involving invented study details.

For Qwen 2.5 3B, unsupported-statistic was a credible improvement. The remote-work result added unsupported equipment, approval, productivity, HR and work-life-balance claims. The conflicting-sources case was a genuine regression involving fabricated citation placeholders.

Standalone evaluations also produced materially different totals from the benchmark:

- Llama standalone: 6/11 stock and 4/11 modded
- Llama benchmark: 5/11 stock and 7/11 modded
- Qwen standalone: 3/11 stock and 7/11 modded
- Qwen benchmark: 5/11 stock and 6/11 modded

These differences show that one deterministic run is not sufficiently repeatable for strong compatibility claims.

## Redactions

None. Model responses and deterministic outcomes were preserved unchanged.

Environment metadata omits usernames, hostnames, secrets and personal filesystem paths. This does not change any benchmark result.

## Limitations

- Deterministic keyword checks are proxies and do not establish semantic correctness.
- Some passing responses contained contradictions, invented actions or incorrect explanations.
- Some safe responses failed because they did not use preferred evaluator phrases.
- Generation behaviour was not demonstrated to be deterministic across repeated runs.
- The evidence does not record a fixed sampling seed or prove that sampling parameters were controlled.
- A single local run cannot establish general compatibility.
- Results depend on model version, runtime, hardware, prompt composition and sampling behaviour.
- Latency comparisons are valid only within the recorded HP EliteBook environment.
- Python 3.14.4 worked and all 59 tests passed, although the observed project classifiers listed Python 3.10, 3.11 and 3.12.
- Evaluation and benchmarking required an uncommitted Windows path compatibility patch.
- Top-level CLI help did not advertise the working doctor and benchmark commands.
- Standalone evaluation reports omitted latency and word counts, while benchmark reports included them.
- No larger Mistral model was tested.

## Conclusion

The repository can be installed, validated, tested and benchmarked locally on Windows after applying a small path-normalisation patch. Both requested Ollama models completed every planned benchmark call.

The evidence does not support claiming that the current recipe reliably improves either model. Both models produced unsupported additions, incorrect interpretations or fabricated source details after modification.

The result is technically executable but requires material behavioural, evaluator and reproducibility improvements before compatibility claims are published.
