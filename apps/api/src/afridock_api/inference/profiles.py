from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

_PROFILES_PATH = Path(__file__).parent / "profiles.yaml"


class ModelProfile(BaseModel):
    """A named, versioned mapping from an Afridock-facing model name to a
    LiteLLM model string plus its default params and per-1k-token pricing.

    Analogous to Dify's provider.yaml-driven AIModelEntity, but static and
    checked into the repo rather than installed at runtime as a plugin —
    Afridock doesn't need third-party-installable providers, only a small,
    known set of models per the execution plan.
    """

    name: str
    provider: str
    litellm_model: str
    input_cost_per_1k_tokens: float
    output_cost_per_1k_tokens: float
    default_params: dict[str, Any] = {}
    # Self-hosted endpoint (e.g. Ollama's `http://ollama:11434`) — passed as
    # litellm's `api_base`. None for hosted providers (HF/Anthropic/OpenAI),
    # which resolve their own endpoint from the model string.
    api_base: str | None = None
    # Drives the org-level commercial-fallback gate (see CLAUDE.md's #1
    # constraint and inference/fallback.py's FallbackChain): true only for
    # non-zero-marginal-cost providers an org must explicitly opt into.
    is_commercial: bool = False


class ModelProfileRegistry:
    def __init__(self, profiles: dict[str, ModelProfile], default_chain: list[str]) -> None:
        self._profiles = profiles
        self.default_chain = default_chain

    def get(self, name: str) -> ModelProfile:
        try:
            return self._profiles[name]
        except KeyError:
            raise KeyError(f"Unknown model profile: {name!r}") from None

    def __contains__(self, name: str) -> bool:
        return name in self._profiles

    def all(self) -> list[ModelProfile]:
        return list(self._profiles.values())

    @classmethod
    def from_yaml(cls, path: Path = _PROFILES_PATH) -> "ModelProfileRegistry":
        raw = yaml.safe_load(path.read_text())
        profiles = {
            name: ModelProfile(name=name, **config) for name, config in raw["profiles"].items()
        }
        return cls(profiles, default_chain=raw.get("default_chain", []))


_default_registry: ModelProfileRegistry | None = None


def get_profile_registry() -> ModelProfileRegistry:
    """Process-wide singleton, lazily loaded from profiles.yaml.

    An organization-specific override table (model_profile_override, see
    db/models/provider.py) can layer on top of this at the call site; this
    registry is only the static, repo-wide default.
    """
    global _default_registry
    if _default_registry is None:
        _default_registry = ModelProfileRegistry.from_yaml()
    return _default_registry
