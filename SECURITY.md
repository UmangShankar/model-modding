# Security Policy

## Supported versions

Security fixes are applied to the latest release and the `main` branch.

## Reporting a vulnerability

Do not open a public issue for a vulnerability that could expose credentials, private data, arbitrary files, remote systems or unsafe execution paths.

Report the issue privately to the repository owner through GitHub. Include:

- affected version or commit;
- reproduction steps;
- expected and observed impact;
- suggested mitigation, when known;
- whether the issue has been disclosed elsewhere.

Please avoid accessing data that is not yours and do not include real secrets in a report.

## Security boundaries

Model Modding packages behavioural instructions and can call model runtimes. Contributors and users should treat third-party mods as untrusted input and inspect instructions, tools, dependencies and evaluation data before use.

The Ollama integration defaults to loopback. Non-loopback endpoints require explicit CLI opt-in. Generated prompts and evaluation reports may contain sensitive user input, so do not commit them without review.

Model Modding does not guarantee that a mod makes a model safe, accurate or suitable for a regulated use case. Domain and security review remain necessary.
