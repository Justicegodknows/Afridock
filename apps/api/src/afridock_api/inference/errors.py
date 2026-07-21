class InferenceError(Exception):
    """Base class for all normalized inference errors.

    Callers (chat endpoints, background jobs) should only ever catch these —
    provider SDK exceptions raised by LiteLLM are translated into this
    hierarchy at the InferenceClient boundary and must never leak past it.
    """


class InferenceRateLimitError(InferenceError):
    """The provider rejected the request due to rate limiting."""


class InferenceAuthError(InferenceError):
    """The configured credentials were rejected or are missing."""


class InferenceConnectionError(InferenceError):
    """The provider was unreachable (timeout, DNS, connection reset)."""


class InferenceQuotaExceededError(InferenceError):
    """The organization has exhausted its plan's inference quota."""


class NoAvailableModelError(InferenceError):
    """Every model in the fallback chain failed or is in cooldown."""
