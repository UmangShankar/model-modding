from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCORECARD = ROOT / "workshop" / "scorecard.html"


def test_scorecard_loads_local_json_without_external_dependencies() -> None:
    content = SCORECARD.read_text(encoding="utf-8")
    for expected in (
        "Model Modding · Dyno Scorecard",
        "Load report.json",
        "Stock passed",
        "Modded passed",
        "Regressions",
        "schema_version",
        "file.text()",
    ):
        assert expected in content
    assert "<script src=" not in content
    assert "https://" not in content


def test_scorecard_contains_privacy_and_human_review_context() -> None:
    content = SCORECARD.read_text(encoding="utf-8")
    assert "nothing is uploaded" in content.lower()
    assert "human review" in content.lower()
