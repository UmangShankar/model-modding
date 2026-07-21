from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_evidence", ROOT / "scripts/validate_evidence.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
validate_package = MODULE.validate_package


def write_package(directory: Path, completed: bool = True) -> None:
    directory.mkdir(parents=True)
    model = {
        "model": "llama3.2",
        "resolved_model": "llama3.2:latest",
        "status": "completed" if completed else "unavailable",
    }
    if completed:
        model["summary"] = {"cases": 1}
        model["cases"] = [{
            "case": "example",
            "stock": {"response": "stock"},
            "modded": {"response": "modded"},
        }]
    (directory / "benchmark.json").write_text(json.dumps({
        "schema_version": "0.1",
        "recipe": "trusted-document-explainer",
        "completed_models": 1 if completed else 0,
        "models": [model],
    }), encoding="utf-8")
    (directory / "benchmark.md").write_text("# Benchmark\n", encoding="utf-8")
    (directory / "environment.json").write_text(json.dumps({
        "schema_version": "0.1",
        "captured_at": "2026-07-21T08:00:00Z",
        "model_modding_commit": "a" * 40,
        "platform": {"os": "Linux", "architecture": "x86_64", "python": "3.12", "ollama": "0.5"},
        "hardware": {"cpu": "test", "memory_gb": 16, "accelerator": "none"},
        "models": [{"requested": "llama3.2", "resolved": "llama3.2:latest"}],
    }), encoding="utf-8")
    (directory / "methodology.md").write_text(
        "# Methodology\n\n## Purpose\nTest.\n\n## Procedure\nRun.\n\n## Human review\nReviewed.\n\n## Limitations\nLimited.\n\n## Conclusion\nEvidence only.\n",
        encoding="utf-8",
    )


def test_valid_evidence_package_passes(tmp_path: Path) -> None:
    package = tmp_path / "run"
    write_package(package)
    assert validate_package(package) == []


def test_evidence_requires_completed_model(tmp_path: Path) -> None:
    package = tmp_path / "run"
    write_package(package, completed=False)
    assert "benchmark.json contains no completed models" in validate_package(package)


def test_evidence_rejects_template_placeholders(tmp_path: Path) -> None:
    package = tmp_path / "run"
    write_package(package)
    environment = json.loads((package / "environment.json").read_text(encoding="utf-8"))
    environment["platform"]["os"] = "REPLACE_ME"
    (package / "environment.json").write_text(json.dumps(environment), encoding="utf-8")
    assert "environment.json still contains template placeholders" in validate_package(package)


def test_evidence_requires_responses(tmp_path: Path) -> None:
    package = tmp_path / "run"
    write_package(package)
    benchmark = json.loads((package / "benchmark.json").read_text(encoding="utf-8"))
    del benchmark["models"][0]["cases"][0]["modded"]["response"]
    (package / "benchmark.json").write_text(json.dumps(benchmark), encoding="utf-8")
    assert any("missing modded response evidence" in failure for failure in validate_package(package))
