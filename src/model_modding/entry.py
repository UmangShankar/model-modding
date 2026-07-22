from __future__ import annotations

import sys

from . import cli


def main(argv: list[str] | None = None) -> int:
    """Run the unified Model Modding command-line interface."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    return cli.main(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
