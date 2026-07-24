import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from afridock_api.db.base import Base


class ApiKey(Base):
    """A machine credential scoped to one organization (plan E5).

    Only `hashed_key` (SHA-256 of the high-entropy random token) is ever
    stored — the plaintext key is returned to the caller once, at creation,
    and never again. SHA-256 (not bcrypt/argon2) is deliberate: this hashes
    a 32-byte random token, not a user-chosen low-entropy password, so a
    slow KDF buys nothing against brute force and only adds latency.
    """

    __tablename__ = "api_keys"
    __table_args__ = (Index("ix_api_keys_org_id", "org_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    key_prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
