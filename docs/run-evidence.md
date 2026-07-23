# Durable run evidence bundles

A run evidence bundle records one provider execution context and binds it to the exact behavioural build that produced the request instructions.

Evidence is available on provider-aware commands:

```bash
modding run trusted-document-explainer \
  --provider ollama \
  --model llama3.2 \
  --prompt "Explain this notice" \
  --evidence build/evidence/single-run
```

```bash
modding evaluate trusted-document-explainer \
  --provider ollama \
  --model llama3.2 \
  --fail-on critical \
  --evidence build/evidence/evaluation-run
```

```bash
modding benchmark trusted-document-explainer \
  --provider ollama \
  --models llama3.2,qwen2.5:3b \
  --evidence build/evidence/benchmark-run
```

## Bundle layout

A single-run bundle contains:

```text
manifest.json
responses.jsonl
recipe.lock.json
abom.json
```

Evaluation and benchmark bundles also contain:

```text
evaluation.json
```

`responses.jsonl` is the authoritative raw-response artifact. Each record includes:

- a stable record identifier and stock or modded role;
- prompt and system-prompt SHA-256 values;
- the exact raw model response and its SHA-256;
- provider and exact returned model;
- requested and effective generation settings;
- latency, finish reason and token usage;
- provider-labelled response metadata;
- case and mod identity when applicable.

## Build identity

Every bundle embeds the exact `recipe.lock.json` and `abom.json` generated from the current behavioural sources. The evidence manifest records:

- recipe name and version;
- source digest;
- build digest;
- recipe-lock digest;
- ABOM digest.

This prevents an execution result from being detached from the mod versions, instruction bytes, composition order and declared invariants that produced it.

## Prompt privacy

Source prompt text is omitted by default. The bundle records a prompt hash instead.

This reduces accidental copying of notices, policies, clauses or other potentially sensitive source documents into evidence. The exact response text is retained because it is the primary execution artifact.

Prompt hashes prove identity only when the verifier has the original prompt. They do not make a low-entropy prompt secret and are not a substitute for access controls.

## Raw execution and interpreted evaluation

Raw responses and interpreted evaluation are separate artifacts.

`responses.jsonl` retains the original model outputs. `evaluation.json` contains evaluator results with prompt and response text removed. A future evaluator can therefore analyse the preserved raw responses without rewriting or replacing the original execution record.

## Manifest identity

`manifest.json` records:

- evidence schema and engine versions;
- bundle type and UTC creation time;
- evidence digest;
- build identity;
- provider, endpoint description, requested models and options;
- evaluator and fixture-set digest where applicable;
- source-control commit and dirty-tree state when available;
- privacy declarations;
- artifact hashes and byte counts;
- known limitations.

API-key values are never included. Provider adapters may report only whether authentication is configured.

## Offline verification

```bash
modding verify-evidence build/evidence/evaluation-run
```

Verification does not call a model provider. It checks:

- manifest schema validity;
- evidence-digest reconstruction;
- every artifact SHA-256 and byte count;
- response count and response-text hashes;
- absence of prompt text fields in raw records;
- recipe-lock build-digest validity;
- agreement between the manifest, lock and ABOM;
- missing or unexpected artifacts.

## What a bundle does not prove

A valid bundle proves that its recorded files and internal hashes agree. It does not prove:

- that the model response is correct or safe;
- that every material meaning change was detected;
- that a provider or model is universally compatible;
- that source-control state was available in every environment;
- that a prompt hash can replace the original source for human review.

Compatibility and regression claims require explicit comparison rules, reviewed evidence and exact provider, model, fixture and generation context. Those comparison capabilities remain the next v0.1.7 increment.
