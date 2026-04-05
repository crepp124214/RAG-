import pytest

from backend.app.settings.config import PROJECT_ROOT, SettingsError, load_backend_settings


def test_load_backend_settings_reads_complete_values_from_env_file() -> None:
    settings = load_backend_settings(
        env_file=PROJECT_ROOT / '.env.example',
        overrides={
            'APP_ENV': 'test',
            'APP_NAME': '测试配置',
            'DASHSCOPE_API_KEY': 'test-key',
        },
    )

    assert settings.app_env == 'test'
    assert settings.app_name == '测试配置'
    assert settings.llm_mode == 'production'
    assert settings.vector_top_k == 12
    assert settings.rerank_top_n == 5
    assert settings.reranker_model == 'gte-rerank-v2'
    assert settings.file_storage_path == (PROJECT_ROOT / 'data' / 'uploads').resolve()


def test_load_backend_settings_requires_core_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ('DATABASE_URL', 'REDIS_URL', 'DASHSCOPE_API_KEY', 'API_KEY', 'FILE_STORAGE_PATH'):
        monkeypatch.delenv(key, raising=False)

    with pytest.raises(SettingsError) as exc_info:
        load_backend_settings(env_file=None, overrides={})

    assert '缺少必需环境变量' in str(exc_info.value)


def test_load_backend_settings_rejects_invalid_chunk_relationship() -> None:
    with pytest.raises(SettingsError) as exc_info:
        load_backend_settings(
            env_file=None,
            overrides={
                'DATABASE_URL': 'postgresql+psycopg://postgres:postgres@127.0.0.1:5432/rag_assistant',
                'REDIS_URL': 'redis://127.0.0.1:6379/0',
                'DASHSCOPE_API_KEY': 'test-key',
                'FILE_STORAGE_PATH': './data/uploads',
                'CHUNK_SIZE': '100',
                'CHUNK_OVERLAP': '100',
            },
        )

    assert 'CHUNK_OVERLAP' in str(exc_info.value)


def test_load_backend_settings_rejects_invalid_llm_mode() -> None:
    with pytest.raises(SettingsError) as exc_info:
        load_backend_settings(
            env_file=None,
            overrides={
                'DATABASE_URL': 'postgresql+psycopg://postgres:postgres@127.0.0.1:5432/rag_assistant',
                'REDIS_URL': 'redis://127.0.0.1:6379/0',
                'DASHSCOPE_API_KEY': 'test-key',
                'FILE_STORAGE_PATH': './data/uploads',
                'LLM_MODE': 'shadow',
            },
        )

    assert 'LLM_MODE' in str(exc_info.value)
