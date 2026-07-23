from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_pr_execution_is_read_only_and_commenting_is_trusted() -> None:
    execution = read(".github/workflows/evidence-pr-summary.yml")
    comment = read(".github/workflows/evidence-pr-comment.yml")

    assert "pull_request:" in execution
    assert "contents: read" in execution
    assert "pull-requests: write" not in execution
    assert "actions/checkout@v4" in execution
    assert "scripts/generate_ci_evidence.py" in execution
    assert "actions/upload-artifact@v4" in execution

    assert "workflow_run:" in comment
    assert 'workflows: ["Evidence PR summary"]' in comment
    assert "actions: read" in comment
    assert "pull-requests: write" in comment
    assert "actions/checkout" not in comment
    assert "actions/download-artifact@v4" in comment
    assert "context.payload.workflow_run.pull_requests" in comment


def test_provider_workflows_are_manual_protected_allowlisted_and_bounded() -> None:
    cloud = read(".github/workflows/provider-evidence.yml")
    ollama = read(".github/workflows/ollama-evidence.yml")

    for workflow in (cloud, ollama):
        assert "workflow_dispatch:" in workflow
        assert "environment: provider-evidence" in workflow
        assert 'default: "1"' in workflow
        assert '- "3"' in workflow
        assert '- "1024"' in workflow
        assert "--fail-on none" in workflow
        assert "validate_release_bundle" in workflow
        assert "--minimum-repetitions" in workflow
        assert "actions/upload-artifact@v4" in workflow

    assert "MODEL_MODDING_ALLOWED_MODELS" in cloud
    assert "modding validate-provider-run" in cloud
    assert "ANTHROPIC_API_KEY" in cloud
    assert "OPENAI_API_KEY" in cloud
    assert "runs-on: [self-hosted, model-modding, ollama]" in ollama
    assert "MODEL_MODDING_ALLOWED_OLLAMA_MODELS" in ollama


def test_release_evidence_and_tag_publication_are_strictly_gated() -> None:
    evidence = read(".github/workflows/release-evidence.yml")
    release = read(".github/workflows/release.yml")

    assert '"evidence/release-candidate/**/manifest.json"' in evidence
    assert '"evidence/release-candidate/**"' not in evidence
    assert "scripts/assemble_release_evidence.py" in evidence
    assert "--minimum-repetitions 3" in evidence
    assert "--minimum-cases 40" in evidence

    assert "environment: release" in release
    assert "Verify tag and package version" in release
    assert "startsWith(github.ref, 'refs/tags/v0.2')" in release
    assert "scripts/assemble_release_evidence.py" in release
    assert "--minimum-repetitions 3" in release
    assert "--minimum-cases 40" in release
    assert "gh release create" in release
