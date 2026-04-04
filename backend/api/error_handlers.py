from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.api.schemas.response import error_response
from backend.app.exceptions import AppError


logger = logging.getLogger(__name__)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(
                message="请求处理失败",
                code=exc.code,
                detail=exc.message,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=error_response(
                message="请求参数校验失败",
                code="validation_error",
                detail=str(exc),
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "not_found" if exc.status_code == 404 else "http_error"
        message = "请求的资源不存在" if exc.status_code == 404 else "请求处理失败"
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(
                message=message,
                code=code,
                detail=str(exc.detail),
            ),
        )

    @app.exception_handler(HTTPException)
    async def handle_fastapi_http_error(_: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(
                message="请求处理失败",
                code="http_error",
                detail=str(exc.detail),
            ),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled application error", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content=error_response(
                message="服务器内部错误",
                code="internal_server_error",
                detail="服务器发生未处理异常，请检查日志。",
            ),
        )
