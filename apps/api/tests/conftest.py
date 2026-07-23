import asyncio
import uuid
from collections.abc import AsyncIterator, Iterator

import httpx
import pytest
from afridock_api.config import get_settings
from afridock_api.main import app
from fastapi.testclient import TestClient
from fastapi_users.jwt import generate_jwt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


@pytest.fixture(scope="session")
def event_loop() -> Iterator[asyncio.AbstractEventLoop]:
    """One event loop for the whole test session, not pytest-asyncio's
    per-function default: db/session.py's asyncpg engine/pool is a
    module-level singleton created once at import time, bound to whichever
    loop is running then — reusing it from a *different* loop per test
    (the default) raises "Event loop is closed" once more than one
    DB-touching async test runs in the same process.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncIterator[httpx.AsyncClient]:
    """Talks to the real app (full middleware stack, real Postgres/Redis via
    docker compose's network) through an in-process ASGI transport — no
    server process needed, but nothing about auth/RLS/persistence is
    mocked. Cookies persist across requests on the same client instance,
    matching the browser's `credentials: "include"` behavior."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def unique_email(label: str) -> str:
    """A fresh email per test run — there's no ephemeral per-test database in
    this environment (tests run against the same dev Postgres via docker
    compose), so uniqueness avoids colliding with a prior run's data instead
    of relying on cleanup."""
    return f"{label}-{uuid.uuid4().hex[:12]}@example.com"


async def fetch_user_row(email: str) -> dict[str, object] | None:
    """Reads directly via the superuser (migrations) connection, bypassing
    RLS entirely — test-only: asserting on ground truth and minting tokens
    below both need this, and neither is something the app itself should
    ever do through this connection."""
    engine = create_async_engine(get_settings().migrations_database_url)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT id, email, hashed_password, org_id, role FROM users WHERE email = :e"),
                {"e": email},
            )
            row = result.mappings().one_or_none()
            return dict(row) if row is not None else None
    finally:
        await engine.dispose()


async def mint_verification_token(user_id: uuid.UUID, email: str) -> str:
    """Mirrors UserManager.request_verify's token exactly (see auth/manager.py)
    — avoids scraping the structlog-logged link out of stdout in tests."""
    settings = get_settings()
    return generate_jwt(
        {"sub": str(user_id), "email": email, "aud": "fastapi-users:verify"},
        settings.api_secret_key,
    )


async def mint_reset_password_token(user_id: uuid.UUID, hashed_password: str) -> str:
    """Mirrors UserManager.forgot_password's token exactly (see
    auth/manager.py / fastapi_users.manager.BaseUserManager.forgot_password)."""
    from fastapi_users.password import PasswordHelper

    settings = get_settings()
    password_fingerprint = PasswordHelper().hash(hashed_password)
    return generate_jwt(
        {"sub": str(user_id), "password_fgpt": password_fingerprint, "aud": "fastapi-users:reset"},
        settings.api_secret_key,
    )


STRONG_PASSWORD = "correct-horse-battery-staple"


async def signup_verify_login(
    client: httpx.AsyncClient, org_name: str, label: str
) -> dict[str, object]:
    """Full E1 happy path in one call: signup -> mint+use the verification
    token -> log in. Returns the register response body (id, org_id, role,
    ...) with the session cookie already set on `client`."""
    email = unique_email(label)
    register_response = await client.post(
        "/auth/register",
        json={"email": email, "password": STRONG_PASSWORD, "organization_name": org_name},
    )
    assert register_response.status_code == 201, register_response.text
    user = register_response.json()

    token = await mint_verification_token(uuid.UUID(user["id"]), email)
    verify_response = await client.post("/auth/verify", json={"token": token})
    assert verify_response.status_code == 200, verify_response.text

    login_response = await client.post(
        "/auth/cookie/login",
        data={"username": email, "password": STRONG_PASSWORD},
    )
    assert login_response.status_code == 204, login_response.text

    return {**user, "email": email}
