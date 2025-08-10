from alembic import context
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlmodel import SQLModel
from pathlib import Path
import os
from sqlalchemy.engine.url import make_url

from app.models import user as _user, apikey as _apikey  # [[ ensure models are imported]]
_ = (_user, _apikey)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Make SQLite file URLs absolute relative to the directory of alembic.ini.
# This prevents failures when running Alembic from a different Current Working Directory (CWD).
def _normalize_sqlite_url(url_str: str) -> str:
    """Resolve relative SQLite file paths against alembic.ini's folder to avoid CWD issues."""
    try:
        url = make_url(url_str)
    except Exception:
        return url_str

    if url.drivername.startswith("sqlite") and url.database:
        db_path = Path(url.database)
        if not db_path.is_absolute():
            base = Path(config.config_file_name).resolve().parent if config.config_file_name else Path.cwd()
            abs_path = (base / db_path).resolve()
            return f"sqlite:///{abs_path.as_posix()}"
    return url_str

# Normalize the configured URL once so all below code (offline/online) uses an absolute path for SQLite.
# Prefer DATABASE_URL env var for overrides (e.g., testing), else use alembic.ini
_db_url = os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
if _db_url:
    config.set_main_option("sqlalchemy.url", _normalize_sqlite_url(_db_url))

# add your model's MetaData object here
# for 'autogenerate' support
# Import your SQLModel models to ensure they're registered
target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
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
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
