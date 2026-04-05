from __future__ import annotations

from fastapi import APIRouter, Request

from backend.api.schemas.response import success_response


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
