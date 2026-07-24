"""E2 (inference orchestrator wiring) / E3 (chat streaming + persistence) /
E4 (history & search) against the real endpoint, real Postgres, and the
inference stub-fallback path.

This deliberately forces stub mode (`SELF_HOSTED_PROVIDERS = set()`) rather
than relying on whatever the environment's actual state is: a real Ollama
container is genuinely reachable in local dev/CI now (see CLAUDE.md's #1
constraint), so without this override the assistant's reply would be a real,
non-deterministic Llama completion instead of the canned stub text this
test asserts on — this test is about the SSE envelope/persistence plumbing,
not about which model answered.
"""

import httpx
import pytest

from tests.conftest import signup_verify_login


@pytest.fixture(autouse=True)
def _force_stub_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("afridock_api.inference.client.SELF_HOSTED_PROVIDERS", set())


async def test_send_message_streams_and_persists_the_conversation(
    async_client: httpx.AsyncClient,
) -> None:
    await signup_verify_login(async_client, "Chat Flow Co", "chat-flow")
    conversation_id = (await async_client.post("/conversations", json={})).json()["id"]

    async with async_client.stream(
        "POST",
        f"/conversations/{conversation_id}/messages",
        json={"content": "Hello Afridock", "model_profile": "llama-3.1-8b-instruct"},
    ) as response:
        assert response.status_code == 200
        events = [line async for line in response.aiter_lines() if line.startswith("data:")]

    assert any('"event": "message"' in e for e in events)
    assert any('"event": "message_end"' in e for e in events)
    assert '"model_profile": "stub-local-dev"' in events[-1]

    messages = (await async_client.get(f"/conversations/{conversation_id}/messages")).json()
    assert [m["role"] for m in messages] == ["user", "assistant"]
    assert messages[0]["content"] == "Hello Afridock"
    assert messages[1]["modelProfile"] == "stub-local-dev"
    assert messages[1]["status"] == "complete"


async def test_conversations_list_and_search(async_client: httpx.AsyncClient) -> None:
    await signup_verify_login(async_client, "Search Co", "search-flow")
    conversation_id = (await async_client.post("/conversations", json={})).json()["id"]
    async with async_client.stream(
        "POST",
        f"/conversations/{conversation_id}/messages",
        json={"content": "a message about zebras", "model_profile": "llama-3.1-8b-instruct"},
    ) as response:
        async for _ in response.aiter_lines():
            pass

    listed = (await async_client.get("/conversations")).json()
    assert len(listed) == 1
    assert listed[0]["id"] == conversation_id
    assert listed[0]["messageCount"] == 2

    match = (await async_client.get("/conversations", params={"q": "zebras"})).json()
    assert [c["id"] for c in match] == [conversation_id]

    no_match = (await async_client.get("/conversations", params={"q": "giraffes"})).json()
    assert no_match == []


async def test_unknown_model_profile_is_rejected(async_client: httpx.AsyncClient) -> None:
    await signup_verify_login(async_client, "Bad Profile Co", "bad-profile")
    conversation_id = (await async_client.post("/conversations", json={})).json()["id"]

    response = await async_client.post(
        f"/conversations/{conversation_id}/messages",
        json={"content": "hi", "model_profile": "not-a-real-model"},
    )

    assert response.status_code == 400
