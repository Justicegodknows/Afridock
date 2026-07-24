"""Plan E5's RBAC Scenario Outline, asserted explicitly as a named test
(the underlying enforcement — require_role/current_active_user — has
existed since Phase 1's E1, but was never asserted against this exact
Gherkin table). One row per (role, action, expected result).
"""

import uuid

import httpx

from tests.conftest import invite_and_login_as, signup_verify_login


async def test_admin_can_invite_a_new_user(async_client: httpx.AsyncClient) -> None:
    await signup_verify_login(async_client, "RBAC Admin Invite Co", "rbac-admin-invite")

    response = await async_client.post(
        "/organizations/current/members/invite",
        json={"emails": ["someone-new@example.com"], "role": "user"},
    )

    assert response.status_code == 200


async def test_admin_can_rotate_an_api_key(async_client: httpx.AsyncClient) -> None:
    await signup_verify_login(async_client, "RBAC Admin Key Co", "rbac-admin-key")
    created = (
        await async_client.post("/organizations/current/api-keys", json={"name": "to rotate"})
    ).json()

    revoke_response = await async_client.delete(f"/organizations/current/api-keys/{created['id']}")
    recreate_response = await async_client.post(
        "/organizations/current/api-keys", json={"name": "replacement"}
    )

    assert revoke_response.status_code == 204
    assert recreate_response.status_code == 201


async def test_user_can_send_a_chat_message(async_client: httpx.AsyncClient) -> None:
    await signup_verify_login(async_client, "RBAC User Chat Co", "rbac-user-chat")
    user_client = await invite_and_login_as(async_client, "user", "rbac-user-sender")
    try:
        conversation_id = (await user_client.post("/conversations", json={})).json()["id"]

        async with user_client.stream(
            "POST",
            f"/conversations/{conversation_id}/messages",
            json={"content": "hi", "model_profile": "llama-3.2-1b-instruct"},
        ) as response:
            assert response.status_code == 200
            async for _ in response.aiter_lines():
                pass
    finally:
        await user_client.aclose()


async def test_user_cannot_change_billing_settings(async_client: httpx.AsyncClient) -> None:
    await signup_verify_login(async_client, "RBAC User Billing Co", "rbac-user-billing")
    user_client = await invite_and_login_as(async_client, "user", "rbac-user-billing-actor")
    try:
        response = await user_client.patch(
            "/organizations/current/settings", json={"allow_commercial_fallback": True}
        )
        assert response.status_code == 403
    finally:
        await user_client.aclose()


async def test_viewer_can_view_conversations(async_client: httpx.AsyncClient) -> None:
    await signup_verify_login(async_client, "RBAC Viewer View Co", "rbac-viewer-view")
    viewer_client = await invite_and_login_as(async_client, "viewer", "rbac-viewer-viewer")
    try:
        response = await viewer_client.get("/conversations")
        assert response.status_code == 200
    finally:
        await viewer_client.aclose()


async def test_viewer_cannot_send_a_chat_message(async_client: httpx.AsyncClient) -> None:
    await signup_verify_login(async_client, "RBAC Viewer Chat Co", "rbac-viewer-chat")
    viewer_client = await invite_and_login_as(async_client, "viewer", "rbac-viewer-sender")
    try:
        create_attempt = await viewer_client.post("/conversations", json={})
        assert create_attempt.status_code == 403

        send_attempt = await viewer_client.post(
            f"/conversations/{uuid.uuid4()}/messages",
            json={"content": "hi", "model_profile": "llama-3.2-1b-instruct"},
        )
        assert send_attempt.status_code == 403
    finally:
        await viewer_client.aclose()
