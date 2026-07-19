# Creating mods

Create a scaffold with:

```bash
modding create mod my-mod --category personality --author "Your Name"
```

Keep the purpose narrow. Complete `mod.yaml`, replace the starter instruction text, add representative examples and write evaluation cases.

A useful mod explains:

- what behaviour it changes;
- who benefits;
- when it should not be used;
- supported model families;
- dependencies and conflicts;
- risks and limitations;
- how success and regression will be reviewed.

Validate and test before opening a pull request:

```bash
modding validate
pytest
```

Do not include credentials, private prompts, personal data or content you cannot license under the repository terms.
