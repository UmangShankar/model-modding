#!/usr/bin/env python3
"""Backward-compatible standalone wrapper for manifest validation."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from model_modding.cli import validate_repository


if __name__ == "__main__":
    raise SystemExit(validate_repository(ROOT))
