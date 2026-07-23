"""E1's "Tenant isolation on login" scenario: two orgs exist, and a user
from one can never reach the other's resources — verified against the
real, live-Postgres-enforced RLS policies (migrations 0001/0002), not a
mocked query layer.
"""

import httpx
from afridock_api.main import app

from tests.conftest import signup_verify_login


def _second_client() -> httpx.AsyncClient:
    """A separate client (own cookie jar) for the "other org" side of an
    isolation test — same in-process app, independent session."""
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


async def test_conversations_are_scoped_to_the_authenticated_users_org(
    async_client: httpx.AsyncClient,
) -> None:
    await signup_verify_login(async_client, "Alpha Corp", "alpha")
    create_response = await async_client.post("/conversations", json={})
    assert create_response.status_code == 201, create_response.text
    alpha_conversation_id = create_response.json()["id"]

    beta_client = _second_client()
    try:
        await signup_verify_login(beta_client, "Beta Inc", "beta")

        beta_list = await beta_client.get("/conversations")
        assert beta_list.json() == []

        beta_direct_access = await beta_client.get(
            f"/conversations/{alpha_conversation_id}/messages"
        )
        assert beta_direct_access.status_code == 404
    finally:
        await beta_client.aclose()


async def test_org_members_are_scoped_to_the_authenticated_users_org(
    async_client: httpx.AsyncClient,
) -> None:
    alpha = await signup_verify_login(async_client, "Alpha Members Co", "alpha-members")

    beta_client = _second_client()
    try:
        beta = await signup_verify_login(beta_client, "Beta Members Co", "beta-members")

        alpha_members = (await async_client.get("/organizations/current/members")).json()
        beta_members = (await beta_client.get("/organizations/current/members")).json()

        assert [m["email"] for m in alpha_members] == [alpha["email"]]
        assert [m["email"] for m in beta_members] == [beta["email"]]
    finally:
        await beta_client.aclose()
