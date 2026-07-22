from __future__ import annotations

import json
from pathlib import Path

from model_modding.evaluation import (
    build_report,
    evaluate_recipe,
    load_evaluation_cases,
    markdown_report,
    score_response,
)

ROOT = Path(__file__).resolve().parents[1]


class FakeResponse:
    def __init__(self, text: str) -> None:
        self.lines = [json.dumps({"message": {"content": text}, "done": True}).encode() + b"\n"]

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def __iter__(self):
        return iter(self.lines)


def test_loads_cases_from_all_recipe_mods() -> None:
    compiled, cases = load_evaluation_cases(ROOT, "research-learning-companion")
    assert compiled.references == ("personality/socratic-teacher", "safety/citation-guardian")
    assert len(cases) == 10
    assert {case.mod for case in cases} == {"personality/socratic-teacher", "safety/citation-guardian"}
    assert all(case.checks for case in cases)


def test_deterministic_scoring_supports_terms_questions_and_length() -> None:
    passed, checks = score_response(
        "Think of three groups of four. Can you picture the groups?",
        {"contains_any": [["groups", "sets"]], "question_count_min": 1, "question_count_max": 1, "max_words": 20},
    )
    assert passed is True
    assert all(item["passed"] for item in checks)

    failed, checks = score_response("Paris?", {"contains_any": [["Paris"]], "question_count_max": 0})
    assert failed is False
    assert any(not item["passed"] for item in checks)


def test_report_flags_improvements_and_regressions() -> None:
    _, cases = load_evaluation_cases(ROOT, "research-learning-companion")
    rows = [
        {"mod": cases[0].mod, "case": "improved", "stock": {"passed": False}, "modded": {"passed": True}},
        {"mod": cases[0].mod, "case": "regressed", "stock": {"passed": True}, "modded": {"passed": False}},
    ]
    report = build_report("research-learning-companion", "llama3.2", cases[:2], rows)
    assert report["summary"]["stock_passed"] == 1
    assert report["summary"]["modded_passed"] == 1
    assert report["summary"]["average_stock_latency_seconds"] == 0
    assert report["summary"]["average_modded_words"] == 0
    assert report["improvements"] == [f"{cases[0].mod}:improved"]
    assert report["regressions"] == [f"{cases[0].mod}:regressed"]
    assert "Human review" in markdown_report(report)


def test_evaluate_dry_run_does_not_call_model(capsys) -> None:
    result = evaluate_recipe(ROOT, "research-learning-companion", "llama3.2", dry_run=True)
    captured = capsys.readouterr()
    assert result == 0
    assert "Cases: 10" in captured.out
    assert "urgent-safety" in captured.out


def test_evaluate_writes_json_and_markdown_reports(tmp_path: Path, capsys) -> None:
    responses = iter(
        [
            "Three groups of four make twelve.",
            "Imagine three groups of four objects. Can you see why the total is twelve?",
        ] * 10
    )

    def opener(request, timeout):
        return FakeResponse(next(responses))

    result = evaluate_recipe(
        ROOT,
        "research-learning-companion",
        "llama3.2",
        output=tmp_path,
        opener=opener,
    )
    captured = capsys.readouterr()
    assert result == 0
    assert (tmp_path / "report.json").exists()
    assert (tmp_path / "report.md").exists()
    payload = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert payload["summary"]["cases"] == 10
    assert len(payload["cases"]) == 10
    assert payload["summary"]["average_stock_latency_seconds"] >= 0
    assert payload["summary"]["average_modded_latency_seconds"] >= 0
    assert payload["summary"]["average_stock_words"] > 0
    assert payload["summary"]["average_modded_words"] > 0
    assert payload["cases"][0]["stock"]["latency_seconds"] >= 0
    assert payload["cases"][0]["stock"]["words"] > 0
    assert payload["cases"][0]["modded"]["latency_seconds"] >= 0
    assert payload["cases"][0]["modded"]["words"] > 0
    markdown = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "Average stock latency" in markdown
    assert "Average modded words" in markdown
    assert "â€”" not in markdown
    assert "JSON report" in captured.out
