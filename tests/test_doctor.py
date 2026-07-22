from __future__ import annotations

from pathlib import Path

import pytest

from model_modding.doctor import run_doctor
from model_modding.entry import main

ROOT = Path(__file__).resolve().parents[1]


def test_doctor_is_ready_when_required_checks_pass(capsys) -> None:
    result = run_doctor(ROOT, model_loader=lambda host, timeout: ["llama3.2:latest"])
    output = capsys.readouterr().out

    assert result == 0
    assert "Release readiness: READY" in output
    assert "Manifest validation" in output
    assert "llama3.2:latest" in output


def test_doctor_requires_invariant_schema(tmp_path: Path, capsys) -> None:
    root = tmp_path / "repo"
    (root / "schemas").mkdir(parents=True)
    (root / "mods").mkdir()
    (root / "recipes").mkdir()
    (root / "pyproject.toml").write_text("[project]\nname='example'\n", encoding="utf-8")
    (root / "schemas" / "mod.schema.json").write_text("{}\n", encoding="utf-8")
    (root / "schemas" / "recipe.schema.json").write_text("{}\n", encoding="utf-8")

    result = run_doctor(root, model_loader=lambda host, timeout: [])
    output = capsys.readouterr().out

    assert result == 1
    assert "schemas/invariant.schema.json" in output
    assert "Release readiness: NOT READY" in output


def test_doctor_treats_ollama_as_optional(capsys) -> None:
    def unavailable(host, timeout):
        raise OSError("connection refused")

    result = run_doctor(ROOT, model_loader=unavailable)
    output = capsys.readouterr().out

    assert result == 0
    assert "WARN  Ollama" in output
    assert "Release readiness: READY" in output


def test_console_entry_routes_doctor_with_command_root(capsys) -> None:
    result = main(["doctor", "--root", str(ROOT), "--host", "http://127.0.0.1:1"])
    output = capsys.readouterr().out

    assert result == 0
    assert "Model Modding doctor" in output


def test_console_entry_routes_doctor_with_global_root(capsys) -> None:
    result = main(["--root", str(ROOT), "doctor", "--host", "http://127.0.0.1:1"])
    output = capsys.readouterr().out

    assert result == 0
    assert "Model Modding doctor" in output


def test_top_level_help_lists_every_available_command(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--help"])

    assert exc.value.code == 0
    output = capsys.readouterr().out
    assert "doctor" in output
    assert "benchmark" in output
    assert "evaluate" in output
