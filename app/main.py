from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.routers import menu_router
from app.db.config import get_database_settings


def upgrade_database(connection: Connection) -> None:
    config = Config(str(Path(__file__).resolve().parent.parent / "alembic.ini"))
    config.attributes["connection"] = connection
    command.upgrade(config, "head")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_database_settings()
    engine = create_async_engine(
        settings.sqlalchemy_url,
        pool_pre_ping=True,
    )
    try:
        async with engine.begin() as connection:
            await connection.run_sync(upgrade_database)

        app.state.db_engine = engine
        app.state.session_factory = async_sessionmaker(
            engine,
            expire_on_commit=False,
        )
        yield
    finally:
        await engine.dispose()


app = FastAPI(title="Rybaltika API", lifespan=lifespan)
app.include_router(menu_router)
