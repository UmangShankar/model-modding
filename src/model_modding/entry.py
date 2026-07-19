from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import cli
from .doctor import run_doctor


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if "doctor" not in arguments:
        return cli.main(arguments)

    parser = argparse.ArgumentParser(prog="modding doctor", description="Check Model Modding release and local runtime readiness")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    parser.add_argument("--host", default="http://127.0.0.1:11434", help="Ollama API base URL")

    doctor_index = arguments.index("doctor")
    global_arguments = arguments[:doctor_index]
    doctor_arguments = arguments[doctor_index + 1 :]
    if global_arguments:
        global_parser = argparse.ArgumentParser(add_help=False)
        global_parser.add_argument("--root", type=Path)
        known, unknown = global_parser.parse_known_args(global_arguments)
        if unknown:
            return cli.main(arguments)
        if known.root is not None and "--root" not in doctor_arguments:
            doctor_arguments = ["--root", str(known.root), *doctor_arguments]

    args = parser.parse_args(doctor_arguments)
    return run_doctor(args.root.resolve(), args.host)


if __name__ == "__main__":
    raise SystemExit(main())
