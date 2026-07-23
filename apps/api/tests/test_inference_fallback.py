import pytest
from afridock_api.inference.errors import NoAvailableModelError
from afridock_api.inference.fallback import FallbackChain, InMemoryCooldownStore


def test_candidates_returns_all_profiles_when_none_in_cooldown() -> None:
    chain = FallbackChain(["llama-3.1-8b-instruct", "mixtral-8x7b-instruct", "claude-fallback"])

    candidates = chain.candidates()

    assert [c.name for c in candidates] == [
        "llama-3.1-8b-instruct",
        "mixtral-8x7b-instruct",
        "claude-fallback",
    ]


def test_cooldown_removes_profile_from_candidates() -> None:
    chain = FallbackChain(["llama-3.1-8b-instruct", "mixtral-8x7b-instruct"])

    chain.cooldown("llama-3.1-8b-instruct", seconds=60)

    candidates = chain.candidates()
    assert [c.name for c in candidates] == ["mixtral-8x7b-instruct"]


def test_all_profiles_in_cooldown_raises_no_available_model_error() -> None:
    store = InMemoryCooldownStore()
    chain = FallbackChain(["llama-3.1-8b-instruct"], cooldown_store=store)

    chain.cooldown("llama-3.1-8b-instruct", seconds=60)

    with pytest.raises(NoAvailableModelError):
        chain.candidates()


def test_cooldown_expires_after_the_window() -> None:
    store = InMemoryCooldownStore()
    chain = FallbackChain(["llama-3.1-8b-instruct"], cooldown_store=store)

    chain.cooldown("llama-3.1-8b-instruct", seconds=-1)  # already expired

    candidates = chain.candidates()
    assert [c.name for c in candidates] == ["llama-3.1-8b-instruct"]
