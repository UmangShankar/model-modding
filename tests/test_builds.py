from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from model_modding.builds import (
    BUILD_FILENAMES,
    build_recipe,
    canonical_json_bytes,
    canonical_text_bytes,
    sha256_bytes,
    verify_build,
)
from model_modding.entry import main

ROOT = Path(__file__).resolve().parents[1]
RECIPE = "trusted-document-explainer"


def copy_behaviour_source(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    shutil.copytree(ROOT / "schemas", root / "schemas")
    shutil.copytree(ROOT / "mods", root / "mods")
    shutil.copytree(ROOT / "recipes", root / "recipes")
    return root


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_canonical_text_bytes_normalise_platform_line_endings(tmp_path: Path) -> None:
    lf = tmp_path / "lf.md"
    crlf = tmp_path / "crlf.md"
    lf.write_bytes(b"first\nsecond\n")
    crlf.write_bytes(b"first\r\nsecond\r\n")

    assert canonical_text_bytes(lf) == b"first\nsecond\n"
    assert canonical_text_bytes(crlf) == canonical_text_bytes(lf)


def test_build_emits_lock_abom_prompt_and_manifest(tmp_path: Path) -> None:
    output = tmp_path / "build"
    result = build_recipe(ROOT, RECIPE, output)

    assert {path.name for path in output.iterdir()} == set(BUILD_FILENAMES)
    assert len(result.source_digest) == 64
    assert len(result.build_digest) == 64

    lock = read_json(output / "recipe.lock.json")
    abom = read_json(output / "abom.json")
    manifest = read_json(output / "manifest.json")

    assert lock["schema_version"] == "0.1"
    assert lock["algorithm"] == "sha256"
    assert lock["build_digest"] == sha256_bytes(canonical_json_bytes(lock["digest_inputs"]))
    assert lock["source_digest"] == lock["digest_inputs"]["source_digest"]
    assert lock["outputs"]["system_prompt"]["sha256"] == sha256_bytes(
        (output / "system.md").read_bytes()
    )
    assert [component["reference"] for component in lock["components"]] == [
        "domain/plain-language-explainer",
        "safety/deadline-guardian",
        "safety/obligation-guardian",
        "safety/exception-guardian",
        "safety/source-grounding-guardian",
    ]
    assert all("\\" not in component["manifest"]["path"] for component in lock["components"])

    assert abom["document_type"] == "agent-behaviour-bill-of-materials"
    assert abom["build_digest"] == lock["build_digest"]
    assert {component["role"] for component in abom["components"]} == {
        "transformation",
        "assurance",
    }
    assert any(component["invariants"]["preserve"] for component in abom["components"])
    assert "generated_at" not in abom
    assert str(ROOT) not in (output / "abom.json").read_text(encoding="utf-8")

    assert manifest["document_type"] == "model-modding-build"
    assert manifest["build_digest"] == result.build_digest
    assert {item["path"] for item in manifest["artifacts"]} == {
        "abom.json",
        "abom.md",
        "recipe.lock.json",
        "system.md",
    }


def test_two_builds_from_same_sources_are_byte_identical(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"

    first_result = build_recipe(ROOT, RECIPE, first)
    second_result = build_recipe(ROOT, RECIPE, second)

    assert first_result.source_digest == second_result.source_digest
    assert first_result.build_digest == second_result.build_digest
    for filename in BUILD_FILENAMES:
        assert (first / filename).read_bytes() == (second / filename).read_bytes()


def test_line_ending_only_change_keeps_build_digest_stable(tmp_path: Path) -> None:
    root = copy_behaviour_source(tmp_path)
    first = build_recipe(root, RECIPE, tmp_path / "first")
    instruction = root / "mods" / "domain" / "plain-language-explainer" / "instructions" / "system.md"
    instruction.write_bytes(instruction.read_bytes().replace(b"\n", b"\r\n"))

    second = build_recipe(root, RECIPE, tmp_path / "second")

    assert first.source_digest == second.source_digest
    assert first.build_digest == second.build_digest


def test_behaviour_byte_change_invalidates_lock_and_existing_build(tmp_path: Path) -> None:
    root = copy_behaviour_source(tmp_path)
    output = tmp_path / "build"
    first = build_recipe(root, RECIPE, output)
    instruction = root / "mods" / "domain" / "plain-language-explainer" / "instructions" / "system.md"
    instruction.write_text(
        instruction.read_text(encoding="utf-8") + "\nPreserve this additional behavioural byte.\n",
        encoding="utf-8",
    )

    failures = verify_build(root, RECIPE, output)
    second = build_recipe(root, RECIPE, tmp_path / "changed")

    assert failures
    assert any("artifact mismatch" in failure for failure in failures)
    assert first.source_digest != second.source_digest
    assert first.build_digest != second.build_digest


def test_tampered_artifact_fails_offline_verification(tmp_path: Path) -> None:
    output = tmp_path / "build"
    build_recipe(ROOT, RECIPE, output)
    (output / "system.md").write_text("tampered\n", encoding="utf-8")

    failures = verify_build(ROOT, RECIPE, output)

    assert any("system.md" in failure for failure in failures)


def test_build_refuses_unmanaged_output_paths(tmp_path: Path) -> None:
    output = tmp_path / "build"
    output.mkdir()
    (output / "notes.txt").write_text("keep me", encoding="utf-8")

    with pytest.raises(ValueError, match="unmanaged paths"):
        build_recipe(ROOT, RECIPE, output)


def test_cli_build_and_verify_support_command_root_placement(tmp_path: Path, capsys) -> None:
    output = tmp_path / "bundle"

    assert main(["build", RECIPE, "--output", str(output), "--root", str(ROOT)]) == 0
    assert main(["verify-build", RECIPE, "--build-directory", str(output), "--root", str(ROOT)]) == 0

    stdout = capsys.readouterr().out
    assert "Build digest:" in stdout
    assert "Build verified:" in stdout


def test_top_level_help_mentions_reproducible_build_commands(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--help"])

    assert exc.value.code == 0
    output = capsys.readouterr().out
    assert "build" in output
    assert "verify-build" in output
