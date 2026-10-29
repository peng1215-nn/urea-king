from logging.config import fileConfig
import os
from dotenv import load_dotenv
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from database import Base
import core.models  # noqa: F401  确保 platform_users 表注册进 metadata
from poker.models import User
from poker.models import Group
from poker.models import UserGroupRole
from poker.models import InvitationCode
from poker.models import AuditLog
from poker.models import Announcement


load_dotenv()


config = context.config


database_url = os.getenv(
    "DATABASE_URL"
)

if not database_url:
    raise ValueError(
        "DATABASE_URL is not set. Please configure it in .env or environment variables."
    )


if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://",
        "postgresql://",
        1,
    )


config.set_main_option(
    "sqlalchemy.url",
    database_url,
)


if config.config_file_name is not None:
    fileConfig(config.config_file_name)


target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option(
        "sqlalchemy.url"
    )

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(
            config.config_ini_section,
            {},
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()

else:
    run_migrations_online()