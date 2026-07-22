from pathlib import Path
from unittest.mock import patch

from model_modding.benchmark import benchmark_recipe, markdown_report, parse_models, resolve_model_selector
from model_modding.entry import main
from model_modding.evaluation import load_evaluation_cases

ROOT = Path(__file__).resolve().parents[1]


def test_parse_models_deduplicates_and_preserves_order() -> None:
    assert parse_models("llama3.2, qwen2.5:3b,llama3.2") == ["llama3.2", "qwen2.5:3b"]


def test_resolve_model_selector_matches_default_latest_tag() -> None:
    installed = {"llama3.2:latest", "qwen2.5:3b"}
    assert resolve_model_selector("llama3.2", installed) == "llama3.2:latest"
    assert resolve_model_selector("qwen2.5:3b", installed) == "qwen2.5:3b"
    assert resolve_model_selector("qwen2.5", installed) is None


def test_benchmark_dry_run_does_not_call_ollama(capsys) -> None:
    result = benchmark_recipe(ROOT, "trusted-document-explainer", "llama3.2,qwen2.5:3b", dry_run=True)
    assert result == 0
    output = capsys.readouterr().out
    assert "Cases per model" in output
    assert "Structured source facts: 23" in output
    assert "stock +" in output


def test_console_entry_routes_benchmark_with_command_root(capsys) -> None:
    result = main([
        "benchmark",
        "trusted-document-explainer",
        "--models",
        "llama3.2",
        "--dry-run",
        "--root",
        str(ROOT),
    ])
    assert result == 0
    assert "Benchmark: Trusted Document Explainer" in capsys.readouterr().out


def test_benchmark_resolves_default_tag_and_skips_unavailable_models(tmp_path, capsys) -> None:
    _, cases = load_evaluation_cases(ROOT, "trusted-document-explainer")
    responses = iter(
        ["stock answer", "plain explanation deadline exception uncertain not legal advice"] * len(cases)
    )
    seen_models: list[str] = []

    def collect(*args, **kwargs):
        seen_models.append(args[1])
        return next(responses)

    with patch("model_modding.benchmark.list_models", return_value=["llama3.2:latest"]), patch(
        "model_modding.benchmark.collect_response", side_effect=collect
    ):
        result = benchmark_recipe(
            ROOT,
            "trusted-document-explainer",
            "llama3.2,missing-model",
            output=tmp_path,
            opener=object(),
        )
    assert result == 0
    output = capsys.readouterr().out
    assert "Model: llama3.2 (llama3.2:latest)" in output
    assert "SKIP missing-model" in output
    assert set(seen_models) == {"llama3.2:latest"}
    report = (tmp_path / "benchmark.json").read_text(encoding="utf-8")
    assert '"schema_version": "0.3"' in report
    assert '"source_fact_count": 23' in report
    assert '"modded_source_comparison_failures"' in report
    assert '"resolved_model": "llama3.2:latest"' in report
    assert '"status": "unavailable"' in report
    assert '"status": "completed"' in report
    markdown = (tmp_path / "benchmark.md").read_text(encoding="utf-8")
    assert "Structured source facts: 23" in markdown
    assert "Source" in markdown
    assert "Avg latency" in markdown
    assert "Avg words" in markdown
    assert "â€”" not in markdown


def test_markdown_report_contains_fitment_columns() -> None:
    report = {
        "recipe_display_name": "Trusted Document Explainer",
        "case_count": 2,
        "source_fact_count": 1,
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
                "modded_source_comparison_failures": 0,
                "average_latency_seconds": 1.25,
                "average_modded_words": 30,
            },
        }],
    }
    text = markdown_report(report)
    assert "Model" in text
    assert "Regressions" in text
    assert "Source" in text
    assert "+50.0 pp" in text
