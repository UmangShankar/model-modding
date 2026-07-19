from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .cli import load_yaml, resolve_mod

DEFAULT_OLLAMA_HOST = "http://127.0.0.1:11434"


@dataclass(frozen=True)
class CompiledRecipe:
    name: str
    description: str
    references: tuple[str, ...]
    system_prompt: str


def compile_recipe_in_memory(root: Path, name: str) -> CompiledRecipe:
    recipe_path = root / "recipes" / name / "recipe.yaml"
    if not recipe_path.exists():
        raise ValueError(f"Recipe not found: {name}")

    recipe = load_yaml(recipe_path)
    loaded: list[tuple[str, Path, dict[str, Any]]] = []
    for reference in recipe["mods"]:
        loaded.append(resolve_mod(root, reference))

    selected = {reference for reference, _, _ in loaded}
    failures: list[str] = []
    for reference, _, manifest in loaded:
        for dependency in manifest.get("dependencies", []):
            if dependency not in selected:
                failures.append(f"{reference} requires missing dependency {dependency}")
        for conflict in manifest.get("conflicts", []):
            if conflict in selected:
                failures.append(f"{reference} conflicts with {conflict}")
    if failures:
        raise ValueError("; ".join(failures))

    sections = [f"# {recipe['name']}\n", recipe["description"].strip(), "\n## Compiled instructions\n"]
    references: list[str] = []
    for reference, manifest_path, _ in loaded:
        references.append(reference)
        sections.append(f"\n### Mod: {reference}\n")
        for path in sorted((manifest_path.parent / "instructions").glob("**/*.md")):
            sections.append(path.read_text(encoding="utf-8").strip() + "\n")

    return CompiledRecipe(
        name=recipe["name"],
        description=recipe["description"].strip(),
        references=tuple(references),
        system_prompt="\n".join(sections).strip() + "\n",
    )


def validate_ollama_host(host: str, allow_remote: bool = False) -> str:
    normalized = host.rstrip("/")
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Ollama host must be an http(s) URL")
    loopback = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    if not loopback and not allow_remote:
        raise ValueError(
            "Refusing non-loopback Ollama host. Pass --allow-remote-host only when you trust the endpoint."
        )
    return normalized


def list_models(host: str, timeout: float = 3.0, opener: Callable[..., Any] = urlopen) -> list[str]:
    request = Request(f"{host}/api/tags", headers={"Accept": "application/json"})
    with opener(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return [item["name"] for item in payload.get("models", []) if isinstance(item, dict) and item.get("name")]


def stream_chat(
    host: str,
    model: str,
    prompt: str,
    system_prompt: str,
    timeout: float = 120.0,
    opener: Callable[..., Any] = urlopen,
) -> Iterable[str]:
    body = json.dumps(
        {
            "model": model,
            "stream": True,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        }
    ).encode("utf-8")
    request = Request(
        f"{host}/api/chat",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/x-ndjson"},
    )
    with opener(request, timeout=timeout) as response:
        for raw_line in response:
            if not raw_line.strip():
                continue
            event = json.loads(raw_line.decode("utf-8"))
            if event.get("error"):
                raise RuntimeError(str(event["error"]))
            message = event.get("message", {})
            chunk = message.get("content", "") if isinstance(message, dict) else ""
            if chunk:
                yield chunk


def run_recipe(
    root: Path,
    recipe_name: str,
    model: str,
    prompt: str,
    host: str = DEFAULT_OLLAMA_HOST,
    timeout: float = 120.0,
    allow_remote: bool = False,
    opener: Callable[..., Any] = urlopen,
) -> int:
    try:
        normalized_host = validate_ollama_host(host, allow_remote)
        compiled = compile_recipe_in_memory(root, recipe_name)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"Recipe: {compiled.name}")
    print(f"Model: {model}")
    print(f"Ollama: {normalized_host}")
    print(f"Installed mods: {', '.join(compiled.references)}")
    print("\nResponse:\n")
    started = time.monotonic()
    try:
        for chunk in stream_chat(
            normalized_host,
            model,
            prompt,
            compiled.system_prompt,
            timeout=timeout,
            opener=opener,
        ):
            print(chunk, end="", flush=True)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        print(f"\nOllama returned HTTP {exc.code}: {detail or exc.reason}", file=sys.stderr)
        return 1
    except (URLError, TimeoutError, ConnectionError) as exc:
        print(
            f"\nCould not reach Ollama at {normalized_host}. Start Ollama and confirm the host. ({exc})",
            file=sys.stderr,
        )
        return 1
    except (json.JSONDecodeError, RuntimeError) as exc:
        print(f"\nInvalid Ollama response: {exc}", file=sys.stderr)
        return 1

    elapsed = time.monotonic() - started
    print(f"\n\nCompleted in {elapsed:.2f}s")
    return 0
