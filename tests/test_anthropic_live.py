from __future__ import annotations

import os

import pytest

from model_modding.provider import ProviderRequest, create_provider


@pytest.mark.skipif(
    os.environ.get("MODEL_MODDING_LIVE_ANTHROPIC") != "1",
    reason="set MODEL_MODDING_LIVE_ANTHROPIC=1 to run the paid Anthropic smoke test",
)
def test_live_anthropic_smoke() -> None:
    model = os.environ.get("ANTHROPIC_SMOKE_MODEL")
    if not model:
        pytest.skip("set ANTHROPIC_SMOKE_MODEL to an allowed exact model identifier")
    provider = create_provider("anthropic")
    response = provider.generate(
        ProviderRequest(
            model=model,
            prompt="Reply with exactly: model-modding-anthropic-ok",
            timeout=30,
        )
    )
    assert "model-modding-anthropic-ok" in response.text.casefold()
    assert response.provider == "anthropic"
    assert response.model
