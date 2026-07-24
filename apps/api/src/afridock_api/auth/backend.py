import uuid

from fastapi_users.authentication import AuthenticationBackend, CookieTransport, JWTStrategy

from afridock_api.config import get_settings
from afridock_api.db.models.user import User

settings = get_settings()

# Two-week session, matching the cookie's max age below. Cookie (not bearer
# header) transport because apps/web's fetch wrapper (lib/api/http.ts) and
# SSE stream (lib/sse.ts) already send `credentials: "include"` everywhere —
# this needs zero frontend fetch-layer changes.
_SESSION_LIFETIME_SECONDS = 60 * 60 * 24 * 14

cookie_transport = CookieTransport(
    cookie_name="afridock_auth",
    cookie_max_age=_SESSION_LIFETIME_SECONDS,
    # Secure requires HTTPS; local dev serves plain http://localhost. Every
    # deployed environment sets API_ENV to something other than "local",
    # which is exactly when the cookie must be Secure. Both are
    # env-overridable (API_COOKIE_SECURE / API_COOKIE_SAMESITE) for the rare
    # case the frontend is cross-site from the API — see config.py.
    cookie_secure=settings.cookie_secure,
    cookie_samesite=settings.api_cookie_samesite,
)


def get_jwt_strategy() -> JWTStrategy[User, uuid.UUID]:
    return JWTStrategy(secret=settings.api_secret_key, lifetime_seconds=_SESSION_LIFETIME_SECONDS)


auth_backend = AuthenticationBackend(
    name="cookie",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)
