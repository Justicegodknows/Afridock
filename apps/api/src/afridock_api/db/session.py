import uuid
from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from afridock_api.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, pool_pre_ping=True)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Plain, unscoped session — only for routes with no tenant to scope to
    (e.g. /healthz, and auth routes before a user/org is known)."""
    async with async_session_factory() as session:
        yield session


@asynccontextmanager
async def org_scoped_transaction(org_id: uuid.UUID) -> AsyncIterator[AsyncSession]:
    """One transaction, with `app.org_id` set for its duration so the RLS
    policies from migrations 0001/0002 apply — the backstop behind this
    session's explicit `org_id` filtering, not a replacement for it.
    `SELECT set_config(..., true)` (not `SET LOCAL app.org_id =`) because
    asyncpg's extended query protocol doesn't support parameters in a bare
    `SET` statement; `set_config` is a normal parameterized function call.
    The `true` third argument scopes it to the current transaction.

    Commits on success, rolls back on exception. Use this directly (not the
    `org_scoped_session` FastAPI dependency below) for anything that runs
    *after* a route handler returns — e.g. inside a StreamingResponse
    generator — since FastAPI tears down `yield`-dependencies as soon as
    the handler returns the response object, before a streaming body is
    actually sent, not after (see api/routes/conversations.py's
    send_message for why this matters).
    """
    async with async_session_factory() as session, session.begin():
        await session.execute(
            text("SELECT set_config('app.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )
        yield session


async def org_scoped_session(org_id: uuid.UUID) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency wrapper around org_scoped_transaction — only safe
    for routes whose response is fully computed before the handler returns
    (i.e. everything except send_message's StreamingResponse)."""
    async with org_scoped_transaction(org_id) as session:
        yield session
