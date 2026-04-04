from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    code: str = Field(..., description="稳定错误码")
    detail: str = Field(..., description="可读错误说明")


class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Any | None = None
    error: ErrorBody | None = None


def success_response(*, message: str, data: Any | None = None) -> dict[str, Any]:
    return {
        "success": True,
        "message": message,
        "data": data,
        "error": None,
    }


def error_response(*, message: str, code: str, detail: str) -> dict[str, Any]:
    return {
        "success": False,
        "message": message,
        "data": None,
        "error": {
            "code": code,
            "detail": detail,
        },
    }
