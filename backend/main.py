from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.api.error_handlers import register_error_handlers
from backend.api.router import api_router
from backend.app.settings import BackendSettings, get_backend_settings


def create_app(settings: BackendSettings | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if app.state.settings is None:
            app.state.settings = get_backend_settings()
        yield

    app = FastAPI(
        title=(settings.app_name if settings else "RAG智能文档检索助手"),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    app.state.settings = settings

    register_error_handlers(app)
    app.include_router(api_router, prefix=(settings.api_prefix if settings else "/api"))

    return app


app = create_app()
