from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request

from backend.api.error_handlers import register_error_handlers
from backend.api.router import api_router
from backend.app.settings import BackendSettings, get_backend_settings
from backend.infrastructure.database import (
    check_database_connection,
    create_database_engine,
    create_session_factory,
)
from backend.infrastructure.observability import (
    configure_logging,
    log_event,
    reset_request_id,
    set_request_id,
)


logger = logging.getLogger(__name__)


def create_app(settings: BackendSettings | None = None) -> FastAPI:
    configure_logging()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if app.state.settings is None:
            app.state.settings = get_backend_settings()
        app.state.db_engine = create_database_engine(app.state.settings.database_url)
        check_database_connection(app.state.db_engine)
        app.state.db_session_factory = create_session_factory(app.state.db_engine)
        yield
        app.state.db_engine.dispose()

    app = FastAPI(
        title=(settings.app_name if settings else "RAG 智能文档检索助手"),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.db_engine = None
    app.state.db_session_factory = None

    @app.middleware("http")
    async def attach_request_id(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        token = set_request_id(request_id)
        request.state.request_id = request_id

        log_event(
            logger,
            logging.INFO,
            "request.started",
            method=request.method,
            path=request.url.path,
        )

        try:
            response = await call_next(request)
        except Exception:
            reset_request_id(token)
            raise

        response.headers["X-Request-ID"] = request_id
        log_event(
            logger,
            logging.INFO,
            "request.completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
        )
        reset_request_id(token)
        return response

    register_error_handlers(app)
    app.include_router(api_router, prefix=(settings.api_prefix if settings else "/api"))

    return app


app = create_app()
