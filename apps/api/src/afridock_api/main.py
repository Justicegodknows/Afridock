from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from afridock_api.api.routes import api_keys, auth, conversations, health, organizations, usage
from afridock_api.config import get_settings
from afridock_api.logging import configure_logging

settings = get_settings()
configure_logging(settings.api_env)

app = FastAPI(title="Afridock API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Per-IP request throttling (Redis-backed so it's shared across API
# processes), applied API-wide with a generous default rather than only on
# /auth — slowapi's pre-built routers (fastapi-users) can't be decorated
# per-route like hand-written endpoints, and a single sensible default is
# simpler than threading path-specific limits through library routers.
limiter = Limiter(
    key_func=get_remote_address, storage_uri=settings.redis_url, default_limits=["60/minute"]
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
app.add_middleware(SlowAPIMiddleware)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(organizations.router)
app.include_router(organizations.settings_router)
app.include_router(api_keys.router)
app.include_router(usage.router)
app.include_router(conversations.router)
