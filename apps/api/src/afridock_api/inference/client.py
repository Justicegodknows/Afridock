import time
from collections.abc import AsyncIterator
from typing import Any

import litellm
from pydantic import BaseModel

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


class InferenceResult(BaseModel):
    content: str
    model_profile: str
    litellm_model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    latency_ms: int


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
        last_error: Exception | None = None
        for profile in chain.candidates():
            started = time.monotonic()
            try:
                response = await litellm.acompletion(
                    model=profile.litellm_model,
                    messages=messages,
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
            cost_usd = litellm.completion_cost(completion_response=response)
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
        self, messages: list[dict[str, Any]], chain: FallbackChain
    ) -> AsyncIterator[str]:
        """Streams token deltas from the first available model in the chain.

        Only the first candidate is attempted for streaming — mid-stream
        fallback would require re-sending already-emitted tokens to the
        client, which the chat endpoint (not this client) decides how to
        handle, e.g. surface a retry action per plan E3's error-handling
        scenario rather than silently switching models mid-message.
        """
        profile = chain.candidates()[0]
        try:
            response = await litellm.acompletion(
                model=profile.litellm_model,
                messages=messages,
                stream=True,
                **profile.default_params,
            )
        except litellm.exceptions.RateLimitError as exc:
            chain.cooldown(profile.name, RATE_LIMIT_COOLDOWN_SECONDS)
            raise InferenceRateLimitError(str(exc)) from exc
        except litellm.exceptions.AuthenticationError as exc:
            raise InferenceAuthError(str(exc)) from exc
        except (litellm.exceptions.APIConnectionError, litellm.exceptions.Timeout) as exc:
            chain.cooldown(profile.name, CONNECTION_ERROR_COOLDOWN_SECONDS)
            raise InferenceConnectionError(str(exc)) from exc

        async for chunk in response:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
