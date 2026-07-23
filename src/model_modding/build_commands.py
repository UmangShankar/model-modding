from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .builds import build_command, verify_command
from .evidence import verify_evidence_command
from .evidence_comparison import compare_evidence_command, compatibility_matrix_command
from .release_pipeline import (
    activate_baseline,
    validate_provider_run_plan,
    write_aggregate,
    write_pr_summary,
    write_release_readiness,
)

BUILD_COMMANDS = {
    "build",
    "verify-build",
    "verify-evidence",
    "compare-evidence",
    "matrix-evidence",
    "aggregate-evidence",
    "activate-baseline",
    "release-check",
    "evidence-summary",
    "validate-provider-run",
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
        description="Reproducible Model Modding build, evidence and release commands",
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

    aggregate = subcommands.add_parser(
        "aggregate-evidence",
        help="Aggregate repeated compatible evidence bundles",
    )
    aggregate.add_argument("directories", type=Path, nargs="+", help="Evidence bundle directories")
    aggregate.add_argument("--output", type=Path, required=True, help="Aggregate output directory")
    aggregate.add_argument("--minimum-repetitions", type=int, default=1)
    aggregate.add_argument("--require-zero-critical", action="store_true")

    baseline = subcommands.add_parser(
        "activate-baseline",
        help="Activate a verified evidence bundle as a scoped reviewed baseline",
    )
    baseline.add_argument("source", type=Path, help="Verified evidence bundle")
    baseline.add_argument("destination", type=Path, help="Reviewed baseline directory")
    baseline.add_argument("--reviewer", required=True)
    baseline.add_argument("--scope", required=True)
    baseline.add_argument("--notes", default="")

    release = subcommands.add_parser(
        "release-check",
        help="Check v0.2 release evidence against provider, repetition, case and critical-failure gates",
    )
    release.add_argument("--aggregate", type=Path, required=True, help="aggregate.json")
    release.add_argument("--matrix", type=Path, required=True, help="matrix.json")
    release.add_argument("--output", type=Path, required=True, help="Readiness output directory")
    release.add_argument("--minimum-repetitions", type=int, default=3)
    release.add_argument("--minimum-cases", type=int, default=40)

    summary = subcommands.add_parser(
        "evidence-summary",
        help="Create a concise Markdown summary for CI or pull requests",
    )
    summary.add_argument("--comparison", type=Path)
    summary.add_argument("--matrix", type=Path)
    summary.add_argument("--aggregate", type=Path)
    summary.add_argument("--readiness", type=Path)
    summary.add_argument("--output", type=Path, required=True)
    summary.add_argument("--github-summary", action="store_true")

    plan = subcommands.add_parser(
        "validate-provider-run",
        help="Validate a protected cloud evidence run against cost and model allowlists",
    )
    plan.add_argument("--provider", required=True)
    plan.add_argument("--model", required=True)
    plan.add_argument("--repetitions", type=int, required=True)
    plan.add_argument("--max-tokens", type=int, required=True)
    plan.add_argument("--case-limit", type=int, required=True)
    plan.add_argument(
        "--allowlist",
        default=None,
        help="Comma-separated exact model IDs; defaults to MODEL_MODDING_ALLOWED_MODELS",
    )
    return parser


def main(arguments: list[str] | None = None) -> int:
    args = build_parser().parse_args(arguments)
    root = args.root.resolve()
    try:
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
        if args.command == "aggregate-evidence":
            destination, report = write_aggregate(
                root,
                args.directories,
                args.output,
                minimum_repetitions=args.minimum_repetitions,
                require_zero_critical=args.require_zero_critical,
            )
            print(f"Repeated evidence aggregate: {destination}")
            print(f"Pipeline status: {report['pipeline']['status'].upper()}")
            return 0 if report["pipeline"]["status"] == "passed" else 1
        if args.command == "activate-baseline":
            destination = activate_baseline(
                root,
                args.source,
                args.destination,
                reviewer=args.reviewer,
                scope=args.scope,
                notes=args.notes,
            )
            print(f"Reviewed baseline activated: {destination}")
            return 0
        if args.command == "release-check":
            destination, report = write_release_readiness(
                root,
                args.aggregate,
                args.matrix,
                args.output,
                minimum_repetitions=args.minimum_repetitions,
                minimum_cases=args.minimum_cases,
            )
            print(f"Release readiness: {destination}")
            print(f"Status: {report['status'].upper()}")
            return 0 if report["status"] == "ready" else 1
        if args.command == "evidence-summary":
            destination = write_pr_summary(
                args.output,
                comparison_path=args.comparison,
                matrix_path=args.matrix,
                aggregate_path=args.aggregate,
                readiness_path=args.readiness,
                append_github_summary=args.github_summary,
            )
            print(f"Evidence summary: {destination}")
            return 0
        if args.command == "validate-provider-run":
            plan = validate_provider_run_plan(
                provider=args.provider,
                model=args.model,
                repetitions=args.repetitions,
                max_tokens=args.max_tokens,
                case_limit=args.case_limit,
                allowlist=args.allowlist if args.allowlist is not None else os.environ.get("MODEL_MODDING_ALLOWED_MODELS", ""),
            )
            print(json.dumps(plan, sort_keys=True))
            return 0
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 2
