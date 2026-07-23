from __future__ import annotations

import argparse
from pathlib import Path

from .builds import build_command, verify_command

BUILD_COMMANDS = {"build", "verify-build"}


def handles(arguments: list[str]) -> bool:
    skip = False
    for token in arguments:
        if skip:
            skip = False
            continue
        if token == "--root":
            skip = True
            continue
        if token.startswith("-"):
            continue
        return token in BUILD_COMMANDS
    return False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="modding",
        description="Reproducible Model Modding build commands",
    )
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    subcommands = parser.add_subparsers(dest="command", required=True)

    build = subcommands.add_parser("build", help="Build a recipe lock and Agent Behaviour Bill of Materials")
    build.add_argument("name", help="Recipe name")
    build.add_argument("--output", type=Path, help="Build directory")

    verify = subcommands.add_parser("verify-build", help="Verify a build against current behavioural sources")
    verify.add_argument("name", help="Recipe name")
    verify.add_argument("--build-directory", type=Path, help="Build directory")
    return parser


def main(arguments: list[str] | None = None) -> int:
    args = build_parser().parse_args(arguments)
    root = args.root.resolve()
    if args.command == "build":
        return build_command(root, args.name, args.output)
    if args.command == "verify-build":
        return verify_command(root, args.name, args.build_directory)
    return 2
