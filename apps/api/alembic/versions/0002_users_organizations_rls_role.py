"""organizations, users, deferred FK constraints, and the afridock_app role

Revision ID: 0002_users_organizations_rls_role
Revises: 0001_conversations_messages_providers
Create Date: 2026-07-23

Phase 1 E1 (Authentication & Organizations). Also fixes a real RLS gap
found while wiring this up: migration 0001's RLS policies were silent
no-ops, because Postgres superusers *and* table owners always bypass RLS
regardless of ENABLE/FORCE, and the API connects (and runs migrations) as
`afridock`, the superuser docker-compose creates via POSTGRES_USER. This
migration creates a separate, non-superuser `afridock_app` role for the
running API to connect as (see config.py's `database_url` vs
`migrations_database_url` split, and docker-compose.yml) so the existing
and new RLS policies actually apply. FORCE ROW LEVEL SECURITY is added too,
defense-in-depth for the (currently untrue, but cheap to guard against)
case where afridock_app ever became a table owner.

`revision`/`down_revision` are short ids ("0002"/"0001"), not this file's
full descriptive name — see 0001's docstring: Alembic's default
alembic_version.version_num column is VARCHAR(32), which the original
descriptive revision strings overflowed on the first live migration run.
"""

import os
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Local-dev default only — every deployed environment must set APP_DB_PASSWORD
# independently (see docker-compose.yml / .env.example), same convention as
# CREDENTIAL_ENCRYPTION_KEY in config.py.
_APP_DB_PASSWORD = os.environ.get("APP_DB_PASSWORD", "afridock_app_local_dev")

_EXISTING_RLS_TABLES = (
    "conversations",
    "messages",
    "provider_credentials",
    "model_profile_overrides",
    "inference_usage_logs",
)


def upgrade() -> None:
    escaped_password = _APP_DB_PASSWORD.replace("'", "''")
    op.execute(
        f"""
        DO $$
        BEGIN
          IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'afridock_app') THEN
            EXECUTE format(
              'CREATE ROLE afridock_app WITH LOGIN PASSWORD %L '
              'NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS',
              '{escaped_password}'
            );
          ELSE
            EXECUTE format('ALTER ROLE afridock_app WITH PASSWORD %L', '{escaped_password}');
          END IF;
          EXECUTE format('GRANT CONNECT ON DATABASE %I TO afridock_app', current_database());
        END
        $$;
        """
    )

    op.create_table(
        "organizations",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    op.create_table(
        "users",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("hashed_password", sa.String(1024), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("is_superuser", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column(
            "org_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(16), nullable=False, server_default="user"),
        sa.Column("display_name", sa.String(255)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_org_id", "users", ["org_id"])

    # Deferred FK constraints from 0001 (org_id/user_id were plain UUID
    # columns until the users/organizations tables existed).
    op.create_foreign_key(
        "fk_conversations_org_id_organizations",
        "conversations",
        "organizations",
        ["org_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_conversations_user_id_users",
        "conversations",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_messages_org_id_organizations",
        "messages",
        "organizations",
        ["org_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_provider_credentials_org_id_organizations",
        "provider_credentials",
        "organizations",
        ["org_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_model_profile_overrides_org_id_organizations",
        "model_profile_overrides",
        "organizations",
        ["org_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_inference_usage_logs_org_id_organizations",
        "inference_usage_logs",
        "organizations",
        ["org_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_inference_usage_logs_user_id_users",
        "inference_usage_logs",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Runtime grants for the app's non-superuser role. Tables above already
    # exist at this point in the migration, so `ALL TABLES IN SCHEMA public`
    # covers both the 0001 tables and the two created just above.
    op.execute("GRANT USAGE ON SCHEMA public TO afridock_app")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO afridock_app"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO afridock_app"
    )
    # afridock_app also executes the search_tsv trigger function (0001) as
    # the inserting/updating role — functions are PUBLIC-executable by
    # default, so no explicit GRANT is needed there.

    op.execute("ALTER TABLE organizations ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE organizations FORCE ROW LEVEL SECURITY")
    # Signup creates a brand-new Organization row (UserManager.create) before
    # any org context exists — the same unscoped-session window as `users`
    # below — so this needs the identical "pass through when app.org_id
    # isn't set" carve-out, or the INSERT itself is rejected as an RLS
    # violation (RLS's USING clause doubles as the INSERT check by default).
    # coalesce(..., '') = '' (not just `IS NULL`): pooled connections that
    # have ever had this custom GUC set via set_config(..., true) reset to
    # an empty string on transaction end, not back to NULL/undefined — a
    # bare `IS NULL` check only holds the very first time a given pooled
    # connection is used. CASE, not OR: Postgres doesn't guarantee
    # short-circuit evaluation of OR, so `::uuid` still runs — and errors —
    # on the empty string even when the left branch is true; CASE WHEN does
    # guarantee only one branch is evaluated.
    op.execute(
        "CREATE POLICY organizations_tenant_isolation ON organizations "
        "USING ("
        "  CASE WHEN coalesce(current_setting('app.org_id', true), '') = '' THEN true"
        "  ELSE id = current_setting('app.org_id', true)::uuid END"
        ")"
    )

    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE users FORCE ROW LEVEL SECURITY")
    # Login/registration must look a user up by email before any org
    # context exists (get_db_session, not org_scoped_session, is used
    # there) — so unlike every other table, `users` stays fully visible
    # when app.org_id hasn't been set for the session, and is scoped once
    # it has. This is what makes auth possible at all while still stopping
    # an authenticated (org-scoped) request from ever seeing another org's
    # users, even via an application bug.
    op.execute(
        "CREATE POLICY users_tenant_isolation ON users "
        "USING ("
        "  CASE WHEN coalesce(current_setting('app.org_id', true), '') = '' THEN true"
        "  ELSE org_id = current_setting('app.org_id', true)::uuid END"
        ")"
    )

    for table in _EXISTING_RLS_TABLES:
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")


def downgrade() -> None:
    for table in _EXISTING_RLS_TABLES:
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")

    op.execute("DROP POLICY IF EXISTS users_tenant_isolation ON users")
    op.execute("ALTER TABLE users NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY")

    op.execute("DROP POLICY IF EXISTS organizations_tenant_isolation ON organizations")
    op.execute("ALTER TABLE organizations NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE organizations DISABLE ROW LEVEL SECURITY")

    op.execute("REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM afridock_app")
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        "REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLES FROM afridock_app"
    )
    op.execute("REVOKE USAGE ON SCHEMA public FROM afridock_app")

    op.drop_constraint(
        "fk_inference_usage_logs_user_id_users", "inference_usage_logs", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_inference_usage_logs_org_id_organizations", "inference_usage_logs", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_model_profile_overrides_org_id_organizations",
        "model_profile_overrides",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_provider_credentials_org_id_organizations", "provider_credentials", type_="foreignkey"
    )
    op.drop_constraint("fk_messages_org_id_organizations", "messages", type_="foreignkey")
    op.drop_constraint("fk_conversations_user_id_users", "conversations", type_="foreignkey")
    op.drop_constraint("fk_conversations_org_id_organizations", "conversations", type_="foreignkey")

    op.drop_table("users")
    op.drop_table("organizations")

    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'afridock_app') THEN
            EXECUTE format('REVOKE CONNECT ON DATABASE %I FROM afridock_app', current_database());
            DROP OWNED BY afridock_app;
            DROP ROLE afridock_app;
          END IF;
        END
        $$;
        """
    )
