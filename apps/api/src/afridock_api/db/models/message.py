import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import Computed, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from afridock_api.db.base import Base
from afridock_api.db.models.enums import MessageRole, MessageStatus

if TYPE_CHECKING:
    from afridock_api.db.models.conversation import Conversation

# Placeholder — set to the chosen embedding model's actual output dimension
# when E4 (conversation search) picks one; 1536 matches common
# OpenAI-compatible embedding endpoints reachable via LiteLLM.
EMBEDDING_DIM = 1536


class Message(Base):
    """One row per conversational turn (user, assistant, system, or tool).

    Departs from Dify's query/answer-pair-per-row Message (api/models/model.py)
    specifically so each row can carry its own model_provider/model_id — plan
    E2's "Model switching at conversation level" requires that earlier
    messages keep their original attribution, which falls out naturally here
    since attribution lives on the message, not the conversation.
    parent_message_id is a genuine self-referential FK (Dify's equivalent
    column has no FK constraint) to support regenerate/branch trees.
    """

    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_org_conversation_created", "org_id", "conversation_id", "created_at"),
        Index("ix_messages_content_tsv", "content_tsv", postgresql_using="gin"),
        Index(
            "ix_messages_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    # Denormalized from conversations.org_id so RLS applies directly to this
    # table too, without requiring a join on every query.
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    parent_message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="SET NULL")
    )

    role: Mapped[MessageRole] = mapped_column(
        SAEnum(
            MessageRole,
            native_enum=False,
            length=16,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Per-message attribution — source of truth for "which model answered
    # this", independent of the conversation's current default model.
    model_provider: Mapped[str | None] = mapped_column(String(64))
    model_id: Mapped[str | None] = mapped_column(String(128))

    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    estimated_cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(12, 6), default=Decimal("0"), server_default="0"
    )
    latency_ms: Mapped[int | None] = mapped_column(Integer)

    status: Mapped[MessageStatus] = mapped_column(
        SAEnum(
            MessageStatus,
            native_enum=False,
            length=16,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=MessageStatus.NORMAL,
        server_default=MessageStatus.NORMAL.value,
    )
    error: Mapped[str | None] = mapped_column(Text)

    # Postgres-generated (STORED) from `content` — always in sync, no
    # trigger needed for the per-row case (contrast conversations.search_tsv,
    # which aggregates across rows and does need a trigger; see migration).
    content_tsv: Mapped[str | None] = mapped_column(
        TSVECTOR, Computed("to_tsvector('english', content)", persisted=True)
    )
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
