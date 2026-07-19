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
        failures.append(f"No {label} manifests found")
        return failures

    for manifest_path in manifests:
        try:
            manifest = load_yaml(manifest_path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            failures.append(f"{manifest_path.relative_to(root)}: {exc}")
            continue

        errors = sorted(validator.iter_errors(manifest), key=lambda error: list(error.path))
        if errors:
            for error in errors:
                location = ".".join(str(part) for part in error.path) or "<root>"
                failures.append(
                    f"{manifest_path.relative_to(root)} [{location}]: {error.message}"
                )
        else:
            print(f"PASS {manifest_path.relative_to(root)}")

    return failures


def validate_repository(root: Path) -> int:
    failures: list[str] = []
    failures.extend(
        validate_group(
            root,
            "mod",
            root / "schemas" / "mod.schema.json",
            sorted((root / "mods").glob("**/mod.yaml")),
        )
    )
    failures.extend(
        validate_group(
            root,
            "recipe",
            root / "schemas" / "recipe.schema.json",
            sorted((root / "recipes").glob("**/recipe.yaml")),
        )
    )

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
    if not KEBAB_CASE.fullmatch(category):
        print("Categories must use lowercase kebab-case.", file=sys.stderr)
        return 2

    destination = root / "mods" / category / name
    if destination.exists():
        print(f"Refusing to overwrite existing path: {destination.relative_to(root)}", file=sys.stderr)
        return 2

    template_path = root / "templates" / "mod" / "mod.yaml"
    template = load_yaml(template_path)
    template["name"] = name
    template["category"] = category
    template["description"] = f"Describe the single, clearly defined change made by the {name} mod."
    template["authors"] = [{"name": author, **({"github": github} if github else {})}]

    destination.mkdir(parents=True)
    (destination / "instructions").mkdir()
    (destination / "examples").mkdir()
    (destination / "evaluations").mkdir()

    with (destination / "mod.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(template, handle, sort_keys=False, allow_unicode=True)

    (destination / "README.md").write_text(
        f"# {name}\n\nDescribe what this mod changes, when to use it, limitations, and examples.\n",
        encoding="utf-8",
    )
    (destination / "instructions" / "system.md").write_text(
        "# Behavioural instructions\n\nAdd the reusable instructions for this mod here.\n",
        encoding="utf-8",
    )
    (destination / "examples" / "README.md").write_text(
        "# Examples\n\nAdd representative inputs and expected outputs here.\n",
        encoding="utf-8",
    )
    (destination / "evaluations" / "cases.yaml").write_text(
        "cases: []\n",
        encoding="utf-8",
    )

    print(f"Created {destination.relative_to(root)}")
    print("Next: edit mod.yaml, add instructions and evaluations, then run `modding validate`.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="modding", description="Model Modding developer tools")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    subcommands = parser.add_subparsers(dest="command", required=True)

    subcommands.add_parser("validate", help="Validate all mod and recipe manifests")

    create = subcommands.add_parser("create", help="Create a project asset")
    create_subcommands = create.add_subparsers(dest="asset", required=True)
    create_mod_parser = create_subcommands.add_parser("mod", help="Create a mod from the starter template")
    create_mod_parser.add_argument("name")
    create_mod_parser.add_argument("--category", default=DEFAULT_CATEGORY)
    create_mod_parser.add_argument("--author", default="Model Modding Contributor")
    create_mod_parser.add_argument("--github")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()

    if args.command == "validate":
        return validate_repository(root)
    if args.command == "create" and args.asset == "mod":
        return create_mod(root, args.name, args.category, args.author, args.github)

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
