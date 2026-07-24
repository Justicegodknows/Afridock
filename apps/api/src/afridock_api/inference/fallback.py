import time
from typing import Protocol

from afridock_api.inference.errors import NoAvailableModelError
from afridock_api.inference.profiles import ModelProfile, ModelProfileRegistry, get_profile_registry

# Cooldown windows mirror Dify's LBModelManager (core/model_manager.py):
# short cooldown for transient/connection errors, longer for rate limits.
RATE_LIMIT_COOLDOWN_SECONDS = 60.0
CONNECTION_ERROR_COOLDOWN_SECONDS = 10.0


class CooldownStore(Protocol):
    """Tracks which model profiles are in cooldown after a failure.

    Backed by Redis in production so cooldowns are shared across API
    processes (same idea as Dify's Redis-backed LBModelManager). The
    in-memory implementation below is process-local — swap in a Redis-backed
    store once a shared Redis client is threaded through the app the same
    way db/session.py wires the async SQLAlchemy engine.
    """

    def is_in_cooldown(self, profile_name: str) -> bool: ...

    def set_cooldown(self, profile_name: str, seconds: float) -> None: ...


class InMemoryCooldownStore:
    def __init__(self) -> None:
        self._until: dict[str, float] = {}

    def is_in_cooldown(self, profile_name: str) -> bool:
        until = self._until.get(profile_name)
        return until is not None and until > time.monotonic()

    def set_cooldown(self, profile_name: str, seconds: float) -> None:
        self._until[profile_name] = time.monotonic() + seconds


class FallbackChain:
    """Walks an ordered list of model profiles, skipping any in cooldown.

    Mirrors Dify's LBModelManager round-robin-with-cooldown pattern, but
    across *different models* (Llama -> Mixtral -> Claude) rather than across
    multiple credential sets for one model — Afridock's plan-level fallback
    (E2: "Provider failure triggers fallback") is model/provider escalation,
    not load-balancing.
    """

    def __init__(
        self,
        profile_names: list[str],
        registry: ModelProfileRegistry | None = None,
        cooldown_store: CooldownStore | None = None,
        allow_commercial: bool = False,
    ) -> None:
        self._profile_names = profile_names
        self._registry = registry or get_profile_registry()
        self._cooldown_store = cooldown_store or InMemoryCooldownStore()
        # CLAUDE.md's #1 constraint: a commercial (non-zero marginal cost)
        # profile is only ever a candidate if the organization has
        # explicitly opted in (Organization.allow_commercial_fallback) — no
        # org can be silently enrolled into a real per-token bill.
        self._allow_commercial = allow_commercial

    def candidates(self) -> list[ModelProfile]:
        all_profiles = [self._registry.get(name) for name in self._profile_names]
        available = [
            profile
            for profile in all_profiles
            if not self._cooldown_store.is_in_cooldown(profile.name)
            and (self._allow_commercial or not profile.is_commercial)
        ]
        if not available:
            raise NoAvailableModelError(
                f"no model profiles available in {self._profile_names}: all are either in "
                "cooldown, or commercial fallback is disabled for this organization"
            )
        return available

    def cooldown(self, profile_name: str, seconds: float) -> None:
        self._cooldown_store.set_cooldown(profile_name, seconds)
