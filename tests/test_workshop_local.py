from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCAL_WORKSHOP = ROOT / "workshop" / "local.html"


def test_local_workshop_exposes_ollama_comparison() -> None:
    content = LOCAL_WORKSHOP.read_text(encoding="utf-8")
    for expected in (
        "Model Modding · Local Dyno",
        "http://127.0.0.1:11434",
        "/api/tags",
        "/api/chat",
        "Stock model",
        "Modded build",
        "Run comparison",
        "Research Learning Companion",
        "Product Strategy Copilot",
    ):
        assert expected in content


def test_local_workshop_embeds_reference_instruction_contracts() -> None:
    content = LOCAL_WORKSHOP.read_text(encoding="utf-8")
    for path in (
        ROOT / "mods/personality/socratic-teacher/instructions/system.md",
        ROOT / "mods/safety/citation-guardian/instructions/system.md",
    ):
        instructions = path.read_text(encoding="utf-8")
        for line in instructions.splitlines():
            if line.startswith("- "):
                assert line[2:] in content


def test_local_workshop_only_targets_loopback() -> None:
    content = LOCAL_WORKSHOP.read_text(encoding="utf-8")
    assert "const HOST='http://127.0.0.1:11434'" in content
    assert "https://" not in content
    assert "analytics" in content.lower()
