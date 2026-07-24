import json
import time
import uuid
from collections.abc import AsyncIterator
from decimal import Decimal

import anyio
import litellm
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from afridock_api.auth.dependencies import current_active_user, get_org_session, require_role
from afridock_api.db.models.conversation import Conversation
from afridock_api.db.models.enums import MessageRole, MessageStatus, UserRole
from afridock_api.db.models.message import Message
from afridock_api.db.models.organization import Organization
from afridock_api.db.models.provider import InferenceUsageLog
from afridock_api.db.models.user import User
from afridock_api.db.session import org_scoped_transaction
from afridock_api.inference.client import InferenceClient, StreamResult
from afridock_api.inference.errors import InferenceError
from afridock_api.inference.fallback import FallbackChain
from afridock_api.inference.profiles import ModelProfileRegistry, get_profile_registry

logger = structlog.get_logger()
router = APIRouter(tags=["conversations"])
inference_client = InferenceClient()

_PREVIEW_LENGTH = 140
_DEFAULT_TITLE = "New conversation"


class CreateConversationRequest(BaseModel):
    model_profile: str | None = None


class CreateConversationResponse(BaseModel):
    id: uuid.UUID


class ConversationOut(BaseModel):
    id: uuid.UUID
    title: str
    preview: str
    modelProfile: str
    messageCount: int
    updatedAt: str


class MessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    modelProfile: str | None
    status: str


class SendMessageRequest(BaseModel):
    content: str
    model_profile: str


def _message_status_out(status_: MessageStatus) -> str:
    return "error" if status_ == MessageStatus.ERROR else "complete"


def _estimated_cost_usd(
    registry: ModelProfileRegistry, model_profile: str, prompt_tokens: int, completion_tokens: int
) -> Decimal:
    """CLAUDE.md's #1 constraint made visible: every open-source/self-hosted
    profile prices to $0 here (see profiles.yaml), so the audit trail itself
    proves the constraint rather than just asserting it — a real dollar
    figure only ever appears for a commercial (opted-in) profile."""
    if model_profile not in registry:
        return Decimal("0")
    profile = registry.get(model_profile)
    cost = (prompt_tokens / 1000) * profile.input_cost_per_1k_tokens + (
        completion_tokens / 1000
    ) * profile.output_cost_per_1k_tokens
    return Decimal(str(round(cost, 6)))


async def _get_conversation_or_404(
    session: AsyncSession, user: User, conversation_id: uuid.UUID
) -> Conversation:
    result = await session.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.org_id == user.org_id,
            Conversation.user_id == user.id,
            Conversation.is_deleted.is_(False),
        )
    )
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="conversation not found")
    return conversation


@router.post(
    "/conversations", response_model=CreateConversationResponse, status_code=status.HTTP_201_CREATED
)
async def create_conversation(
    body: CreateConversationRequest,
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.USER)),
    session: AsyncSession = Depends(get_org_session),
) -> CreateConversationResponse:
    registry = get_profile_registry()
    default_profile = body.model_profile or registry.default_chain[0]
    if default_profile not in registry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"unknown model profile: {default_profile!r}",
        )
    conversation = Conversation(
        org_id=user.org_id,
        user_id=user.id,
        default_model_id=default_profile,
    )
    session.add(conversation)
    await session.flush()
    return CreateConversationResponse(id=conversation.id)


@router.get("/conversations", response_model=list[ConversationOut])
async def list_conversations(
    q: str = "",
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_org_session),
) -> list[ConversationOut]:
    """Personal history, scoped to this user within their org (E4's "results
    are scoped to the user's organization only" is satisfied a fortiori — a
    user's own conversations are always a subset of their org's) — matches
    the plan's chat-history model (per-user, not team-shared history).
    """
    stmt = select(Conversation).where(
        Conversation.org_id == user.org_id,
        Conversation.user_id == user.id,
        Conversation.is_deleted.is_(False),
    )
    if q:
        ts_query = func.plainto_tsquery("english", q)
        stmt = stmt.where(Conversation.search_tsv.op("@@")(ts_query)).order_by(
            func.ts_rank(Conversation.search_tsv, ts_query).desc()
        )
    else:
        stmt = stmt.order_by(Conversation.updated_at.desc())

    conversations = (await session.execute(stmt)).scalars().all()

    out: list[ConversationOut] = []
    for conversation in conversations:
        # One extra query per conversation — acceptable at MVP scale
        # (dozens, not thousands, of conversations per user); revisit with
        # a joined/aggregated query if that stops being true.
        count_result = await session.execute(
            select(func.count(Message.id)).where(Message.conversation_id == conversation.id)
        )
        message_count = count_result.scalar_one()
        latest_result = await session.execute(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        latest = latest_result.scalar_one_or_none()
        preview = (latest.content[:_PREVIEW_LENGTH] if latest else "") or ""
        model_profile = (
            latest.model_id if latest and latest.model_id else conversation.default_model_id
        ) or ""
        out.append(
            ConversationOut(
                id=conversation.id,
                title=conversation.title or _DEFAULT_TITLE,
                preview=preview,
                modelProfile=model_profile,
                messageCount=message_count,
                updatedAt=conversation.updated_at.isoformat(),
            )
        )
    return out


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageOut])
async def list_messages(
    conversation_id: uuid.UUID,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_org_session),
) -> list[MessageOut]:
    conversation = await _get_conversation_or_404(session, user, conversation_id)
    result = await session.execute(
        select(Message)
        .where(
            Message.conversation_id == conversation.id,
            Message.role.in_([MessageRole.USER, MessageRole.ASSISTANT]),
        )
        .order_by(Message.created_at)
    )
    return [
        MessageOut(
            id=message.id,
            role=message.role.value,
            content=message.content,
            modelProfile=message.model_id,
            status=_message_status_out(message.status),
        )
        for message in result.scalars().all()
    ]


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: uuid.UUID,
    body: SendMessageRequest,
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.USER)),
) -> StreamingResponse:
    """Deliberately does not use `Depends(get_org_session)`: FastAPI tears
    down `yield`-dependencies as soon as this function *returns* the
    StreamingResponse object, before Starlette actually iterates the
    generator to send the body — so a dependency-injected session would
    already be closed by the time `event_stream` below runs. Instead, each
    phase (pre-stream setup, post-stream persistence) opens its own short
    `org_scoped_transaction`, self-contained and independent of FastAPI's
    response lifecycle.
    """
    registry = get_profile_registry()
    if body.model_profile not in registry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"unknown model profile: {body.model_profile!r}",
        )

    async with org_scoped_transaction(user.org_id) as session:
        conversation = await _get_conversation_or_404(session, user, conversation_id)
        org = await session.get(Organization, user.org_id)
        allow_commercial = bool(org.allow_commercial_fallback) if org else False

        if conversation.title is None:
            conversation.title = body.content[:_PREVIEW_LENGTH]

        history_result = await session.execute(
            select(Message)
            .where(
                Message.conversation_id == conversation.id,
                Message.role.in_([MessageRole.USER, MessageRole.ASSISTANT]),
            )
            .order_by(Message.created_at)
        )
        llm_messages = [
            {"role": message.role.value, "content": message.content}
            for message in history_result.scalars().all()
        ]
        llm_messages.append({"role": "user", "content": body.content})

        session.add(
            Message(
                org_id=user.org_id,
                conversation_id=conversation.id,
                role=MessageRole.USER,
                content=body.content,
            )
        )
    # `conversation` is a detached instance past this point (session closed
    # at the `async with` exit) — only its already-loaded `.id` is used below.
    conversation_id = conversation.id

    chain_profiles = [body.model_profile] + [
        name for name in registry.default_chain if name != body.model_profile
    ]
    chain = FallbackChain(chain_profiles, registry, allow_commercial=allow_commercial)

    async def persist_assistant_message(
        content: str,
        model_profile: str | None,
        litellm_model: str | None,
        error: str | None,
        latency_ms: int,
    ) -> None:
        # Shielded: SlowAPIMiddleware is a Starlette BaseHTTPMiddleware,
        # which runs this whole request in an anyio task group that
        # monitors for client disconnect and cancels its scope when the
        # client goes away — including this generator's `finally` block
        # (see event_stream below). Without shielding, the *new* awaits
        # this function performs (opening a fresh transaction) would be
        # cancelled immediately too, silently losing the reply exactly
        # the same way as if `finally` weren't there at all.
        with anyio.CancelScope(shield=True):
            async with org_scoped_transaction(user.org_id) as session:
                if error is not None:
                    session.add(
                        Message(
                            org_id=user.org_id,
                            conversation_id=conversation_id,
                            role=MessageRole.ASSISTANT,
                            content=content,
                            status=MessageStatus.ERROR,
                            error=error,
                        )
                    )
                    session.add(
                        InferenceUsageLog(
                            org_id=user.org_id,
                            user_id=user.id,
                            request_id=str(uuid.uuid4()),
                            model_profile=model_profile or "unknown",
                            litellm_model=litellm_model or "unknown",
                            latency_ms=latency_ms,
                            status="error",
                        )
                    )
                else:
                    assert model_profile is not None
                    assert litellm_model is not None
                    # Estimated, not provider-returned: the Gherkin says "an
                    # estimated cost is computed" — exact usage isn't
                    # available in the streaming path without provider-
                    # specific stream_options support not every target here
                    # (self-hosted Ollama/vLLM included) honors.
                    prompt_tokens = litellm.token_counter(  # type: ignore[attr-defined]
                        model=litellm_model, messages=llm_messages
                    )
                    completion_tokens = litellm.token_counter(  # type: ignore[attr-defined]
                        model=litellm_model, text=content
                    )
                    session.add(
                        Message(
                            org_id=user.org_id,
                            conversation_id=conversation_id,
                            role=MessageRole.ASSISTANT,
                            content=content,
                            model_provider=(
                                registry.get(model_profile).provider
                                if model_profile in registry
                                else "stub"
                            ),
                            model_id=model_profile,
                        )
                    )
                    session.add(
                        InferenceUsageLog(
                            org_id=user.org_id,
                            user_id=user.id,
                            request_id=str(uuid.uuid4()),
                            model_profile=model_profile,
                            litellm_model=litellm_model,
                            prompt_tokens=prompt_tokens,
                            completion_tokens=completion_tokens,
                            total_tokens=prompt_tokens + completion_tokens,
                            cost_usd=_estimated_cost_usd(
                                registry, model_profile, prompt_tokens, completion_tokens
                            ),
                            latency_ms=latency_ms,
                            status="ok",
                        )
                    )

    async def event_stream() -> AsyncIterator[str]:
        result = StreamResult()
        content_parts: list[str] = []
        error_message: str | None = None
        started_at = time.monotonic()
        # The assistant's reply is persisted in `finally`, not only after a
        # clean finish: if the client disconnects mid-stream (navigates
        # away, aborts the fetch), Starlette/uvicorn cancels this generator
        # via GeneratorExit at its current `yield` — code after the
        # streaming loop would never run, silently losing whatever had
        # already been generated. `finally` runs on that path too, so
        # partial (or complete) content is never lost.
        try:
            async for delta in inference_client.stream(llm_messages, chain, result):
                content_parts.append(delta)
                yield f"data: {json.dumps({'event': 'message', 'delta': delta})}\n\n"
        except InferenceError as exc:
            error_message = str(exc)
            yield f"data: {json.dumps({'event': 'error', 'message': error_message})}\n\n"
        finally:
            latency_ms = int((time.monotonic() - started_at) * 1000)
            await persist_assistant_message(
                "".join(content_parts),
                result.model_profile,
                result.litellm_model,
                error_message,
                latency_ms,
            )

        if error_message is None:
            assert result.model_profile is not None
            if result.model_profile != body.model_profile:
                logger.warning(
                    "inference.fallback_used",
                    requested=body.model_profile,
                    used=result.model_profile,
                    conversation_id=str(conversation_id),
                )
            end_payload = {"event": "message_end", "model_profile": result.model_profile}
            yield f"data: {json.dumps(end_payload)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
