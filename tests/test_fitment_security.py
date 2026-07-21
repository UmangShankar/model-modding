from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_fitment_viewer_uses_safe_dom_rendering() -> None:
    content = (ROOT / "workshop/fitment.html").read_text(encoding="utf-8")

    assert ".innerHTML" not in content
    assert "document.createElement" in content
    assert ".textContent" in content
    assert "replaceChildren" in content


def test_fitment_viewer_constrains_report_driven_widths() -> None:
    content = (ROOT / "workshop/fitment.html").read_text(encoding="utf-8")

    assert "Math.max(0,Math.min(100" in content
    assert "span.style.width=pct" in content
