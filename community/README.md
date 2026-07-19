# Model Modding Community Hub

Model Modding grows through small, inspectable contributions. This hub connects real problems to contributors who can build, test, review or document solutions.

## Start here

1. Browse the [Requests for Mods](rfms/README.md).
2. Pick an unclaimed request or propose a new one.
3. Comment on the matching GitHub issue before starting substantial work.
4. Create the mod with `modding create mod`.
5. Add instructions, limitations, examples and evaluation cases.
6. Run `modding validate`, `modding doctor` and `pytest`.
7. Open a focused pull request.

## Contribution paths

You do not need to build the whole mod alone.

- **Mod creator:** packages the behaviour and manifest.
- **Domain reviewer:** checks accuracy, safety and usefulness.
- **Evaluator:** creates cases and regression checks.
- **Example writer:** supplies representative interactions.
- **Model tester:** compares behaviour across local models.
- **Designer or writer:** improves the Workshop, explanations and onboarding.

## Requests for Mods

A Request for Mod, or RFM, describes an unmet user need without prematurely prescribing the implementation. Each request includes intended users, desired behaviour, risks, acceptance criteria and suggested evaluation scenarios.

The first community requests are intentionally varied:

- RFM-001: Plain-language document explainer
- RFM-002: Child-safe learning companion
- RFM-003: Meeting decision recorder
- RFM-004: Evidence-aware health information guide
- RFM-005: Product discovery interviewer

See the [RFM index](rfms/README.md) for details.

## How a mod enters the catalogue

A merged mod is listed in the repository catalogue when it has:

- a valid manifest;
- clear purpose and limitations;
- reusable instructions or implementation;
- representative examples;
- evaluation cases;
- documented compatibility;
- an explicit maturity status.

Experimental mods are welcome. The status must reflect the evidence available, not ambition or popularity.

## Community standards

Keep discussion respectful, evidence visible and claims proportionate. Never include private data, proprietary prompts, credentials or restricted datasets. Follow the repository code of conduct and security policy.
