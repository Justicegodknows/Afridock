"""Plan E5 (RBAC & API Keys): issuance, scoping, and revocation of
machine credentials. "A request is made with that key... authorized only
for that key's organization" is exercised against
GET /organizations/current/members — see auth/dependencies.py's
get_org_id_via_cookie_or_api_key for why that specific endpoint.
"""

import httpx

from tests.conftest import invite_and_login_as, second_client, signup_verify_login


async def test_admin_can_create_list_and_revoke_an_api_key(
    async_client: httpx.AsyncClient,
) -> None:
    await signup_verify_login(async_client, "API Key Co", "api-key-admin")

    create_response = await async_client.post(
        "/organizations/current/api-keys", json={"name": "CI integration"}
    )
    assert create_response.status_code == 201, create_response.text
    created = create_response.json()
    assert created["key"].startswith("afk_")
    assert created["keyPrefix"] == created["key"][:8]

    listed = (await async_client.get("/organizations/current/api-keys")).json()
    assert len(listed) == 1
    assert listed[0]["id"] == created["id"]
    assert listed[0]["keyPrefix"] == created["keyPrefix"]
    assert "key" not in listed[0]  # plaintext is never returned again

    revoke_response = await async_client.delete(f"/organizations/current/api-keys/{created['id']}")
    assert revoke_response.status_code == 204


async def test_api_key_authorizes_only_its_own_organization(
    async_client: httpx.AsyncClient,
) -> None:
    alpha_admin = await signup_verify_login(async_client, "Key Alpha", "key-alpha")
    alpha_key = (
        await async_client.post("/organizations/current/api-keys", json={"name": "alpha key"})
    ).json()["key"]

    beta_client = second_client()
    try:
        await signup_verify_login(beta_client, "Key Beta", "key-beta")

        alpha_members = (
            await beta_client.get(
                "/organizations/current/members",
                headers={"Authorization": f"Bearer {alpha_key}"},
            )
        ).json()
        assert [m["email"] for m in alpha_members] == [alpha_admin["email"]]
    finally:
        await beta_client.aclose()

    anon_client = second_client()
    try:
        no_auth_response = await anon_client.get("/organizations/current/members")
        assert no_auth_response.status_code == 401
    finally:
        await anon_client.aclose()


async def test_revoked_api_key_is_rejected(async_client: httpx.AsyncClient) -> None:
    await signup_verify_login(async_client, "Revoke Co", "revoke-admin")
    created = (
        await async_client.post("/organizations/current/api-keys", json={"name": "temp key"})
    ).json()
    raw_key = created["key"]

    anon_client = second_client()
    try:
        ok_response = await anon_client.get(
            "/organizations/current/members", headers={"Authorization": f"Bearer {raw_key}"}
        )
        assert ok_response.status_code == 200

        await async_client.delete(f"/organizations/current/api-keys/{created['id']}")

        revoked_response = await anon_client.get(
            "/organizations/current/members", headers={"Authorization": f"Bearer {raw_key}"}
        )
        assert revoked_response.status_code == 401
    finally:
        await anon_client.aclose()


async def test_non_admin_cannot_manage_api_keys(async_client: httpx.AsyncClient) -> None:
    await signup_verify_login(async_client, "Key RBAC Co", "key-rbac-admin")
    user_client = await invite_and_login_as(async_client, "user", "key-rbac-user")
    try:
        create_attempt = await user_client.post(
            "/organizations/current/api-keys", json={"name": "nope"}
        )
        assert create_attempt.status_code == 403

        list_attempt = await user_client.get("/organizations/current/api-keys")
        assert list_attempt.status_code == 403
    finally:
        await user_client.aclose()
