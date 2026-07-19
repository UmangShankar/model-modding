from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import cli
from .benchmark import benchmark_recipe
from .doctor import run_doctor


def _extract_root(arguments: list[str], command_index: int) -> tuple[Path, list[str]]:
    root = Path.cwd()
    global_arguments = arguments[:command_index]
    command_arguments = arguments[command_index + 1 :]
    if global_arguments:
        global_parser = argparse.ArgumentParser(add_help=False)
        global_parser.add_argument("--root", type=Path)
        known, unknown = global_parser.parse_known_args(global_arguments)
        if unknown:
            raise ValueError("unsupported global arguments")
        if known.root is not None:
            root = known.root
    return root.resolve(), command_arguments


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)

    if "doctor" in arguments:
        doctor_index = arguments.index("doctor")
        try:
            root, doctor_arguments = _extract_root(arguments, doctor_index)
        except ValueError:
            return cli.main(arguments)
        parser = argparse.ArgumentParser(prog="modding doctor", description="Check Model Modding release and local runtime readiness")
        parser.add_argument("--host", default="http://127.0.0.1:11434", help="Ollama API base URL")
        args = parser.parse_args(doctor_arguments)
        return run_doctor(root, args.host)

    if "benchmark" in arguments:
        benchmark_index = arguments.index("benchmark")
        try:
            root, benchmark_arguments = _extract_root(arguments, benchmark_index)
        except ValueError:
            return cli.main(arguments)
        parser = argparse.ArgumentParser(prog="modding benchmark", description="Compare a recipe across local Ollama models")
        parser.add_argument("name", help="Recipe name")
        parser.add_argument("--models", required=True, help="Comma-separated installed Ollama models")
        parser.add_argument("--output", type=Path, help="Report directory")
        parser.add_argument("--dry-run", action="store_true", help="Show the benchmark plan without calling models")
        parser.add_argument("--host", default="http://127.0.0.1:11434", help="Ollama API base URL")
        parser.add_argument("--timeout", type=float, default=120.0, help="Request timeout in seconds")
        parser.add_argument("--allow-remote-host", action="store_true", help="Allow a non-loopback Ollama endpoint")
        args = parser.parse_args(benchmark_arguments)
        return benchmark_recipe(root, args.name, args.models, args.output, args.dry_run, args.host, args.timeout, args.allow_remote_host)

    return cli.main(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
