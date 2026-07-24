# Version and release status

Model Modding separates the **published package version**, the **capabilities implemented on `main`**, and an **evidence-backed release claim**.

## Current state

| State | Version or branch | Meaning |
| --- | --- | --- |
| Current package version | `0.1.1` | The version declared in `pyproject.toml` and the latest completed release entry in the changelog. |
| Current development state | `main` | Contains the engineering delivered through roadmap increments `v0.1.2` to `v0.1.7`, including invariants, three provider adapters, reproducible builds, durable evidence, comparison, repeated-run aggregation and release gates. |
| Next evidence-backed release | `v0.2.0` | Must not be published until reviewed Ollama, Anthropic and OpenAI evidence, baseline approval, the public case study and independent reproduction satisfy the enforced release contract. |

The repository therefore remains versioned as `0.1.1` while the v0.2 evidence operations are completed. This is deliberate: implemented machinery is not the same as reviewed provider compatibility evidence.

## How to describe the project today

Accurate wording:

> Model Modding 0.1.1 is the current package version. The `main` branch contains the complete v0.1.7 engineering pipeline for portable assured behaviour. v0.2.0 remains evidence-gated pending reviewed three-provider runs and independent reproduction.

Do not describe:

- roadmap increments `v0.1.2` to `v0.1.7` as separately published releases unless corresponding releases are deliberately created;
- adapter availability or synthetic CI evidence as provider compatibility;
- the repository as v0.2-ready merely because the release-readiness machinery passes synthetic contract fixtures;
- `v0.2.0` as released before the checked-in reviewed evidence passes the tag-time gate.

## What is already implemented on `main`

- machine-readable invariants and four narrow assurance guardians;
- exactly 40 Trusted Document Explainer cases and 23 typed source facts;
- provider-neutral execution with Ollama, Anthropic and OpenAI adapters;
- deterministic recipe builds, locks and Agent Behaviour Bills of Materials;
- durable raw-response evidence and offline verification;
- strict evidence comparison and compatibility matrices;
- repeated-run aggregation and scoped reviewed baselines;
- protected provider workflows and automatic pull-request contract summaries;
- release-candidate assembly and a v0.2 tag-publication gate.

## What still blocks v0.2.0

The remaining work is operational evidence, not missing release-pipeline engineering:

- configure protected environments, secrets, exact model allowlists and the Ollama runner;
- execute and review three complete 40-case repetitions for Ollama, Anthropic and OpenAI;
- approve the first authoritative scoped baseline;
- commit reviewed release-candidate evidence;
- publish the case study with failures and limitations;
- complete independent reproduction.

The live checklist is tracked in [Issue #36](https://github.com/UmangShankar/model-modding/issues/36).

## Version changes

Do not change `pyproject.toml` from `0.1.1` solely because additional engineering exists on `main`. Update the package version only as part of a deliberate release decision with matching changelog, tag and release evidence.

For v0.2, the package version and Git tag must match exactly, and the protected release workflow must pass before publication.
