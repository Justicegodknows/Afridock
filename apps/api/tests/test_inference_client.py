import pytest
from afridock_api.inference.client import _api_base_for, _is_configured
from afridock_api.inference.profiles import get_profile_registry


@pytest.fixture(autouse=True)
def _clear_settings_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """NIM's endpoint is per-deployment settings, not a static profiles.yaml
    value — isolate each test from whatever happens to be in a developer's
    real .env."""
    from afridock_api import config

    config.get_settings.cache_clear()
    monkeypatch.setenv("NVIDIA_NIM_API_KEY", "")
    monkeypatch.setenv("NVIDIA_NIM_BASE_URL", "")
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
