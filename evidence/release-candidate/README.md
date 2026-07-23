# Reviewed v0.2 release-candidate evidence

Only reviewed, complete evidence bundles belong here.

Use this layout:

```text
<provider>/<exact-model-safe-name>/run-1/
<provider>/<exact-model-safe-name>/run-2/
<provider>/<exact-model-safe-name>/run-3/
```

Each `run-*` directory must contain a verified evaluation evidence bundle:

```text
manifest.json
responses.jsonl
recipe.lock.json
abom.json
evaluation.json
```

Requirements:

- the exact same locked Trusted Document Explainer build;
- the complete 40-case fixture set;
- evaluator contract `deterministic-source-invariant-evaluator`;
- exact provider and returned model identity;
- three repetitions per release target;
- raw responses reviewed for publication;
- no API keys or private prompt text;
- limitations documented honestly.

Synthetic CI evidence must never be copied here. Provider workflow artifacts must be reviewed before being committed.

The v0.2 release workflow assembles this directory and blocks release unless Ollama, Anthropic and OpenAI evidence satisfies all readiness gates.
