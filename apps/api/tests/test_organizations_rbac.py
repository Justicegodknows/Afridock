"""Extension of E1's org model the already-built Team page depends on:
inviting a member (reusing fastapi-users' reset-password flow instead of a
bespoke invite-token system — see organizations.py) and role-based
authorization (only Admins may invite/update/remove).
"""

import httpx
from afridock_api.main import app

from tests.conftest import (
    fetch_user_row,
    mint_reset_password_token,
    signup_verify_login,
    unique_email,
)


def _second_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


async def test_invite_then_reset_password_then_login(async_client: httpx.AsyncClient) -> None:
    await signup_verify_login(async_client, "Invite Co", "invite-admin")
    invitee_email = unique_email("invitee")

    invite_response = await async_client.post(
        "/organizations/current/members/invite",
        json={"emails": [invitee_email], "role": "viewer"},
    )
    assert invite_response.status_code == 200
    assert invite_response.json() == {"invited": [invitee_email]}

    members = (await async_client.get("/organizations/current/members")).json()
    invitee = next(m for m in members if m["email"] == invitee_email)
    assert invitee["role"] == "viewer"
    assert invitee["status"] == "active"  # invited users are pre-verified, see organizations.py

    row = await fetch_user_row(invitee_email)
    assert row is not None
    reset_token = await mint_reset_password_token(row["id"], row["hashed_password"])
    reset_response = await async_client.post(
        "/auth/reset-password", json={"token": reset_token, "password": "brand-new-strong-password"}
    )
    assert reset_response.status_code == 200, reset_response.text

    invitee_client = _second_client()
    try:
        login_response = await invitee_client.post(
            "/auth/cookie/login",
            data={"username": invitee_email, "password": "brand-new-strong-password"},
        )
        assert login_response.status_code == 204
    finally:
        await invitee_client.aclose()


async def test_non_admin_cannot_invite_or_remove_members(async_client: httpx.AsyncClient) -> None:
    await signup_verify_login(async_client, "RBAC Co", "rbac-admin")
    viewer_email = unique_email("rbac-viewer")
    await async_client.post(
        "/organizations/current/members/invite", json={"emails": [viewer_email], "role": "viewer"}
    )
    row = await fetch_user_row(viewer_email)
    assert row is not None
    reset_token = await mint_reset_password_token(row["id"], row["hashed_password"])
    await async_client.post(
        "/auth/reset-password", json={"token": reset_token, "password": "viewer-strong-password-1"}
    )

    viewer_client = _second_client()
    try:
        login_response = await viewer_client.post(
            "/auth/cookie/login",
            data={"username": viewer_email, "password": "viewer-strong-password-1"},
        )
        assert login_response.status_code == 204

        invite_attempt = await viewer_client.post(
            "/organizations/current/members/invite",
            json={"emails": [unique_email("should-not-exist")], "role": "user"},
        )
        assert invite_attempt.status_code == 403

        remove_attempt = await viewer_client.delete(f"/organizations/current/members/{row['id']}")
        assert remove_attempt.status_code == 403

        read_attempt = await viewer_client.get("/organizations/current/members")
        assert read_attempt.status_code == 200
    finally:
        await viewer_client.aclose()
