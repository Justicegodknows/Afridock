"""api_keys table and Organization.allow_commercial_fallback

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-24

Phase 2 foundational slice: E5 (API keys) plus the org-level commercial-
fallback opt-in gate that enforces CLAUDE.md's #1 constraint (low-cost AI
via open-source models) — see inference/fallback.py's FallbackChain and
db/models/organization.py. `api_keys` inherits afridock_app's grants via the
`ALTER DEFAULT PRIVILEGES` migration 0002 already set up (both migrations
run as the same superuser role), so no explicit GRANT is needed here.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "organizations",
        sa.Column(
            "allow_commercial_fallback",
            sa.Boolean,
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.create_table(
        "api_keys",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "org_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("hashed_key", sa.String(64), nullable=False, unique=True),
        sa.Column("key_prefix", sa.String(16), nullable=False),
        sa.Column(
            "created_by",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_api_keys_org_id", "api_keys", ["org_id"])

    op.execute("ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE api_keys FORCE ROW LEVEL SECURITY")
    # Same "pass through when unscoped" carve-out as users/organizations in
    # 0002: API-key *authentication* itself (auth/dependencies.py) must look
    # a key up by its hash before any org context exists — the org_id is
    # exactly what that lookup determines. Once authenticated, every
    # subsequent query in the request runs with app.org_id set, so this
    # only widens the unauthenticated-lookup window, not steady-state access.
    op.execute(
        "CREATE POLICY api_keys_tenant_isolation ON api_keys "
        "USING ("
        "  CASE WHEN coalesce(current_setting('app.org_id', true), '') = '' THEN true"
        "  ELSE org_id = current_setting('app.org_id', true)::uuid END"
        ")"
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS api_keys_tenant_isolation ON api_keys")
    op.drop_table("api_keys")
    op.drop_column("organizations", "allow_commercial_fallback")
