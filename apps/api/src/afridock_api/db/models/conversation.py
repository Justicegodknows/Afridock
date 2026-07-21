import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Index, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from afridock_api.db.base import Base
from afridock_api.db.models.enums import ConversationStatus

if TYPE_CHECKING:
    from afridock_api.db.models.message import Message


class Conversation(Base):
    """A chat conversation, scoped to a single organization and owner.

    Schema loosely follows Dify's Conversation (api/models/model.py) with two
    deliberate departures: org_id is a first-class column (not resolved
    transitively through an App table) so Postgres row-level security can
    enforce tenant isolation directly on this table, and there's no
    query/answer-pair-per-row shape — Afridock stores one row per turn in
    `messages` instead (see message.py) so per-message model attribution and
    FTS/embedding indexing are straightforward.

    org_id/user_id are plain UUID columns without FK constraints for now —
    the organizations/users tables land with Phase 1 E1 (auth & orgs). Add
    the FK constraints once those tables exist; the RLS policy in the
    migration already assumes org_id is populated correctly by the app layer.
    """

    __tablename__ = "conversations"
    __table_args__ = (
        Index("ix_conversations_org_updated", "org_id", "updated_at"),
        Index("ix_conversations_search_tsv", "search_tsv", postgresql_using="gin"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    title: Mapped[str | None] = mapped_column(String(255))
    default_model_provider: Mapped[str | None] = mapped_column(String(64))
    default_model_id: Mapped[str | None] = mapped_column(String(128))

    status: Mapped[ConversationStatus] = mapped_column(
        SAEnum(
            ConversationStatus,
            native_enum=False,
            length=16,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=ConversationStatus.ACTIVE,
        server_default=ConversationStatus.ACTIVE.value,
    )
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Kept in sync by a trigger that aggregates message content on
    # insert/update (see the migration) rather than computed per-query.
    search_tsv: Mapped[str | None] = mapped_column(TSVECTOR)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )
