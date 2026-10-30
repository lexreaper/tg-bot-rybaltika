from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.routers import images_router, menu_router
from app.api.routers.admin import router as hub_admin_router
from app.api.routers.content import router as content_router
from app.api.routers.public import router as hub_public_router
from app.db.config import get_database_settings
from app.db.model import Base
from app.demo import seed_demo
from app.demo_content import seed_demo_content
from app.settings import get_app_settings


def upgrade_database(connection: Connection) -> None:
    config = Config(str(Path(__file__).resolve().parent.parent / "alembic.ini"))
    config.attributes["connection"] = connection
    command.upgrade(config, "head")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    app_settings = get_app_settings()
    url = (
        app_settings.demo_database_url
        if app_settings.demo_mode
        else get_database_settings().sqlalchemy_url
    )
    engine = create_async_engine(
        url,
        pool_pre_ping=True,
    )
    try:
        # async with engine.begin() as connection:
        #     if app_settings.demo_mode:
        #         await connection.run_sync(Base.metadata.create_all)
        #     else:
        #         await connection.run_sync(upgrade_database)

        app.state.db_engine = engine
        app.state.session_factory = async_sessionmaker(
            engine,
            expire_on_commit=False,
        )
        if app_settings.demo_mode:
            async with app.state.session_factory() as session:
                await seed_demo(session)
                await seed_demo_content(session)
        yield
    finally:
        await engine.dispose()


app = FastAPI(title="Rybaltika API", lifespan=lifespan)
app.include_router(menu_router)
app.include_router(images_router)
app.include_router(content_router)
app.include_router(hub_public_router, prefix="/api/hub")
app.include_router(hub_admin_router, prefix="/api/hub")


# Serve UI and API from one origin: no frontend build or CORS needed locally.
frontend = Path(__file__).resolve().parent.parent / "frontend"
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_app_settings().cors_origins,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Admin-Token"],
)
app.mount("/assets", StaticFiles(directory=frontend / "assets"), name="assets")


@app.exception_handler(SQLAlchemyError)
async def database_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    logging.getLogger(__name__).error("Database request failed", exc_info=exc)
    return JSONResponse(
        status_code=503,
        content={"detail": "Данные временно недоступны. Попробуйте позже."},
    )


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(frontend / "index.html", headers={"Cache-Control": "no-cache"})


@app.get("/app-config", include_in_schema=False)
async def app_config():
    return {"demo_mode": get_app_settings().demo_mode}


@app.get("/design", include_in_schema=False)
async def design():
    return FileResponse(frontend / "design.html")


@app.get("/admin", include_in_schema=False)
async def content_admin():
    return FileResponse(
        frontend / "admin.html",
        headers={"Cache-Control": "no-store"},
    )
