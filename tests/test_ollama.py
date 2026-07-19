from __future__ import annotations

import io
import json
from pathlib import Path
from urllib.error import URLError

import pytest

from model_modding.ollama import (
    compile_recipe_in_memory,
    list_models,
    run_recipe,
    stream_chat,
    validate_ollama_host,
)

ROOT = Path(__file__).resolve().parents[1]


class FakeResponse:
    def __init__(self, body: bytes = b"", lines: list[bytes] | None = None) -> None:
        self.body = body
        self.lines = lines or []

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body

    def __iter__(self):
        return iter(self.lines)


def test_compile_recipe_uses_repository_instruction_files() -> None:
    compiled = compile_recipe_in_memory(ROOT, "research-learning-companion")
    teacher = (ROOT / "mods/personality/socratic-teacher/instructions/system.md").read_text(encoding="utf-8").strip()
    citation = (ROOT / "mods/safety/citation-guardian/instructions/system.md").read_text(encoding="utf-8").strip()

    assert compiled.references == ("personality/socratic-teacher", "safety/citation-guardian")
    assert teacher in compiled.system_prompt
    assert citation in compiled.system_prompt


def test_validate_host_defaults_to_loopback_and_rejects_remote() -> None:
    assert validate_ollama_host("http://127.0.0.1:11434/") == "http://127.0.0.1:11434"
    assert validate_ollama_host("http://localhost:11434") == "http://localhost:11434"
    with pytest.raises(ValueError, match="Refusing non-loopback"):
        validate_ollama_host("https://example.com")
    assert validate_ollama_host("https://example.com", allow_remote=True) == "https://example.com"


def test_list_models_reads_ollama_tags_response() -> None:
    payload = json.dumps({"models": [{"name": "llama3.2:latest"}, {"name": "qwen3:4b"}]}).encode()

    def opener(request, timeout):
        assert request.full_url.endswith("/api/tags")
        assert timeout == 3.0
        return FakeResponse(body=payload)

    assert list_models("http://127.0.0.1:11434", opener=opener) == ["llama3.2:latest", "qwen3:4b"]


def test_stream_chat_yields_incremental_content() -> None:
    lines = [
        json.dumps({"message": {"content": "Hello"}, "done": False}).encode() + b"\n",
        json.dumps({"message": {"content": " world"}, "done": False}).encode() + b"\n",
        json.dumps({"message": {"content": ""}, "done": True}).encode() + b"\n",
    ]

    def opener(request, timeout):
        assert request.full_url.endswith("/api/chat")
        body = json.loads(request.data.decode("utf-8"))
        assert body["model"] == "llama3.2"
        assert body["messages"][0]["role"] == "system"
        assert body["messages"][1] == {"role": "user", "content": "Hi"}
        return FakeResponse(lines=lines)

    assert "".join(stream_chat("http://127.0.0.1:11434", "llama3.2", "Hi", "Be helpful", opener=opener)) == "Hello world"


def test_run_recipe_streams_response_and_reports_metadata(capsys) -> None:
    lines = [json.dumps({"message": {"content": "A modded answer."}, "done": True}).encode() + b"\n"]

    def opener(request, timeout):
        return FakeResponse(lines=lines)

    result = run_recipe(
        ROOT,
        "research-learning-companion",
        "llama3.2",
        "Explain gravity",
        opener=opener,
    )
    captured = capsys.readouterr()

    assert result == 0
    assert "Research Learning Companion" in captured.out
    assert "personality/socratic-teacher" in captured.out
    assert "A modded answer." in captured.out
    assert "Completed in" in captured.out


def test_run_recipe_handles_unavailable_ollama(capsys) -> None:
    def opener(request, timeout):
        raise URLError("connection refused")

    result = run_recipe(
        ROOT,
        "research-learning-companion",
        "llama3.2",
        "Hello",
        opener=opener,
    )
    captured = capsys.readouterr()

    assert result == 1
    assert "Could not reach Ollama" in captured.err
