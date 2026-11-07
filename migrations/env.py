from logging.config import fileConfig

from alembic import context

from app import models  # noqa: F401  (registers the tables on Base.metadata)
from app.db import Base, engine

if context.config.config_file_name is not None:
    fileConfig(context.config.config_file_name)

target_metadata = Base.metadata


def run_migrations_online() -> None:
    connection = context.config.attributes.get("connection")
    if connection is not None:
        # Tests pass their own connection so the in-memory database is shared.
        context.configure(connection=connection, target_metadata=target_metadata, render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()
        return
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
