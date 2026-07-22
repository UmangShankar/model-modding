from __future__ import annotations

import sys

from . import cli, provider_commands


def main(argv: list[str] | None = None) -> int:
    """Run the unified Model Modding command-line interface."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if provider_commands.handles(arguments):
        return provider_commands.main(arguments)
    return cli.main(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
