from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
import logging

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.settings import get_app_settings
from app.db.model import Base
from app.demo import seed_demo
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.routers import menu_router, images_router
from app.db.config import get_database_settings


def upgrade_database(connection: Connection) -> None:
    config = Config(str(Path(__file__).resolve().parent.parent / "alembic.ini"))
    config.attributes["connection"] = connection
    command.upgrade(config, "head")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    app_settings = get_app_settings()
    url = app_settings.demo_database_url if app_settings.demo_mode else get_database_settings().sqlalchemy_url
    engine = create_async_engine(
        url,
        pool_pre_ping=True,
    )
    try:
        async with engine.begin() as connection:
            if app_settings.demo_mode:
                await connection.run_sync(Base.metadata.create_all)
            else:
                await connection.run_sync(upgrade_database)

        app.state.db_engine = engine
        app.state.session_factory = async_sessionmaker(
            engine,
            expire_on_commit=False,
        )
        if app_settings.demo_mode:
            async with app.state.session_factory() as session:
                await seed_demo(session)
        yield
    finally:
        await engine.dispose()


app = FastAPI(title="Rybaltika API", lifespan=lifespan)
app.include_router(menu_router)
app.include_router(images_router)


# Serve UI and API from one origin: no frontend build or CORS needed locally.
frontend = Path(__file__).resolve().parent.parent / "frontend"
app.add_middleware(CORSMiddleware, allow_origins=get_app_settings().cors_origins,
                   allow_methods=["GET"], allow_headers=["Content-Type"])
app.mount("/assets", StaticFiles(directory=frontend / "assets"), name="assets")


@app.exception_handler(SQLAlchemyError)
async def database_error(request: Request, exc: SQLAlchemyError):
    logging.getLogger(__name__).error("Database request failed", exc_info=exc)
    return JSONResponse(status_code=503, content={"detail": "Меню временно недоступно. Попробуйте позже."})


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(frontend / "index.html", headers={"Cache-Control": "no-cache"})


@app.get("/app-config", include_in_schema=False)
async def app_config():
    return {"demo_mode": get_app_settings().demo_mode}


@app.get("/design", include_in_schema=False)
async def design():
    return FileResponse(frontend / "design.html")
