from afridock_api.inference.client import (
    STUB_LITELLM_MODEL,
    STUB_MODEL_PROFILE,
    InferenceClient,
    StreamResult,
)
from afridock_api.inference.fallback import FallbackChain

# Every test in this module assumes local-dev stub mode (no credentials
# configured) — guaranteed session-wide by conftest.py's
# `_no_real_inference_credentials` autouse fixture, not whatever happens to
# be in a developer's real .env.


async def test_complete_returns_stub_response_when_no_credentials_configured() -> None:
    client = InferenceClient()
    chain = FallbackChain(["llama-3.1-8b-instruct", "mixtral-8x7b-instruct", "claude-fallback"])

    result = await client.complete([{"role": "user", "content": "hi"}], chain)

    assert result.model_profile == STUB_MODEL_PROFILE
    assert result.litellm_model == STUB_LITELLM_MODEL
    assert result.cost_usd == 0.0
    assert "stub" in result.content.lower()


async def test_stream_yields_stub_tokens_and_records_the_profile_used() -> None:
    client = InferenceClient()
    chain = FallbackChain(["llama-3.1-8b-instruct"])
    result = StreamResult()

    deltas = [
        delta async for delta in client.stream([{"role": "user", "content": "hi"}], chain, result)
    ]

    assert "".join(deltas).strip() != ""
    assert result.model_profile == STUB_MODEL_PROFILE
    assert result.litellm_model == STUB_LITELLM_MODEL
