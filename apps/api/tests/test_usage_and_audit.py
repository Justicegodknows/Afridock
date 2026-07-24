"""Plan E6 (Audit Logs & Cost Attribution): every chat request writes an
InferenceUsageLog row (see conversations.py's persist_assistant_message),
and the usage/audit endpoints surface it — with the audit *export*
restricted to Admins per the Gherkin ("Viewers cannot access the audit
export").
"""

import httpx

from tests.conftest import invite_and_login_as, signup_verify_login


async def _send_one_message(client: httpx.AsyncClient) -> str:
    conversation_id = (await client.post("/conversations", json={})).json()["id"]
    async with client.stream(
        "POST",
        f"/conversations/{conversation_id}/messages",
        json={"content": "hello", "model_profile": "llama-3.1-8b-instruct"},
    ) as response:
        async for _ in response.aiter_lines():
            pass
    return conversation_id


async def test_chat_request_is_audited_with_cost_and_tokens(
    async_client: httpx.AsyncClient,
) -> None:
    await signup_verify_login(async_client, "Usage Co", "usage-admin")
    await _send_one_message(async_client)

    summary = (await async_client.get("/organizations/current/usage")).json()
    assert summary["requestCount"] == 1
    assert summary["totalTokens"] > 0

    audit = (await async_client.get("/organizations/current/audit")).json()
    assert len(audit) == 1
    assert audit[0]["status"] == "ok"
    assert audit[0]["totalTokens"] > 0
    assert audit[0]["userEmail"] is not None


async def test_open_source_profile_costs_zero(async_client: httpx.AsyncClient) -> None:
    """CLAUDE.md's #1 constraint made visible in the audit trail itself."""
    await signup_verify_login(async_client, "Zero Cost Co", "zero-cost")
    await _send_one_message(async_client)

    audit = (await async_client.get("/organizations/current/audit")).json()
    assert audit[0]["costUsd"] == 0.0


async def test_admin_can_export_audit_log_csv(async_client: httpx.AsyncClient) -> None:
    await signup_verify_login(async_client, "Export Co", "export-admin")
    await _send_one_message(async_client)

    response = await async_client.get("/organizations/current/audit/export.csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    body = response.text
    assert body.startswith("id,user_email,model_profile")
    assert len(body.strip().splitlines()) == 2  # header + one row


async def test_viewer_cannot_access_audit_log_or_export(async_client: httpx.AsyncClient) -> None:
    await signup_verify_login(async_client, "Viewer Audit Co", "viewer-audit")
    viewer_client = await invite_and_login_as(async_client, "viewer", "viewer-audit-actor")
    try:
        audit_attempt = await viewer_client.get("/organizations/current/audit")
        assert audit_attempt.status_code == 403

        export_attempt = await viewer_client.get("/organizations/current/audit/export.csv")
        assert export_attempt.status_code == 403

        # The aggregate cost dashboard, unlike the raw audit trail, is open
        # to any active member.
        usage_attempt = await viewer_client.get("/organizations/current/usage")
        assert usage_attempt.status_code == 200
    finally:
        await viewer_client.aclose()
