import types

import litellm
import pytest
from afridock_api.inference.client import (
    InferenceClient,
    _api_base_for,
    _api_key_for,
    _is_configured,
)
from afridock_api.inference.fallback import FallbackChain
from afridock_api.inference.profiles import get_profile_registry


@pytest.fixture(autouse=True)
def _clear_settings_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """NIM's endpoint is per-deployment settings, not a static profiles.yaml
    value — isolate each test from whatever happens to be in a developer's
    real .env. NVIDIA_API_KEY is blanked for the same reason: a real key may
    genuinely be configured in .env for the hosted-cloud profile."""
    from afridock_api import config

    config.get_settings.cache_clear()
    monkeypatch.setenv("NVIDIA_NIM_API_KEY", "")
    monkeypatch.setenv("NVIDIA_NIM_BASE_URL", "")
    monkeypatch.setenv("NVIDIA_API_KEY", "")
    yield
    config.get_settings.cache_clear()


def test_nvidia_nim_profile_unconfigured_when_base_url_blank() -> None:
    profile = get_profile_registry().get("llama-3.1-70b-nim")

    assert profile.api_base is None
    assert _api_base_for(profile) is None
    assert _is_configured(profile) is False


def test_nvidia_nim_profile_configured_when_base_url_set(monkeypatch: pytest.MonkeyPatch) -> None:
    from afridock_api import config

    monkeypatch.setenv("NVIDIA_NIM_BASE_URL", "http://dgx-spark.local:8000/v1")
    config.get_settings.cache_clear()

    profile = get_profile_registry().get("llama-3.1-70b-nim")

    assert _api_base_for(profile) == "http://dgx-spark.local:8000/v1"
    assert _is_configured(profile) is True


def test_ollama_profile_still_uses_its_static_api_base_not_settings() -> None:
    profile = get_profile_registry().get("llama-3.2-1b-instruct")

    assert _api_base_for(profile) == profile.api_base == "http://ollama:11434"


def test_nvidia_cloud_profile_unconfigured_when_key_blank() -> None:
    profile = get_profile_registry().get("llama-3.3-70b-nvidia")

    assert profile.api_base == "https://integrate.api.nvidia.com/v1"
    assert _is_configured(profile) is False


def test_nvidia_cloud_profile_configured_when_key_set(monkeypatch: pytest.MonkeyPatch) -> None:
    from afridock_api import config

    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-test-key")
    config.get_settings.cache_clear()

    profile = get_profile_registry().get("llama-3.3-70b-nvidia")

    assert _api_key_for(profile.provider) == "nvapi-test-key"
    assert _is_configured(profile) is True


class _FakeUsage:
    prompt_tokens = 5
    completion_tokens = 3
    total_tokens = 8


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self.choices = [types.SimpleNamespace(message=types.SimpleNamespace(content=content))]
        self.usage = _FakeUsage()


async def test_complete_defaults_cost_to_zero_when_completion_cost_raises_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression test for a real bug found against a live NVIDIA-cloud call:
    litellm.completion_cost doesn't just return None for a custom
    `openai/<name>` model string outside its pricing map (already handled
    below) — it can also raise NotFoundError. Either way, no pricing entry
    means $0 by definition for this registry, not a crash."""

    async def _fake_acompletion(**kwargs: object) -> _FakeResponse:
        return _FakeResponse("hi there")

    def _raise_not_found(**kwargs: object) -> None:
        raise litellm.exceptions.NotFoundError(
            "no pricing entry", model="openai/meta/llama-3.3-70b-instruct", llm_provider="openai"
        )

    monkeypatch.setattr(litellm, "acompletion", _fake_acompletion)
    monkeypatch.setattr(litellm, "completion_cost", _raise_not_found)

    client = InferenceClient()
    chain = FallbackChain(["llama-3.2-1b-instruct"])

    result = await client.complete([{"role": "user", "content": "hi"}], chain)

    assert result.content == "hi there"
    assert result.cost_usd == 0.0
