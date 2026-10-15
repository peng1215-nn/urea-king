import os
import sys
from logging.config import fileConfig

# Ensure project root is first in sys.path so "platform" resolves to our
# package, not Python's built-in platform module.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from database import Base

# Import all models so Alembic sees every table in target_metadata
from core.models import PlatformUser  # noqa: F401
from poker.models import (  # noqa: F401
    PokerAnnouncement,
    PokerAuditLog,
    PokerChipRequest,
    PokerGame,
    PokerGamePlayer,
    PokerGroup,
    PokerInvitationCode,
    PokerUserGroupRole,
)

load_dotenv()

config = context.config

database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise ValueError("DATABASE_URL is not set.")

# Normalize Render's legacy postgres:// scheme
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# Force psycopg2 driver (SQLAlchemy 2.x defaults to psycopg v3)
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)

config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
