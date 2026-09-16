"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.errors import http_exception_handler, validation_exception_handler
from app.api.router import api_router, v1_router
from app.config import get_settings
from app.db import init_db
from app.services.app_downloads_service import sync_bundled_downloads


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    (settings.data_dir / ".gitkeep").touch(exist_ok=True)
    init_db(settings)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version="0.5.10",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_exception_handler(StarletteHTTPException, http_exception_handler)
    application.add_exception_handler(RequestValidationError, validation_exception_handler)
    application.include_router(api_router)
    application.include_router(v1_router)
    downloads_dir = settings.data_dir / "downloads"
    sync_bundled_downloads(downloads_dir)
    application.mount(
        "/downloads",
        StaticFiles(directory=str(downloads_dir)),
        name="app-downloads",
    )
    return application


app = create_app()
