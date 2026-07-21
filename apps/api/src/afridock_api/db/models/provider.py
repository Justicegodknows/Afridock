import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, DateTime, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from afridock_api.db.base import Base


class ProviderCredential(Base):
    """A per-organization set of encrypted credentials for one LLM provider.

    encrypted_config holds a Fernet-encrypted JSON blob (see
    inference/credentials.py) — never store plaintext API keys. Mirrors
    Dify's Provider/ProviderCredential (api/models/provider.py), scoped down
    to what Afridock's plan actually needs (no plugin-daemon indirection).
    """

    __tablename__ = "provider_credentials"
    __table_args__ = (Index("ix_provider_credentials_org_provider", "org_id", "provider"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    encrypted_config: Mapped[str] = mapped_column(String, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ModelProfileOverride(Base):
    """Per-organization override of the static profile registry
    (inference/profiles.yaml) — e.g. a custom fallback chain or a
    self-hosted vLLM endpoint URL. Mirrors Dify's TenantPreferredModelProvider
    /TenantDefaultModel (api/models/provider.py).
    """

    __tablename__ = "model_profile_overrides"
    __table_args__ = (Index("ix_model_profile_overrides_org_profile", "org_id", "profile_name"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    profile_name: Mapped[str] = mapped_column(String(64), nullable=False)
    litellm_model: Mapped[str | None] = mapped_column(String(255))
    api_base: Mapped[str | None] = mapped_column(String(255))
    default_params: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default="{}")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class InferenceUsageLog(Base):
    """Append-only audit/billing record for every LLM call (plan E6, E10).

    Kept independent of Message so billing reconciliation doesn't depend on
    the chat/conversation feature existing — background jobs and future
    Slack/WhatsApp/workflow integrations all funnel through InferenceClient
    and log here too, giving a single audit trail regardless of call site.
    """

    __tablename__ = "inference_usage_logs"
    __table_args__ = (Index("ix_inference_usage_logs_org_created", "org_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)

    model_profile: Mapped[str] = mapped_column(String(64), nullable=False)
    litellm_model: Mapped[str] = mapped_column(String(255), nullable=False)

    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(12, 6), default=Decimal("0"), server_default="0"
    )
    latency_ms: Mapped[int | None] = mapped_column(Integer)

    status: Mapped[str] = mapped_column(String(16), default="ok", server_default="ok")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
