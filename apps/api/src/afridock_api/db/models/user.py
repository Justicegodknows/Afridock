import uuid
from datetime import datetime

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from afridock_api.db.base import Base
from afridock_api.db.models.enums import UserRole


class User(SQLAlchemyBaseUserTableUUID, Base):
    """Extends fastapi-users' base user table (email, hashed_password,
    is_active, is_superuser, is_verified) with the org membership and role
    Afridock's plan needs. One org per user (no membership join table) —
    E1's Gherkin only requires a user to belong to a single isolated org;
    add a join table if/when multi-org membership is ever needed.

    `org_id` has no server-side default and isn't nullable: every user is
    created either via signup (which creates a new Organization first, see
    auth/manager.py) or via an org's invite flow (org_id = inviter's org) —
    there's no valid "orgless" user.
    """

    __tablename__ = "users"

    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[UserRole] = mapped_column(
        SAEnum(
            UserRole,
            native_enum=False,
            length=16,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=UserRole.USER,
        server_default=UserRole.USER.value,
    )
    display_name: Mapped[str | None] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
