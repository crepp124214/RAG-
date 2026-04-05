from __future__ import annotations

from backend.app.settings.config import load_backend_settings
from backend.infrastructure.llm import (
    AcceptanceChatClient,
    AcceptanceEmbeddingClient,
    AcceptanceRerankerClient,
    DashScopeEmbeddingClient,
    DashScopeRerankerClient,
    QwenChatClient,
    create_chat_client,
    create_embedding_client,
    create_reranker_client,
)


def _build_settings(llm_mode: str):
    return load_backend_settings(
        env_file=None,
        overrides={
            'APP_ENV': 'test',
            'DATABASE_URL': 'sqlite+pysqlite:///./backend/tests/.tmp/llm-factory.sqlite3',
            'REDIS_URL': 'redis://127.0.0.1:6379/0',
            'DASHSCOPE_API_KEY': 'test-key',
            'FILE_STORAGE_PATH': './backend/tests/.tmp/uploads',
            'LLM_MODE': llm_mode,
        },
    )


def test_factory_returns_dashscope_clients_in_production_mode() -> None:
    settings = _build_settings('production')

    assert isinstance(create_embedding_client(settings), DashScopeEmbeddingClient)
    assert isinstance(create_reranker_client(settings), DashScopeRerankerClient)
    assert isinstance(create_chat_client(settings), QwenChatClient)


def test_factory_returns_acceptance_clients_in_acceptance_mode() -> None:
    settings = _build_settings('acceptance')

    assert isinstance(create_embedding_client(settings), AcceptanceEmbeddingClient)
    assert isinstance(create_reranker_client(settings), AcceptanceRerankerClient)
    assert isinstance(create_chat_client(settings), AcceptanceChatClient)
