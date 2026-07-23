# Independently reproduce the v0.2 flagship evidence

This guide is for a developer who was not responsible for producing the original release-candidate evidence.

## Objective

Reproduce the Trusted Document Explainer evidence for one or more exact provider/model targets without changing the recipe, mods, fixtures or evaluator.

A successful reproduction must preserve:

- the recipe source and build digests;
- the 40-case fixture-set digest;
- the evaluator identity;
- the exact provider and returned model;
- requested and effective generation settings;
- raw responses and evidence hashes;
- all reported failures and limitations.

## Prepare

```bash
git clone https://github.com/UmangShankar/model-modding.git
cd model-modding
git checkout <release-tag-or-reviewed-commit>
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,anthropic,openai]"
modding validate
modding doctor
```

For local Ollama, install the exact reviewed model ID. For Anthropic or OpenAI, configure the relevant API key in your own environment.

## Verify the behavioural build

```bash
modding build trusted-document-explainer --output build/reproduction/build
modding verify-build trusted-document-explainer --build-directory build/reproduction/build
```

Record the build digest from `recipe.lock.json`. It must match the reviewed release evidence.

## Execute three complete repetitions

Run the exact provider, model and settings documented by the release evidence. Example:

```bash
for repetition in 1 2 3; do
  modding evaluate trusted-document-explainer \
    --provider <provider> \
    --model <exact-model-id> \
    --temperature 0 \
    --max-tokens <reviewed-limit> \
    --fail-on none \
    --evidence "build/reproduction/run-$repetition" \
    --output "build/reproduction/report-$repetition"
  modding verify-evidence "build/reproduction/run-$repetition"
done
```

Do not edit raw responses or evaluator output after execution.

## Aggregate

```bash
modding aggregate-evidence \
  build/reproduction/run-1 \
  build/reproduction/run-2 \
  build/reproduction/run-3 \
  --minimum-repetitions 3 \
  --require-zero-critical \
  --output build/reproduction/aggregate
```

## Compare with reviewed evidence

Use the exact reviewed baseline for that provider/model:

```bash
modding compare-evidence \
  evidence/baselines/trusted-document-explainer/<target>/evidence \
  build/reproduction/run-1 \
  --fail-on critical \
  --output build/reproduction/comparison
```

A non-comparable result means the build, fixture set, evaluator or target identity differs and the reproduction cannot support the release claim.

## Submit reproduction evidence

Provide:

- operating system and Python version;
- exact repository commit or tag;
- provider and exact model;
- generation settings;
- build digest;
- three evidence digests;
- aggregate digest;
- comparison digest;
- all failures and limitations;
- confirmation that no behavioural source or fixture was modified.

Submit the evidence through a pull request under a clearly named reproduction directory. Do not include API keys or private source documents.

## Interpretation boundary

Matching the encoded evidence supports reproducibility of this exact test contract. It does not certify legal, medical or universal semantic correctness and does not remove the need for domain review.
