# Evaluations

Evaluation cases live under each mod's `evaluations/` directory. They can contain:

- an input prompt;
- expected behaviours for human review;
- failure indicators;
- transparent deterministic checks.

Inspect a plan without calling a model:

```bash
modding evaluate research-learning-companion --model llama3.2 --dry-run
```

Run stock and modded comparisons:

```bash
modding evaluate research-learning-companion --model llama3.2
```

Reports are written under `build/evaluations/<recipe>/` as JSON and Markdown. They include complete responses, per-check results, per-mod summaries, improvements and regressions.

Keyword, question-count and length checks are useful for repeatable regression detection, but they cannot prove pedagogical quality, factual correctness or safety. Review full outputs and the human rubric before making claims.
