from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_fitment_matrix_is_local_and_explains_limits() -> None:
    content = (ROOT / "workshop/fitment.html").read_text(encoding="utf-8")
    assert "Model Fitment Matrix" in content
    assert "benchmark.json" in content
    assert "Regressions" in content
    assert "universal model quality" in content
    assert "https://" not in content
    assert "analytics" not in content.lower()


def test_workshop_readme_documents_benchmark_command() -> None:
    content = (ROOT / "workshop/README.md").read_text(encoding="utf-8")
    assert "modding benchmark" in content
    assert "workshop/fitment.html" in content
    assert "benchmark.json" in content
