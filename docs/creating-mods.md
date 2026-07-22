# Creating mods

Create a scaffold with:

```bash
modding create mod my-mod --category personality --author "Your Name"
```

New scaffolds declare `role: transformation` by default. Change the role to `assurance` when the mod primarily protects a safeguard or detects a prohibited transformation.

Keep the purpose narrow. Complete `mod.yaml`, replace the starter instruction text, add representative examples and write evaluation cases.

A useful mod explains:

- what behaviour it changes;
- whether its role is transformation or assurance;
- which invariants it explicitly preserves or which transformations it prohibits;
- who benefits;
- when it should not be used;
- supported model families;
- dependencies and conflicts;
- risks and limitations;
- how success and regression will be reviewed.

Do not add invariant declarations merely to make a package appear safer. Every declaration should match the instructions, examples, evaluation cases and documented limitations. Existing v0.1 manifests may omit role and invariant declarations during migration.

Read [Invariant declarations](invariants.md) for the controlled vocabulary and severity model.

Validate, inspect and test before opening a pull request:

```bash
modding validate
modding inspect my-mod
pytest
```

Do not include credentials, private prompts, personal data or content you cannot license under the repository terms.
