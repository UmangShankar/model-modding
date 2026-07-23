from __future__ import annotations

import importlib.util
import os
import shutil
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.error import URLError

from .cli import validate_repository
from .ollama import DEFAULT_OLLAMA_HOST, list_models
from .provider import ProviderError, provider_names


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str
    required: bool = True


def _optional_provider_check(
    name: str,
    package: str,
    extra: str,
    key_name: str,
    environment: Mapping[str, str],
) -> Check:
    sdk = importlib.util.find_spec(package) is not None
    key = bool(environment.get(key_name))
    if sdk and key:
        status, detail = "PASS", f"SDK installed; {key_name} configured"
    elif not sdk and not key:
        status, detail = "WARN", f'install "model-modding[{extra}]" and set {key_name}'
    elif not sdk:
        status, detail = "WARN", f'{key_name} configured; install "model-modding[{extra}]"'
    else:
        status, detail = "WARN", f"SDK installed; {key_name} not configured"
    return Check(name, status, detail, required=False)


def run_doctor(
    root: Path,
    host: str = DEFAULT_OLLAMA_HOST,
    model_loader: Callable[..., list[str]] = list_models,
    environ: Mapping[str, str] | None = None,
) -> int:
    checks: list[Check] = []
    environment = os.environ if environ is None else environ
    version_ok = sys.version_info >= (3, 10)
    checks.append(Check("Python", "PASS" if version_ok else "FAIL", sys.version.split()[0]))

    required_paths = [
        "pyproject.toml",
        "schemas/mod.schema.json",
        "schemas/invariant.schema.json",
        "schemas/recipe.schema.json",
        "mods",
        "recipes",
    ]
    missing = [path for path in required_paths if not (root / path).exists()]
    checks.append(Check("Repository structure", "PASS" if not missing else "FAIL", "complete" if not missing else f"missing: {', '.join(missing)}"))

    dependencies = ["yaml", "jsonschema", "referencing"]
    absent_dependencies = [name for name in dependencies if importlib.util.find_spec(name) is None]
    checks.append(Check("Python dependencies", "PASS" if not absent_dependencies else "FAIL", "installed" if not absent_dependencies else f"missing: {', '.join(absent_dependencies)}"))

    providers = provider_names()
    provider_ok = {"ollama", "anthropic", "openai"}.issubset(providers)
    checks.append(
        Check(
            "Provider registry",
            "PASS" if provider_ok else "FAIL",
            f"registered: {', '.join(providers) or 'none'}",
        )
    )

    checks.append(
        _optional_provider_check(
            "Anthropic", "anthropic", "anthropic", "ANTHROPIC_API_KEY", environment
        )
    )
    checks.append(
        _optional_provider_check(
            "OpenAI", "openai", "openai", "OPENAI_API_KEY", environment
        )
    )

    manifests_ok = validate_repository(root) == 0 if not missing else False
    checks.append(Check("Manifest validation", "PASS" if manifests_ok else "FAIL", "valid" if manifests_ok else "validation failed"))

    pytest_available = shutil.which("pytest") is not None or importlib.util.find_spec("pytest") is not None
    checks.append(Check("Test runner", "PASS" if pytest_available else "WARN", "pytest available" if pytest_available else "install the dev extra", required=False))

    try:
        models = model_loader(host, timeout=2.0)
        detail = f"reachable; {len(models)} model(s): {', '.join(models[:3])}" if models else "reachable; no models installed"
        status = "PASS" if models else "WARN"
    except (OSError, URLError, ValueError, ProviderError) as exc:
        status, detail = "WARN", f"not reachable at {host}: {exc}"
    checks.append(Check("Ollama", status, detail, required=False))

    print("Model Modding doctor\n")
    for check in checks:
        print(f"{check.status:4}  {check.name}: {check.detail}")

    failed = [check for check in checks if check.required and check.status == "FAIL"]
    print("\nRelease readiness: " + ("READY" if not failed else "NOT READY"))
    return 0 if not failed else 1
