# Benchmark methodology

## Purpose

State the question this run is intended to answer.

## Recipe and cases

- Recipe: `REPLACE_ME`
- Evaluation case count: `REPLACE_ME`
- Model Modding commit: `REPLACE_ME`

## Models

List the requested selector, resolved Ollama tag and model digest when available.

## Procedure

1. Validate the repository with `modding validate`.
2. Confirm local readiness with `modding doctor`.
3. Run the benchmark command once without editing cases between models.
4. Preserve generated JSON and Markdown reports unchanged.
5. Review complete responses against expected behaviours and failure indicators.
6. Record any redaction without changing deterministic results.

## Human review

Describe who reviewed the responses, which cases required judgement and whether the deterministic checks were misleading in either direction.

## Redactions

State `None` or describe each redaction and why it was necessary. Never replace a failed result with a rewritten response.

## Limitations

Cover at least:

- deterministic checks are proxies rather than universal quality measures;
- results depend on model version, runtime, hardware and sampling behaviour;
- a single local run does not establish general compatibility;
- latency comparisons are valid only within the recorded environment.

## Conclusion

Summarise only what the evidence supports. Avoid claims that one model is universally best.
