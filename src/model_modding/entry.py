from __future__ import annotations

import sys

from . import cli, provider_commands

_PROVIDER_FLAGS = {
    "--provider",
    "--temperature",
    "--top-p",
    "--max-tokens",
    "--seed",
    "--stop",
}


def _normalise_runtime_root(arguments: list[str]) -> list[str]:
    if "--root" not in arguments:
        return arguments
    index = arguments.index("--root")
    if index == 0 or index + 1 >= len(arguments):
        return arguments
    root_pair = arguments[index:index + 2]
    return root_pair + arguments[:index] + arguments[index + 2:]


def _provider_runtime_requested(arguments: list[str]) -> bool:
    if not provider_commands.handles(arguments):
        return False
    return "--help" in arguments or any(flag in arguments for flag in _PROVIDER_FLAGS)


def main(argv: list[str] | None = None) -> int:
    """Run the unified Model Modding command-line interface."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if _provider_runtime_requested(arguments):
        return provider_commands.main(_normalise_runtime_root(arguments))
    return cli.main(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
