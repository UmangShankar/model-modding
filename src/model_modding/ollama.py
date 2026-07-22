from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.request import urlopen

from .cli import load_yaml, resolve_mod
from .ollama_provider import DEFAULT_OLLAMA_HOST, OllamaProvider, validate_ollama_host
from .provider import (
    GenerationOptions,
    ProviderError,
    ProviderRequest,
    create_provider,
)


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


def list_models(
    host: str,
    timeout: float = 3.0,
    opener: Callable[..., Any] = urlopen,
) -> list[str]:
    """Backward-compatible Ollama model discovery through the provider adapter."""

    return OllamaProvider(host=host, opener=opener).list_models(timeout=timeout)


def stream_chat(
    host: str,
    model: str,
    prompt: str,
    system_prompt: str,
    timeout: float = 120.0,
    opener: Callable[..., Any] = urlopen,
) -> Iterable[str]:
    """Backward-compatible Ollama streaming API through the provider adapter."""

    provider = OllamaProvider(host=host, opener=opener)
    request = ProviderRequest(
        model=model,
        prompt=prompt,
        system_prompt=system_prompt,
        timeout=timeout,
    )
    return provider.stream_text(request)


def display_name(slug: str) -> str:
    return slug.replace("-", " ").title()


def run_recipe(
    root: Path,
    recipe_name: str,
    model: str,
    prompt: str,
    host: str = DEFAULT_OLLAMA_HOST,
    timeout: float = 120.0,
    allow_remote: bool = False,
    opener: Callable[..., Any] = urlopen,
    provider_name: str = "ollama",
    generation_options: GenerationOptions | None = None,
) -> int:
    try:
        compiled = compile_recipe_in_memory(root, recipe_name)
        provider = create_provider(
            provider_name,
            host=host,
            allow_remote=allow_remote,
            opener=opener,
        )
        request = ProviderRequest(
            model=model,
            prompt=prompt,
            system_prompt=compiled.system_prompt,
            options=generation_options or GenerationOptions(),
            timeout=timeout,
        )
    except (OSError, ValueError, ProviderError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    description = provider.describe()
    print(f"Recipe: {display_name(compiled.name)}")
    print(f"Provider: {provider_name.casefold()}")
    print(f"Model: {model}")
    if description.get("endpoint"):
        print(f"Endpoint: {description['endpoint']}")
        if provider_name.casefold() == "ollama":
            print(f"Ollama: {description['endpoint']}")
    print(f"Installed mods: {', '.join(compiled.references)}")
    print(f"Generation options: {json.dumps(request.options.supplied(), sort_keys=True)}")
    print("\nResponse:\n")

    try:
        response = provider.generate(request, on_chunk=lambda chunk: print(chunk, end="", flush=True))
    except ProviderError as exc:
        print(f"\n{exc}", file=sys.stderr)
        return 1

    print(f"\n\nCompleted in {response.latency_seconds:.2f}s")
    print(f"Finish reason: {response.finish_reason or 'not reported'}")
    if response.usage.total_tokens is not None:
        print(
            "Token usage: "
            f"input={response.usage.input_tokens}, "
            f"output={response.usage.output_tokens}, "
            f"total={response.usage.total_tokens}"
        )
    return 0
