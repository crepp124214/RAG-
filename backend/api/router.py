from fastapi import APIRouter

from backend.api.routes import chat, documents, system, tasks


api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(documents.router)
api_router.include_router(tasks.router)
api_router.include_router(chat.router)
