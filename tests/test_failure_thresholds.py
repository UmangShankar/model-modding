from __future__ import annotations

import pytest

from model_modding.evaluation import build_report


def report_for(severity: str, fail_on: str) -> dict:
    failure = {
        "id": f"example:{severity}",
        "mod": "safety/example-guardian",
        "case": "example-case",
        "kind": "preserve",
        "invariant": "deadline",
        "severity": severity,
        "description": "Example failure.",
        "failed_checks": [],
    }
    rows = [
        {
            "mod": "safety/example-guardian",
            "case": "example-case",
            "stock": {"passed": True, "invariant_failures": []},
            "modded": {"passed": False, "invariant_failures": [failure]},
        }
    ]
    return build_report("example-recipe", "example-model", [], rows, fail_on=fail_on)


@pytest.mark.parametrize(
    ("severity", "fail_on", "expected_status"),
    [
        ("critical", "critical", "failed"),
        ("major", "critical", "passed"),
        ("minor", "critical", "passed"),
        ("critical", "major", "failed"),
        ("major", "major", "failed"),
        ("minor", "major", "passed"),
        ("critical", "minor", "failed"),
        ("major", "minor", "failed"),
        ("minor", "minor", "failed"),
        ("critical", "none", "passed"),
        ("major", "none", "passed"),
        ("minor", "none", "passed"),
    ],
)
def test_failure_threshold_matrix(severity: str, fail_on: str, expected_status: str) -> None:
    report = report_for(severity, fail_on)

    assert report["pipeline"]["status"] == expected_status
    assert report["summary"]["modded_failures"][severity] == 1
