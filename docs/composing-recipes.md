# Composing recipes

A recipe selects compatible mods and gives the resulting build a purpose.

```bash
modding compose research-learning-companion
```

The command resolves each mod, checks declared dependencies and conflicts, reads instruction files in deterministic order, and writes:

```text
build/research-learning-companion/
├── system.md
└── manifest.json
```

Use category/name references when names could be ambiguous. Composition order is behavioural: two individually useful mods may interact badly when both ask questions, add caveats or impose formatting. Document the intended order and add evaluation cases for important interactions.

The generated manifest records source versions and instruction files so the build can be inspected and reproduced.
