# Contributing to Model Modding

Model Modding welcomes developers, domain experts, evaluators, educators, designers and writers.

## Before you start

1. Search existing issues and pull requests.
2. Keep each contribution focused on one problem.
3. Do not include secrets, private data, copyrighted datasets, or provider credentials.
4. For substantial format or governance changes, open an issue before implementation.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
modding doctor
modding validate
pytest
```

On Windows PowerShell use `.venv\Scripts\Activate.ps1`.

## Contributing a mod

Create the scaffold:

```bash
modding create mod example-mod --category personality --author "Your Name"
```

A mod pull request should include:

- a schema-valid `mod.yaml`;
- a narrow purpose and documented limitations;
- reusable instructions, not application-specific secrets;
- examples showing intended and unintended behaviour;
- evaluation cases with human-review expectations;
- machine-checkable assertions where they are honest and useful;
- dependency, conflict and compatibility declarations;
- confirmation that contributed content is licensed for this repository.

Run:

```bash
modding validate
pytest
```

## Pull requests

Keep commits understandable. Explain what changed, why it matters, how it was tested and any risks or limitations. Avoid unrelated formatting changes.

Automated checks must pass before merge. Review findings should be resolved or explicitly discussed.

## Evaluation claims

Do not describe a mod as universally better based on one model or a small deterministic suite. State the model, version, prompts, checks, limitations and observed regressions. Preserve full responses for human review.

## No-code contributions

Useful contributions include evaluation prompts, domain reviews, examples, documentation, translations, accessibility feedback and Requests for Mods.
