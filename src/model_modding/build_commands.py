from __future__ import annotations

import argparse
from pathlib import Path

from .builds import build_command, verify_command
from .evidence import verify_evidence_command
from .evidence_comparison import compare_evidence_command, compatibility_matrix_command

BUILD_COMMANDS = {
    "build",
    "verify-build",
    "verify-evidence",
    "compare-evidence",
    "matrix-evidence",
}


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
        description="Reproducible Model Modding build and evidence commands",
    )
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    subcommands = parser.add_subparsers(dest="command", required=True)

    build = subcommands.add_parser("build", help="Build a recipe lock and Agent Behaviour Bill of Materials")
    build.add_argument("name", help="Recipe name")
    build.add_argument("--output", type=Path, help="Build directory")

    verify = subcommands.add_parser("verify-build", help="Verify a build against current behavioural sources")
    verify.add_argument("name", help="Recipe name")
    verify.add_argument("--build-directory", type=Path, help="Build directory")

    evidence = subcommands.add_parser("verify-evidence", help="Verify a durable run evidence bundle")
    evidence.add_argument("directory", type=Path, help="Evidence bundle directory")

    compare = subcommands.add_parser(
        "compare-evidence",
        help="Compare verified baseline and candidate evidence bundles",
    )
    compare.add_argument("baseline", type=Path, help="Baseline evidence bundle")
    compare.add_argument("candidate", type=Path, help="Candidate evidence bundle")
    compare.add_argument("--output", type=Path, help="Comparison output directory")
    compare.add_argument(
        "--fail-on",
        choices=("critical", "major", "minor", "none"),
        default="critical",
        help="Fail when a new or escalated failure reaches this severity",
    )

    matrix = subcommands.add_parser(
        "matrix-evidence",
        help="Create a provider/model compatibility matrix from verified evidence",
    )
    matrix.add_argument("directories", type=Path, nargs="+", help="Evidence bundle directories")
    matrix.add_argument("--output", type=Path, help="Matrix output directory")
    return parser


def main(arguments: list[str] | None = None) -> int:
    args = build_parser().parse_args(arguments)
    root = args.root.resolve()
    if args.command == "build":
        return build_command(root, args.name, args.output)
    if args.command == "verify-build":
        return verify_command(root, args.name, args.build_directory)
    if args.command == "verify-evidence":
        return verify_evidence_command(root, args.directory)
    if args.command == "compare-evidence":
        return compare_evidence_command(
            root,
            args.baseline,
            args.candidate,
            args.output,
            fail_on=args.fail_on,
        )
    if args.command == "matrix-evidence":
        return compatibility_matrix_command(root, args.directories, args.output)
    return 2
