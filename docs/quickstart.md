# Five-minute quick start

## 1. Clone and install

```bash
git clone https://github.com/UmangShankar/model-modding.git
cd model-modding
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

## 2. Validate the repository

```bash
modding validate
```

A healthy repository ends with:

```text
All manifests are valid.
```

## 3. Create your first mod

```bash
modding create mod my-first-mod \
  --category personality \
  --author "Your Name" \
  --github your-github-username
```

This creates:

```text
mods/personality/my-first-mod/
├── mod.yaml
├── README.md
├── instructions/system.md
├── examples/README.md
└── evaluations/cases.yaml
```

The command refuses invalid names and will not overwrite an existing mod.

## 4. Edit and validate

Describe the mod in `mod.yaml`, add its reusable instructions and write evaluation cases. Then run:

```bash
modding validate
```

## 5. Run the test suite

```bash
pytest
```

You are now ready to open a pull request.
