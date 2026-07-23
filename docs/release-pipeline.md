# v0.2 release evidence pipeline

Model Modding separates **pipeline readiness** from **provider compatibility evidence**. Synthetic CI fixtures prove that the machinery works. Only reviewed provider executions may support a compatibility or release claim.

## Pipeline stages

```text
Build and lock
  → execute exact provider/model runs
  → verify every evidence bundle
  → activate reviewed baselines where appropriate
  → compare baseline and candidate
  → aggregate repeated runs
  → build compatibility matrix
  → run v0.2 readiness checks
  → publish reviewed evidence
  → tag and release
```

## Repeated-run aggregation

Aggregate compatible evidence bundles:

```bash
modding aggregate-evidence \
  evidence/run-1 \
  evidence/run-2 \
  evidence/run-3 \
  --minimum-repetitions 3 \
  --require-zero-critical \
  --output build/aggregate
```

The inputs must share the exact recipe source and build digests, fixture-set digest and evaluator contract. The output contains:

```text
aggregate.json
aggregate.md
```

The report records repetitions, minimum case coverage, run pass/fail status, critical-free runs, failure totals, evidence digests and per-invariant observations for every exact provider/model target.

Repeated passing runs remain contextual evidence. They do not prove universal compatibility or semantic correctness.

## Scoped reviewed baselines

A baseline is activated only after its evidence bundle passes offline verification:

```bash
modding activate-baseline \
  evidence/candidate \
  evidence/baselines/trusted-document-explainer/current \
  --reviewer "Reviewer name or review group" \
  --scope "Exact CI or release scope" \
  --notes "Why this evidence was accepted"
```

The baseline directory contains:

```text
baseline.json
evidence/
```

`baseline.json` records a canonical baseline digest, reviewer, review scope, evidence digest, build identity, fixture set, evaluator and explicit limitations. Baseline acceptance never means that the provider or model is universally compatible.

## Pull-request evidence summaries

`modding evidence-summary` turns comparison, matrix, aggregate and readiness reports into one concise Markdown block:

```bash
modding evidence-summary \
  --comparison build/comparison/comparison.json \
  --matrix build/matrix/matrix.json \
  --aggregate build/aggregate/aggregate.json \
  --readiness build/readiness/readiness.json \
  --output build/pr-summary.md \
  --github-summary
```

`.github/workflows/evidence-pr-summary.yml` runs on every pull request. It:

- generates deterministic synthetic evidence;
- exercises reviewed-baseline activation, comparison, matrix, aggregation and release readiness;
- uploads all generated reports;
- appends a job summary;
- creates or updates one pull-request comment for same-repository branches.

The summary begins with an explicit synthetic-evidence warning. It is not real provider evidence.

## Protected cloud provider runs

`.github/workflows/provider-evidence.yml` is manual and uses the `provider-evidence` environment. Operators must configure:

- environment approval rules;
- `ANTHROPIC_API_KEY` and/or `OPENAI_API_KEY` environment secrets;
- `MODEL_MODDING_ALLOWED_MODELS` as a comma-separated repository or environment variable containing exact permitted model IDs.

The workflow restricts:

- provider to Anthropic or OpenAI;
- model to the explicit allowlist;
- repetitions to one, two or three;
- maximum output tokens to 256, 512 or 1024;
- the release fixture set to all 40 cases;
- concurrent runs for the same provider/model;
- total job time.

Every repetition uses `--fail-on none` so failures are recorded rather than discarded. Release readiness later requires zero critical failures.

## Protected Ollama runs

`.github/workflows/ollama-evidence.yml` runs only on a self-hosted runner carrying all of these labels:

```text
self-hosted
model-modding
ollama
```

Operators must configure `MODEL_MODDING_ALLOWED_OLLAMA_MODELS` and ensure the selected exact model is installed. The workflow uses the same repetition, token, evidence-verification, aggregation and artifact rules as the cloud workflow.

## Release-candidate evidence

Reviewed evidence bundles are committed under:

```text
evidence/release-candidate/<provider>/<model>/<repetition>/
```

Each leaf directory must be a complete, verified evidence bundle. Do not commit API keys, source prompt text or unreviewed scratch output.

Assemble the release candidate:

```bash
python scripts/assemble_release_evidence.py \
  --evidence-root evidence/release-candidate \
  --output build/release-candidate \
  --minimum-repetitions 3 \
  --minimum-cases 40
```

The assembler verifies every bundle, groups repeated exact targets, selects one representative run per target for the matrix, creates the repeated aggregate, builds the compatibility matrix and runs the release-readiness gate.

## v0.2 readiness gate

The equivalent direct command is:

```bash
modding release-check \
  --aggregate build/release-candidate/aggregate/aggregate.json \
  --matrix build/release-candidate/matrix/matrix.json \
  --minimum-repetitions 3 \
  --minimum-cases 40 \
  --output build/release-candidate/readiness
```

The gate requires:

- matching recipe, build, fixture-set and evaluator identities;
- Ollama, Anthropic and OpenAI coverage;
- at least three repetitions for every exact target;
- at least 40 cases in every repetition;
- zero critical failures;
- passing matrix target status.

A failed check produces `not_ready` and a non-zero exit code.

## Release enforcement

`.github/workflows/release-evidence.yml` runs when checked-in release-candidate evidence changes and uploads the assembled reports.

`.github/workflows/release.yml` applies an additional rule to `v0.2*` tags: the tag cannot be released unless the checked-in evidence passes the complete readiness gate. The package version must also exactly match the tag.

## What remains human

Automation cannot truthfully replace:

- provider credentials and paid execution approval;
- review of raw model responses and limitations;
- domain review for high-stakes claims;
- approval of the first authoritative baseline;
- independent reproduction by someone outside the originating implementation path.

The pipeline records and enforces those boundaries rather than pretending they have already happened.
