#!/usr/bin/env python3
"""Backward-compatible wrapper for the packaged manifest validator."""

from pathlib import Path

from model_modding.cli import validate_repository


if __name__ == "__main__":
    raise SystemExit(validate_repository(Path.cwd()))
