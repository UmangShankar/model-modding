from pathlib import Path
from unittest.mock import patch

from model_modding.benchmark import benchmark_recipe, markdown_report, parse_models

ROOT = Path(__file__).resolve().parents[1]


def test_parse_models_deduplicates_and_preserves_order() -> None:
    assert parse_models("llama3.2, qwen2.5:3b,llama3.2") == ["llama3.2", "qwen2.5:3b"]


def test_benchmark_dry_run_does_not_call_ollama(capsys) -> None:
    result = benchmark_recipe(ROOT, "trusted-document-explainer", "llama3.2,qwen2.5:3b", dry_run=True)
    assert result == 0
    output = capsys.readouterr().out
    assert "Cases per model" in output
    assert "stock +" in output


def test_benchmark_skips_unavailable_models(tmp_path, capsys) -> None:
    responses = iter(["stock answer", "plain explanation deadline exception uncertain not legal advice"] * 12)
    with patch("model_modding.benchmark.list_models", return_value=["llama3.2"]), patch(
        "model_modding.benchmark.collect_response", side_effect=lambda *args, **kwargs: next(responses)
    ):
        result = benchmark_recipe(
            ROOT,
            "trusted-document-explainer",
            "llama3.2,missing-model",
            output=tmp_path,
            opener=object(),
        )
    assert result == 0
    assert "SKIP missing-model" in capsys.readouterr().out
    report = (tmp_path / "benchmark.json").read_text(encoding="utf-8")
    assert '"status": "unavailable"' in report
    assert '"status": "completed"' in report


def test_markdown_report_contains_fitment_columns() -> None:
    report = {
        "recipe_display_name": "Trusted Document Explainer",
        "case_count": 2,
        "requested_models": ["a"],
        "models": [{
            "model": "a",
            "status": "completed",
            "summary": {
                "cases": 2,
                "stock_passed": 1,
                "modded_passed": 2,
                "improvement_points": 50.0,
                "regressions": 0,
                "average_latency_seconds": 1.25,
                "average_modded_words": 30,
            },
        }],
    }
    text = markdown_report(report)
    assert "Model" in text
    assert "Regressions" in text
    assert "+50.0 pp" in text
