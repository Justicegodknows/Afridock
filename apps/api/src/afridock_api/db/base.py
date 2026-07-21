from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models.

    Model modules live under db/models/ and are imported as a package from
    alembic/env.py (not here) so Alembic autogenerate sees every mapped
    class — importing them here instead would create a circular import,
    since each model module imports Base from this file.
    """
