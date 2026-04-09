from logging.config import fileConfig
import asyncio
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

from alembic import context
""" 
Bổ sung các package cần thiết cho async migration
"""
from app.database import Base
from app.models import Blog, Comment, User
import os

""" 
Tải biến môi trường từ .env
"""
load_dotenv(Path(__file__).parent.parent / ".env") 

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
""" 
Bổ sung biến môi trường
Dùng DOCKER_DATABASE_URL khi chạy qua Docker Compose, fallback DATABASE_URL
"""
config.set_main_option("sqlalchemy.url", os.getenv("DOCKER_DATABASE_URL") or os.getenv("DATABASE_URL"))
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# target_metadata = None
""" 
target_metadata cần trỏ vào đúng metadata thật của project ! 
"""
target_metadata = Base.metadata

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
    """
    Chuyển đổi URL từ postgresql:// sang postgresql+asyncpg:// vì dùng async driver
    """
    if url and url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url and url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (async).

    In this scenario we need to create an async Engine
    and associate a connection with the context.
    Vì project dùng async SQLAlchemy, migration cũng dùng async pattern

    """
   
    async def do_run_migrations():
        url = config.get_main_option("sqlalchemy.url")
        
        """
        Chuyển đổi URL async nếu là postgresql URL
        """
        if url and url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url and url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        
        engine = create_async_engine(url, echo=False, future=True)

        """
        Chạy migration thông qua async connection
        """
        def do_run_migrations(connection):
            context.configure(connection=connection, target_metadata=target_metadata)

            with context.begin_transaction():
                context.run_migrations()

        async with engine.connect() as connection:
            await connection.run_sync(do_run_migrations)
        
        await engine.dispose()

    asyncio.run(do_run_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
