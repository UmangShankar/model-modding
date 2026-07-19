from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKSHOP = ROOT / "workshop" / "index.html"


def test_workshop_exists_as_standalone_html() -> None:
    content = WORKSHOP.read_text(encoding="utf-8")
    assert "<!doctype html>" in content.lower()
    assert "Model Modding Workshop" in content
    assert "<script>" in content
    assert "<style>" in content


def test_workshop_exposes_core_interactions() -> None:
    content = WORKSHOP.read_text(encoding="utf-8")
    for expected in (
        "Product Strategy Copilot",
        "Research Learning Companion",
        "Inquisitive Strategist",
        "Socratic Teacher",
        "Citation Guardian",
        "Copy prompt",
        "Download Markdown",
        "Fitment check",
    ):
        assert expected in content


def test_workshop_has_no_external_runtime_dependencies() -> None:
    content = WORKSHOP.read_text(encoding="utf-8")
    assert "<script src=" not in content
    assert "<link rel=\"stylesheet\"" not in content
    assert "fetch(" not in content
