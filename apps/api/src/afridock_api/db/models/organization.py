import uuid
from datetime import datetime

from sqlalchemy import DateTime, String
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

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
