# Non-goals

Model Modding has a deliberately narrow product boundary.

## Not a training framework

Model Modding does not train, fine-tune or modify model weights. It packages the behavioural layer applied around an existing model.

## Not an agent-orchestration platform

The project does not aim to replace workflow engines, multi-agent frameworks, tool routers, memory systems or application runtimes. Those systems may consume a Model Modding build, but they are not the product.

## Not a prompt marketplace

The repository is not a catalogue of opaque prompts ranked by popularity. Behavioural packages should expose their instructions, dependencies, limitations, evaluation cases and evidence.

## Not generic observability

Model Modding records the evidence required to understand and reproduce a behavioural build. It does not attempt to become a general-purpose tracing, telemetry or production-monitoring platform.

## Not proof that prompts guarantee behaviour

A system prompt cannot guarantee that a model will preserve meaning or follow every instruction. Declared invariants are requirements to evaluate, not certificates of compliance.

## Not a universal model leaderboard

Compatibility claims must remain attached to a specific provider, model, recipe digest, evaluator, fixture set, generation configuration and date.

The framework must not convert contextual evidence into a claim that one model is universally best.

## Not a replacement for domain review

Automated checks and optional model judges do not replace legal, medical, operational or other specialist review.

High-stakes maturity claims require appropriate human assessment and honest publication of failures and limitations.

## Not formal certification

ABOMs, digests and evidence bundles improve transparency and reproducibility. They do not constitute regulatory approval, legal assurance or formal certification.

## Not in the v0.2 programme

The current fast-track programme explicitly defers:

- hosted SaaS;
- user accounts and billing;
- enterprise dashboards;
- registry marketplaces;
- visual recipe authoring;
- broad agent orchestration;
- fine-tuning;
- Bedrock and Vertex providers;
- universal leaderboards;
- formal certification;
- automated prompt optimisation.

These items may be reconsidered only after the portable assured behaviour proof is credible and independently reproducible.
