from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

KEBAB_CASE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MOD_CATEGORIES = (
    "personality", "domain", "workflow", "tool", "memory", "safety", "interface", "experimental"
)
DEFAULT_CATEGORY = "personality"


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML object")
    return data


def validate_group(root: Path, label: str, schema_path: Path, manifests: list[Path]) -> list[str]:
    schema = load_json(schema_path)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    failures: list[str] = []
    if not manifests:
        return [f"No {label} manifests found"]
    for manifest_path in manifests:
        try:
            manifest = load_yaml(manifest_path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            failures.append(f"{manifest_path.relative_to(root)}: {exc}")
            continue
        errors = list(validator.iter_errors(manifest))
        for error in sorted(errors, key=lambda item: list(item.path)):
            location = ".".join(str(part) for part in error.path) or "<root>"
            failures.append(f"{manifest_path.relative_to(root)} [{location}]: {error.message}")
        if not errors:
            print(f"PASS {manifest_path.relative_to(root)}")
    return failures


def validate_repository(root: Path) -> int:
    failures = validate_group(root, "mod", root / "schemas/mod.schema.json", sorted((root / "mods").glob("**/mod.yaml")))
    failures += validate_group(root, "recipe", root / "schemas/recipe.schema.json", sorted((root / "recipes").glob("**/recipe.yaml")))
    if failures:
        print("\nValidation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print("\nAll manifests are valid.")
    return 0


def create_mod(root: Path, name: str, category: str, author: str, github: str | None) -> int:
    if not KEBAB_CASE.fullmatch(name):
        print("Mod names must use lowercase kebab-case, for example: socratic-teacher", file=sys.stderr)
        return 2
    if category not in MOD_CATEGORIES:
        print(f"Category must be one of: {', '.join(MOD_CATEGORIES)}", file=sys.stderr)
        return 2
    destination = root / "mods" / category / name
    if destination.exists():
        print(f"Refusing to overwrite existing path: {destination.relative_to(root)}", file=sys.stderr)
        return 2
    template = load_yaml(root / "templates/mod/mod.yaml")
    template.update(name=name, category=category,
                    description=f"Describe the single, clearly defined change made by the {name} mod.",
                    authors=[{"name": author, **({"github": github} if github else {})}])
    for folder in ("instructions", "examples", "evaluations"):
        (destination / folder).mkdir(parents=True, exist_ok=True)
    (destination / "mod.yaml").write_text(yaml.safe_dump(template, sort_keys=False, allow_unicode=True), encoding="utf-8")
    (destination / "README.md").write_text(f"# {name}\n\nDescribe purpose, use, limitations and examples.\n", encoding="utf-8")
    (destination / "instructions/system.md").write_text("# Behavioural instructions\n\nAdd reusable instructions here.\n", encoding="utf-8")
    (destination / "examples/README.md").write_text("# Examples\n\nAdd representative examples here.\n", encoding="utf-8")
    (destination / "evaluations/cases.yaml").write_text("cases: []\n", encoding="utf-8")
    print(f"Created {destination.relative_to(root)}")
    return 0


def resolve_mod(root: Path, reference: str) -> tuple[str, Path, dict[str, Any]]:
    candidates = [root / "mods" / reference / "mod.yaml"] if "/" in reference else list((root / "mods").glob(f"*/{reference}/mod.yaml"))
    candidates = [path for path in candidates if path.exists()]
    if not candidates:
        raise ValueError(f"Mod not found: {reference}")
    if len(candidates) > 1:
        raise ValueError(f"Mod name is ambiguous; use category/name: {reference}")
    path = candidates[0]
    return str(path.parent.relative_to(root / "mods")), path, load_yaml(path)


def evaluation_count(mod_dir: Path) -> int:
    total = 0
    for path in sorted((mod_dir / "evaluations").glob("*.yaml")) if (mod_dir / "evaluations").exists() else []:
        data = load_yaml(path)
        cases = data.get("cases", [])
        if isinstance(cases, list):
            total += len(cases)
    return total


def inspect_mod(root: Path, reference: str, as_json: bool = False) -> int:
    try:
        resolved, manifest_path, manifest = resolve_mod(root, reference)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    mod_dir = manifest_path.parent
    instruction_files = sorted(str(p.relative_to(mod_dir)) for p in (mod_dir / "instructions").glob("**/*") if p.is_file())
    report = {
        "reference": resolved, "name": manifest["name"], "version": manifest["version"],
        "status": manifest["status"], "description": manifest["description"],
        "capabilities": manifest.get("capabilities", []), "compatible_models": manifest.get("compatible_models", []),
        "dependencies": manifest.get("dependencies", []), "conflicts": manifest.get("conflicts", []),
        "instruction_files": instruction_files, "evaluation_cases": evaluation_count(mod_dir),
    }
    if as_json:
        print(json.dumps(report, indent=2))
    else:
        print(f"{report['name']} {report['version']} [{report['status']}]\n{report['description']}")
        print(f"Reference: {resolved}\nCapabilities: {', '.join(report['capabilities']) or 'none'}")
        print(f"Compatible models: {', '.join(report['compatible_models']) or 'not documented'}")
        print(f"Instructions: {len(instruction_files)} file(s)\nEvaluation cases: {report['evaluation_cases']}")
        if report["dependencies"]:
            print(f"Dependencies: {', '.join(report['dependencies'])}")
        if report["conflicts"]:
            print(f"Conflicts: {', '.join(report['conflicts'])}")
    return 0


def compose_recipe(root: Path, name: str, output: Path | None = None) -> int:
    recipe_path = root / "recipes" / name / "recipe.yaml"
    if not recipe_path.exists():
        print(f"Recipe not found: {name}", file=sys.stderr)
        return 2
    recipe = load_yaml(recipe_path)
    loaded: list[tuple[str, Path, dict[str, Any]]] = []
    try:
        for reference in recipe["mods"]:
            loaded.append(resolve_mod(root, reference))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
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
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    sections = [f"# {recipe['name']}\n", recipe["description"].strip(), "\n## Compiled instructions\n"]
    metadata: list[dict[str, Any]] = []
    for reference, manifest_path, manifest in loaded:
        files = sorted((manifest_path.parent / "instructions").glob("**/*.md"))
        sections.append(f"\n### Mod: {reference}\n")
        for path in files:
            sections.append(path.read_text(encoding="utf-8").strip() + "\n")
        metadata.append({"reference": reference, "version": manifest["version"], "instruction_files": [str(p.relative_to(root)) for p in files]})
    destination = (output or root / "build" / name).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "system.md").write_text("\n".join(sections).strip() + "\n", encoding="utf-8")
    (destination / "manifest.json").write_text(json.dumps({"recipe": recipe, "mods": metadata}, indent=2) + "\n", encoding="utf-8")
    print(f"Compiled {name}\nSystem prompt: {destination / 'system.md'}\nManifest: {destination / 'manifest.json'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="modding", description="Model Modding developer tools")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("validate", help="Validate all mod and recipe manifests")
    inspect = subcommands.add_parser("inspect", help="Inspect a mod")
    inspect.add_argument("reference")
    inspect.add_argument("--json", action="store_true")
    compose = subcommands.add_parser("compose", help="Compile a recipe into reusable instructions")
    compose.add_argument("name")
    compose.add_argument("--output", type=Path)
    run = subcommands.add_parser("run", help="Run a recipe against a local Ollama model")
    run.add_argument("name", help="Recipe name")
    run.add_argument("--model", required=True, help="Installed Ollama model, for example llama3.2")
    run.add_argument("--prompt", required=True, help="User prompt")
    run.add_argument("--host", default="http://127.0.0.1:11434", help="Ollama API base URL")
    run.add_argument("--timeout", type=float, default=120.0, help="Request timeout in seconds")
    run.add_argument("--allow-remote-host", action="store_true", help="Allow a non-loopback Ollama endpoint")
    evaluate = subcommands.add_parser("evaluate", help="Compare stock and modded behaviour across evaluation cases")
    evaluate.add_argument("name", help="Recipe name")
    evaluate.add_argument("--model", required=True, help="Installed Ollama model")
    evaluate.add_argument("--output", type=Path, help="Report directory")
    evaluate.add_argument("--dry-run", action="store_true", help="List cases without calling a model")
    evaluate.add_argument("--host", default="http://127.0.0.1:11434", help="Ollama API base URL")
    evaluate.add_argument("--timeout", type=float, default=120.0, help="Request timeout in seconds")
    evaluate.add_argument("--allow-remote-host", action="store_true", help="Allow a non-loopback Ollama endpoint")
    create = subcommands.add_parser("create", help="Create a project asset")
    create_subcommands = create.add_subparsers(dest="asset", required=True)
    create_mod_parser = create_subcommands.add_parser("mod", help="Create a mod from the starter template")
    create_mod_parser.add_argument("name")
    create_mod_parser.add_argument("--category", choices=MOD_CATEGORIES, default=DEFAULT_CATEGORY)
    create_mod_parser.add_argument("--author", default="Model Modding Contributor")
    create_mod_parser.add_argument("--github")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    if args.command == "validate":
        return validate_repository(root)
    if args.command == "inspect":
        return inspect_mod(root, args.reference, args.json)
    if args.command == "compose":
        return compose_recipe(root, args.name, args.output)
    if args.command == "run":
        from .ollama import run_recipe
        return run_recipe(root, args.name, args.model, args.prompt, args.host, args.timeout, args.allow_remote_host)
    if args.command == "evaluate":
        from .evaluation import evaluate_recipe
        return evaluate_recipe(root, args.name, args.model, args.output, args.dry_run, args.host, args.timeout, args.allow_remote_host)
    if args.command == "create" and args.asset == "mod":
        return create_mod(root, args.name, args.category, args.author, args.github)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
