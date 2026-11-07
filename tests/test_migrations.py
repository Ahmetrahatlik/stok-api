from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine

from app.db import Base


def test_migrations_match_the_models(tmp_path):
    """Running every migration on an empty database must give exactly the tables in models.py."""
    engine = create_engine(f"sqlite:///{tmp_path / 'migrated.db'}")
    config = Config("alembic.ini")
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
        diff = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    assert diff == []

    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.downgrade(config, "base")
