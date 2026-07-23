from __future__ import annotations

import os

import pytest

from model_modding.provider import GenerationOptions, ProviderRequest, create_provider


@pytest.mark.skipif(
    os.environ.get("MODEL_MODDING_LIVE_OPENAI") != "1",
    reason="set MODEL_MODDING_LIVE_OPENAI=1 to run the paid OpenAI smoke test",
)
def test_live_openai_smoke() -> None:
    model = os.environ.get("OPENAI_SMOKE_MODEL")
    if not model:
        pytest.skip("set OPENAI_SMOKE_MODEL to an allowed exact model identifier")
    provider = create_provider("openai")
    response = provider.generate(
        ProviderRequest(
            model=model,
            prompt="Reply with exactly: model-modding-openai-ok",
            options=GenerationOptions(max_tokens=32),
            timeout=30,
        )
    )
    assert "model-modding-openai-ok" in response.text.casefold()
    assert response.provider == "openai"
    assert response.model
