import uuid

import httpx

from tests.conftest import (
    STRONG_PASSWORD,
    fetch_user_row,
    mint_verification_token,
    signup_verify_login,
    unique_email,
)


async def test_weak_password_rejected(async_client: httpx.AsyncClient) -> None:
    response = await async_client.post(
        "/auth/register",
        json={
            "email": unique_email("weak-pw"),
            "password": "short",
            "organization_name": "Weak Password Org",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "REGISTER_INVALID_PASSWORD"


async def test_signup_creates_organization_and_makes_user_admin(
    async_client: httpx.AsyncClient,
) -> None:
    email = unique_email("new-admin")

    response = await async_client.post(
        "/auth/register",
        json={
            "email": email,
            "password": STRONG_PASSWORD,
            "organization_name": "Freshly Founded Co",
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["role"] == "admin"
    assert body["is_verified"] is False
    assert body["org_id"]

    row = await fetch_user_row(email)
    assert row is not None
    assert row["role"] == "admin"


async def test_login_is_rejected_until_verified_then_succeeds(
    async_client: httpx.AsyncClient,
) -> None:
    email = unique_email("verify-flow")
    register_response = await async_client.post(
        "/auth/register",
        json={"email": email, "password": STRONG_PASSWORD, "organization_name": "Verify Flow Org"},
    )
    user_id = uuid.UUID(register_response.json()["id"])

    unverified_login = await async_client.post(
        "/auth/cookie/login",
        data={"username": email, "password": STRONG_PASSWORD},
    )
    assert unverified_login.status_code == 400
    assert unverified_login.json()["detail"] == "LOGIN_USER_NOT_VERIFIED"

    token = await mint_verification_token(user_id, email)
    verify_response = await async_client.post("/auth/verify", json={"token": token})
    assert verify_response.status_code == 200
    assert verify_response.json()["is_verified"] is True

    verified_login = await async_client.post(
        "/auth/cookie/login",
        data={"username": email, "password": STRONG_PASSWORD},
    )
    assert verified_login.status_code == 204
    assert "afridock_auth" in verified_login.cookies


async def test_signup_verify_login_helper_round_trip(async_client: httpx.AsyncClient) -> None:
    """Sanity check for the shared conftest helper other test modules rely on."""
    user = await signup_verify_login(async_client, "Helper Sanity Org", "helper-sanity")

    me_response = await async_client.get("/users/me")
    assert me_response.status_code == 200
    assert me_response.json()["email"] == user["email"]
