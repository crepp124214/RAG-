from __future__ import annotations

from backend.app.settings import BackendSettings
from backend.infrastructure.llm.acceptance_clients import (
    AcceptanceChatClient,
    AcceptanceEmbeddingClient,
    AcceptanceRerankerClient,
)
from backend.infrastructure.llm.chat_client import QwenChatClient
from backend.infrastructure.llm.embedding_client import DashScopeEmbeddingClient
from backend.infrastructure.llm.reranker_client import DashScopeRerankerClient


def create_embedding_client(settings: BackendSettings) -> object:
    if settings.llm_mode == 'acceptance':
        return AcceptanceEmbeddingClient(model=settings.embedding_model)
    return DashScopeEmbeddingClient(api_key=settings.dashscope_api_key, model=settings.embedding_model)


def create_reranker_client(settings: BackendSettings) -> object:
    if settings.llm_mode == 'acceptance':
        return AcceptanceRerankerClient(model=settings.reranker_model)
    return DashScopeRerankerClient(api_key=settings.dashscope_api_key, model=settings.reranker_model)


def create_chat_client(settings: BackendSettings) -> object:
    if settings.llm_mode == 'acceptance':
        return AcceptanceChatClient(model=settings.qwen_chat_model)
    return QwenChatClient(api_key=settings.dashscope_api_key, model=settings.qwen_chat_model)
