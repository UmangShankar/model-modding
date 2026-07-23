# Reviewed evidence baselines

A baseline is a verified evidence bundle accepted for one explicit comparison scope.

Use `modding activate-baseline` rather than copying files manually:

```bash
modding activate-baseline \
  evidence/candidate \
  evidence/baselines/trusted-document-explainer/<target> \
  --reviewer "Reviewer or review group" \
  --scope "Exact comparison scope" \
  --notes "Review decision and limitations"
```

Each baseline contains:

```text
baseline.json
evidence/
```

The embedded bundle remains authoritative. Baseline acceptance does not establish universal compatibility, does not replace domain review and is invalid for comparisons with a different build, fixture set, evaluator or provider/model target.

Synthetic CI contract baselines are generated under build artifacts and must not be presented as provider evidence.
