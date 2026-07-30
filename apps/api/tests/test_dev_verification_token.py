import httpx
import pytest

from tests.conftest import STRONG_PASSWORD, unique_email


async def test_returns_a_token_that_verify_accepts(async_client: httpx.AsyncClient) -> None:
    email = unique_email("dev-verify")
    register_response = await async_client.post(
        "/auth/register",
        json={"email": email, "password": STRONG_PASSWORD, "organization_name": "Dev Verify Co"},
    )
    assert register_response.status_code == 201, register_response.text

    token_response = await async_client.post("/auth/dev/verification-token", json={"email": email})
    assert token_response.status_code == 200, token_response.text
    token = token_response.json()["token"]

    verify_response = await async_client.post("/auth/verify", json={"token": token})
    assert verify_response.status_code == 200, verify_response.text
    assert verify_response.json()["is_verified"] is True

    login_response = await async_client.post(
        "/auth/cookie/login",
        data={"username": email, "password": STRONG_PASSWORD},
    )
    assert login_response.status_code == 204


async def test_unknown_email_returns_404(async_client: httpx.AsyncClient) -> None:
    response = await async_client.post(
        "/auth/dev/verification-token", json={"email": unique_email("does-not-exist")}
    )
    assert response.status_code == 404


async def test_already_verified_user_returns_400(async_client: httpx.AsyncClient) -> None:
    email = unique_email("already-verified")
    register_response = await async_client.post(
        "/auth/register",
        json={
            "email": email,
            "password": STRONG_PASSWORD,
            "organization_name": "Already Verified Co",
        },
    )
    assert register_response.status_code == 201, register_response.text

    first_token = (
        await async_client.post("/auth/dev/verification-token", json={"email": email})
    ).json()["token"]
    await async_client.post("/auth/verify", json={"token": first_token})

    second_response = await async_client.post("/auth/dev/verification-token", json={"email": email})
    assert second_response.status_code == 400


async def test_returns_404_outside_local_env(
    async_client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from afridock_api import config

    email = unique_email("non-local-env")
    register_response = await async_client.post(
        "/auth/register",
        json={"email": email, "password": STRONG_PASSWORD, "organization_name": "Non Local Co"},
    )
    assert register_response.status_code == 201, register_response.text

    monkeypatch.setenv("API_ENV", "staging")
    config.get_settings.cache_clear()
    try:
        response = await async_client.post("/auth/dev/verification-token", json={"email": email})
        assert response.status_code == 404
    finally:
        config.get_settings.cache_clear()
