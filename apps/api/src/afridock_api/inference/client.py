import asyncio
import time
from collections.abc import AsyncIterator
from typing import Any

import litellm
from pydantic import BaseModel

from afridock_api.config import get_settings
from afridock_api.inference.errors import (
    InferenceAuthError,
    InferenceConnectionError,
    InferenceRateLimitError,
    NoAvailableModelError,
)
from afridock_api.inference.fallback import (
    CONNECTION_ERROR_COOLDOWN_SECONDS,
    RATE_LIMIT_COOLDOWN_SECONDS,
    FallbackChain,
)
from afridock_api.inference.profiles import ModelProfile

# Local-dev/self-hosted default when no LLM provider credential is
# configured (see .env.example's "leave blank for local stub mode"): the
# whole chat pipeline (streaming, persistence, model attribution) stays
# genuinely exercisable with zero secrets, and graduates to real inference
# the moment a key is set — no code changes either side of that line.
STUB_MODEL_PROFILE = "stub-local-dev"
STUB_LITELLM_MODEL = "stub"
_STUB_RESPONSE = (
    "This is a stub response from Afridock's local development mode — no LLM provider "
    "credentials are configured. Set HUGGINGFACE_API_TOKEN, OPENAI_API_KEY, or "
    "ANTHROPIC_API_KEY in .env to enable real inference; no code changes are needed."
)

# Providers with no cloud credential to configure — CLAUDE.md's #1
# constraint (low-cost AI via open-source models) means these are the
# preferred, real default path, not a fallback-of-last-resort: a self-hosted
# candidate is always usable regardless of which (if any) cloud API keys are
# set in this environment. `nvidia_nim` covers a self-hosted NVIDIA NIM
# instance (e.g. a DGX Spark box) — your own hardware, zero marginal
# per-token cost, same treatment as Ollama/vLLM.
SELF_HOSTED_PROVIDERS = {"ollama", "vllm", "nvidia_nim"}

# Providers whose endpoint is per-deployment (not a fixed Docker Compose
# service hostname like Ollama's) — resolved from settings at call time
# rather than hardcoded in profiles.yaml.
_DYNAMIC_API_BASE_PROVIDERS = {"nvidia_nim": "nvidia_nim_base_url"}


def _api_key_for(provider: str) -> str | None:
    settings = get_settings()
    return {
        "huggingface": settings.huggingface_api_token,
        "openai": settings.openai_api_key,
        "anthropic": settings.anthropic_api_key,
        "nvidia_nim": settings.nvidia_nim_api_key,
        "nvidia_cloud": settings.nvidia_api_key,
    }.get(provider) or None


def _api_base_for(profile: ModelProfile) -> str | None:
    """Resolves the endpoint to pass as litellm's `api_base`: static profiles
    (e.g. Ollama's fixed `http://ollama:11434`) use `profile.api_base` as-is;
    per-deployment self-hosted endpoints (e.g. a DGX Spark's NIM instance)
    have no `api_base` in profiles.yaml and are resolved from settings
    instead, since that address varies by environment/machine.
    """
    if profile.api_base is not None:
        return profile.api_base
    settings_field = _DYNAMIC_API_BASE_PROVIDERS.get(profile.provider)
    if settings_field is None:
        return None
    return getattr(get_settings(), settings_field) or None


def _is_configured(profile: ModelProfile) -> bool:
    """Whether this candidate can actually be attempted for real: a
    self-hosted profile needs a real endpoint (`api_base`) — someone must
    have actually stood up that Ollama/vLLM/NIM instance, not just declared
    the profile — otherwise it's as unconfigured as a cloud profile with no
    key. Skipping unconfigured candidates without a network call matters:
    without this, an unconfigured cloud profile would attempt a real call
    with no credentials (e.g. hitting a provider's real endpoint and
    surfacing whatever error type that provider happens to return, which may
    not be one of the normalized exceptions below).
    """
    if profile.provider in SELF_HOSTED_PROVIDERS:
        return _api_base_for(profile) is not None
    return _api_key_for(profile.provider) is not None


def _chain_has_credentials(candidates: list[ModelProfile]) -> bool:
    return any(_is_configured(profile) for profile in candidates)


class InferenceResult(BaseModel):
    content: str
    model_profile: str
    litellm_model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    latency_ms: int


class StreamResult:
    """Out-param for `InferenceClient.stream`: async generators can't
    `return` a value alongside their yields (PEP 525), so the model that
    actually answered — needed for the `message_end` SSE event and
    per-message attribution — is recorded here as streaming proceeds
    instead. Read `.model_profile`/`.litellm_model` only after the
    generator is exhausted.
    """

    def __init__(self) -> None:
        self.model_profile: str | None = None
        self.litellm_model: str | None = None


class InferenceClient:
    """Thin async wrapper around LiteLLM: the one call site every LLM
    invocation in Afridock passes through, so error normalization and
    cost/usage capture happen exactly once — mirrors Dify's ModelInstance
    (api/core/model_manager.py), minus the plugin-daemon indirection LiteLLM
    already makes unnecessary.

    Callers persist the returned InferenceResult to inference_usage_log
    (db/models/provider.py) and/or a Message row — this client stays pure
    and DB-agnostic so it's cheap to unit test.
    """

    async def complete(
        self, messages: list[dict[str, Any]], chain: FallbackChain
    ) -> InferenceResult:
        candidates = chain.candidates()
        if not _chain_has_credentials(candidates):
            return InferenceResult(
                content=_STUB_RESPONSE,
                model_profile=STUB_MODEL_PROFILE,
                litellm_model=STUB_LITELLM_MODEL,
                prompt_tokens=0,
                completion_tokens=len(_STUB_RESPONSE.split()),
                total_tokens=len(_STUB_RESPONSE.split()),
                cost_usd=0.0,
                latency_ms=0,
            )

        last_error: Exception | None = None
        for profile in candidates:
            if not _is_configured(profile):
                continue
            started = time.monotonic()
            try:
                response = await litellm.acompletion(
                    model=profile.litellm_model,
                    messages=messages,
                    api_key=_api_key_for(profile.provider),
                    api_base=_api_base_for(profile),
                    **profile.default_params,
                )
            except litellm.exceptions.RateLimitError as exc:
                chain.cooldown(profile.name, RATE_LIMIT_COOLDOWN_SECONDS)
                last_error = InferenceRateLimitError(str(exc))
                continue
            except litellm.exceptions.AuthenticationError as exc:
                chain.cooldown(profile.name, CONNECTION_ERROR_COOLDOWN_SECONDS)
                last_error = InferenceAuthError(str(exc))
                continue
            except (litellm.exceptions.APIConnectionError, litellm.exceptions.Timeout) as exc:
                chain.cooldown(profile.name, CONNECTION_ERROR_COOLDOWN_SECONDS)
                last_error = InferenceConnectionError(str(exc))
                continue

            latency_ms = int((time.monotonic() - started) * 1000)
            usage = response.usage
            # litellm.completion_cost is inconsistent for models outside its
            # pricing map (e.g. any custom `openai/<name>` string used by our
            # self-hosted/NVIDIA-cloud profiles): it returns None for some,
            # but raises NotFoundError for others (confirmed against a real
            # NVIDIA-cloud response). Either way, no registry pricing entry
            # means $0 by definition (CLAUDE.md's #1 constraint), not unknown.
            try:
                cost_usd = (
                    litellm.completion_cost(completion_response=response)  # type: ignore[attr-defined]
                    or 0.0
                )
            except litellm.exceptions.NotFoundError:
                cost_usd = 0.0
            return InferenceResult(
                content=response.choices[0].message.content or "",
                model_profile=profile.name,
                litellm_model=profile.litellm_model,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
                cost_usd=cost_usd,
                latency_ms=latency_ms,
            )

        raise last_error or NoAvailableModelError("no candidates available and no error captured")

    async def stream(
        self, messages: list[dict[str, Any]], chain: FallbackChain, result: StreamResult
    ) -> AsyncIterator[str]:
        """Streams token deltas, falling back to the next candidate on any
        error raised *before* the first token of a given candidate — mirrors
        E2's "Provider failure triggers fallback" scenario for the streaming
        path chat actually uses. Deliberately does not fall back mid-stream
        (after tokens have already reached the client): re-sending
        already-emitted content isn't this client's call to make — the chat
        endpoint decides how to surface a failed generation (plan E3's
        "Error surfaced gracefully" scenario, e.g. a retry action), not a
        silent model switch mid-message.
        """
        candidates = chain.candidates()
        if not _chain_has_credentials(candidates):
            result.model_profile = STUB_MODEL_PROFILE
            result.litellm_model = STUB_LITELLM_MODEL
            for word in _STUB_RESPONSE.split(" "):
                await asyncio.sleep(0.02)
                yield word + " "
            return

        last_error: Exception | None = None
        for profile in candidates:
            if not _is_configured(profile):
                continue
            try:
                response = await litellm.acompletion(
                    model=profile.litellm_model,
                    messages=messages,
                    api_key=_api_key_for(profile.provider),
                    api_base=_api_base_for(profile),
                    stream=True,
                    **profile.default_params,
                )
            except litellm.exceptions.RateLimitError as exc:
                chain.cooldown(profile.name, RATE_LIMIT_COOLDOWN_SECONDS)
                last_error = InferenceRateLimitError(str(exc))
                continue
            except litellm.exceptions.AuthenticationError as exc:
                chain.cooldown(profile.name, CONNECTION_ERROR_COOLDOWN_SECONDS)
                last_error = InferenceAuthError(str(exc))
                continue
            except (litellm.exceptions.APIConnectionError, litellm.exceptions.Timeout) as exc:
                chain.cooldown(profile.name, CONNECTION_ERROR_COOLDOWN_SECONDS)
                last_error = InferenceConnectionError(str(exc))
                continue

            result.model_profile = profile.name
            result.litellm_model = profile.litellm_model
            async for chunk in response:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
            return

        raise last_error or NoAvailableModelError("no candidates available and no error captured")
