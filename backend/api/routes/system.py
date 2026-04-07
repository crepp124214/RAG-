from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from backend.api.schemas.response import success_response
from backend.app.services.system_service import build_readiness_report


router = APIRouter(tags=['system'])


@router.get('/health')
async def health_check(request: Request) -> dict[str, object]:
    settings = request.app.state.settings
    return success_response(
        message='服务运行正常',
        data={
            'status': 'ok',
            'app_name': settings.app_name,
            'app_env': settings.app_env,
            'llm_mode': settings.llm_mode,
        },
    )


@router.get('/ready')
async def readiness_check(request: Request) -> JSONResponse:
    report = build_readiness_report(
        settings=request.app.state.settings,
        db_engine=request.app.state.db_engine,
    )
    return JSONResponse(
        status_code=report.http_status,
        content=success_response(
            message='服务就绪状态已返回',
            data=report.to_payload(),
        ),
    )
