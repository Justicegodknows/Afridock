import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from afridock_api.db.base import Base


class Organization(Base):
    """A tenant. Every org-scoped table (conversations, messages, provider
    credentials, users, ...) carries `org_id`, enforced by Postgres RLS
    (see alembic/versions/0002_users_organizations_rls_role.py) plus
    explicit application-layer filtering — RLS is the backstop, not the
    only mechanism.
    """

    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # CLAUDE.md's #1 constraint (low-cost AI via open-source models):
    # commercial model profiles (inference/profiles.yaml's `is_commercial`)
    # are only ever candidates in inference/fallback.py's FallbackChain when
    # this is explicitly set — an org can never be silently enrolled into a
    # real per-token bill. Admin-only toggle, see api/routes/organizations.py.
    allow_commercial_fallback: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
