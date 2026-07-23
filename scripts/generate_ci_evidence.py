from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from model_modding.builds import canonical_json_bytes
from model_modding.evidence import response_record, write_evidence_bundle
from model_modding.evidence_comparison import (
    build_compatibility_matrix,
    compare_evidence,
    comparison_markdown,
    matrix_markdown,
)
from model_modding.provider import ProviderResponse, ProviderUsage
from model_modding.release_pipeline import (
    activate_baseline,
    build_pr_summary,
    check_release_readiness,
    readiness_markdown,
    write_aggregate,
)

RECIPE = "trusted-document-explainer"
MOD = "safety/deadline-guardian"
CASE = "deadline-case"


def response(provider: str, model: str) -> ProviderResponse:
    return ProviderResponse(
        provider=provider,
        model=model,
        text="The response is due within 14 calendar days.",
        latency_seconds=0.01,
        requested_options={"temperature": 0},
        effective_options={"temperature": 0},
        finish_reason="completed",
        usage=ProviderUsage(input_tokens=8, output_tokens=8, total_tokens=16),
        metadata={"endpoint": f"https://{provider}.invalid", "synthetic": True},
    )


def evaluation(model: str) -> dict:
    invariant = {
        "kind": "preserve",
        "invariant": "deadline",
        "severity": "critical",
        "description": "Preserve the exact deadline.",
        "passed": True,
        "checks": [],
    }
    result = {
        "passed": True,
        "checks": [],
        "invariant_checks": [invariant],
        "invariant_failures": [],
        "source_comparisons": [],
        "source_comparison_failures": [],
        "failures": [],
    }
    return {
        "schema_version": "0.4",
        "evaluator": {
            "name": "deterministic-source-invariant-evaluator",
            "version": "0.3.0",
            "layers": ["legacy_checks", "invariant_checks", "source_comparison"],
        },
        "recipe": RECIPE,
        "model": model,
        "summary": {
            "cases": 40,
            "stock_passed": 40,
            "modded_passed": 40,
            "stock_failures": {"critical": 0, "major": 0, "minor": 0},
            "modded_failures": {"critical": 0, "major": 0, "minor": 0},
        },
        "pipeline": {
            "status": "passed",
            "fail_on": "critical",
            "blocking_failure_count": 0,
            "blocking_failures": [],
        },
        "failures": {"stock": [], "modded": []},
        "cases": [
            {
                "mod": MOD,
                "case": CASE,
                "prompt": "The response is due within 14 calendar days.",
                "stock": result,
                "modded": result,
            }
        ],
    }


def bundle(root: Path, output: Path, provider: str, model: str, repetition: int) -> Path:
    model_response = response(provider, model)
    prompt = "The response is due within 14 calendar days."
    records = [
        response_record(
            identifier="evaluation:1:stock",
            role="stock",
            prompt=prompt,
            system_prompt="",
            response=model_response,
            case=CASE,
            mod=MOD,
        ),
        response_record(
            identifier="evaluation:1:modded",
            role="modded",
            prompt=prompt,
            system_prompt="synthetic behavioural instructions",
            response=model_response,
            case=CASE,
            mod=MOD,
        ),
    ]
    return write_evidence_bundle(
        root,
        RECIPE,
        output,
        bundle_type="evaluation",
        runtime={
            "provider": provider,
            "endpoint": f"https://{provider}.invalid",
            "requested_options": {"temperature": 0},
            "evidence_scope": "synthetic-ci-contract",
        },
        requested_models=[model],
        records=records,
        evaluation=evaluation(model),
        created_at=f"2026-07-23T13:00:0{repetition}Z",
    )


def write_json_markdown(directory: Path, stem: str, report: dict, markdown: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{stem}.json").write_bytes(canonical_json_bytes(report))
    (directory / f"{stem}.md").write_text(markdown, encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output.resolve()
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    baseline_source = bundle(root, output / "baseline-source", "ollama", "ci-contract-model", 1)
    baseline = activate_baseline(
        root,
        baseline_source,
        output / "reviewed-baseline",
        reviewer="Model Modding maintainers",
        scope="synthetic CI comparison-contract baseline",
        notes="This baseline validates comparison plumbing only and is not provider compatibility evidence.",
    )
    candidate = bundle(root, output / "candidate", "ollama", "ci-contract-model", 2)
    comparison = compare_evidence(root, baseline / "evidence", candidate, fail_on="critical")
    write_json_markdown(output / "comparison", "comparison", comparison, comparison_markdown(comparison))

    bundles = []
    representatives = []
    for provider in ("ollama", "anthropic", "openai"):
        model = f"{provider}-ci-contract-model"
        for repetition in range(1, 4):
            current = bundle(root, output / "runs" / provider / f"run-{repetition}", provider, model, repetition)
            bundles.append(current)
            if repetition == 1:
                representatives.append(current)

    aggregate_directory, aggregate = write_aggregate(
        root,
        bundles,
        output / "aggregate",
        minimum_repetitions=3,
        require_zero_critical=True,
    )
    matrix = build_compatibility_matrix(root, representatives)
    write_json_markdown(output / "matrix", "matrix", matrix, matrix_markdown(matrix))
    readiness = check_release_readiness(
        root,
        aggregate_directory / "aggregate.json",
        output / "matrix" / "matrix.json",
    )
    write_json_markdown(output / "readiness", "readiness", readiness, readiness_markdown(readiness))

    summary = build_pr_summary(
        comparison=comparison,
        matrix=matrix,
        aggregate=aggregate,
        readiness=readiness,
    )
    banner = (
        "> **Synthetic CI contract evidence only.** These results validate the evidence pipeline and do not establish real provider or model compatibility.\n\n"
    )
    (output / "pr-summary.md").write_text(banner + summary, encoding="utf-8", newline="\n")
    print(output / "pr-summary.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
