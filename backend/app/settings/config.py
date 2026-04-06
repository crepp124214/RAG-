from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Mapping

from dotenv import dotenv_values


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ENV_FILE = PROJECT_ROOT / '.env'
ALLOWED_APP_ENVS = {'development', 'test', 'production'}
ALLOWED_LLM_MODES = {'production', 'acceptance'}


class SettingsError(ValueError):
    """配置缺失或格式不正确时抛出的错误。"""


@dataclass(frozen=True)
class BackendSettings:
    app_env: str
    app_name: str
    api_prefix: str
    database_url: str
    redis_url: str
    dashscope_api_key: str
    llm_provider: str
    llm_mode: str
    llm_base_url: str | None
    qwen_chat_model: str
    qwen_vl_model: str
    embedding_model: str
    reranker_model: str
    search_provider: str
    search_api_key: str | None
    search_base_url: str | None
    search_timeout_seconds: float
    multimodal_enabled: bool
    max_visual_assets_per_document: int
    visual_caption_timeout_seconds: float
    file_storage_path: Path
    max_upload_size_mb: int
    chunk_size: int
    chunk_overlap: int
    vector_top_k: int
    rerank_top_n: int


def _normalize_env_file(env_file: str | Path | None) -> Path | None:
    if env_file is None:
        return None
    candidate = Path(env_file)
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate


def _load_env_values(env_file: str | Path | None) -> dict[str, str]:
    candidate = _normalize_env_file(env_file)
    if candidate is None or not candidate.exists():
        return {}
    return {
        key: value
        for key, value in dotenv_values(candidate).items()
        if key and value is not None
    }


def _merge_env_values(
    env_file: str | Path | None,
    overrides: Mapping[str, str] | None,
) -> dict[str, str]:
    values: dict[str, str] = {}
    values.update(_load_env_values(env_file))
    values.update(os.environ)
    if overrides:
        values.update({key: value for key, value in overrides.items() if value is not None})
    return values


def _require(values: Mapping[str, str], key: str) -> str:
    value = values.get(key, '').strip()
    if value:
        return value
    raise SettingsError(f'缺少必需环境变量: {key}')


def _get_int(values: Mapping[str, str], key: str, default: int) -> int:
    raw = values.get(key)
    if raw is None or str(raw).strip() == '':
        return default

    try:
        parsed = int(str(raw).strip())
    except ValueError as exc:
        raise SettingsError(f'环境变量 {key} 必须是整数') from exc

    if parsed <= 0:
        raise SettingsError(f'环境变量 {key} 必须大于 0')

    return parsed


def _get_float(values: Mapping[str, str], key: str, default: float) -> float:
    raw = values.get(key)
    if raw is None or str(raw).strip() == '':
        return default

    try:
        parsed = float(str(raw).strip())
    except ValueError as exc:
        raise SettingsError(f'环境变量 {key} 必须是数字') from exc

    if parsed <= 0:
        raise SettingsError(f'环境变量 {key} 必须大于 0')

    return parsed


def _get_bool(values: Mapping[str, str], key: str, default: bool) -> bool:
    raw = values.get(key)
    if raw is None or str(raw).strip() == '':
        return default

    normalized = str(raw).strip().lower()
    if normalized in {'1', 'true', 'yes', 'on'}:
        return True
    if normalized in {'0', 'false', 'no', 'off'}:
        return False
    raise SettingsError(f'环境变量 {key} 必须是布尔值')


def _resolve_storage_path(raw_path: str) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    return (PROJECT_ROOT / candidate).resolve()


def load_backend_settings(
    *,
    env_file: str | Path | None = DEFAULT_ENV_FILE,
    overrides: Mapping[str, str] | None = None,
) -> BackendSettings:
    values = _merge_env_values(env_file=env_file, overrides=overrides)

    app_env = values.get('APP_ENV', 'development').strip().lower()
    if app_env not in ALLOWED_APP_ENVS:
        raise SettingsError('APP_ENV 只允许为 development、test、production')

    llm_mode = values.get('LLM_MODE', 'production').strip().lower() or 'production'
    if llm_mode not in ALLOWED_LLM_MODES:
        raise SettingsError('LLM_MODE 只允许为 production、acceptance')

    dashscope_api_key = values.get('DASHSCOPE_API_KEY', '').strip() or values.get('API_KEY', '').strip()
    if not dashscope_api_key:
        raise SettingsError('缺少必需环境变量: DASHSCOPE_API_KEY')

    file_storage_path = _resolve_storage_path(_require(values, 'FILE_STORAGE_PATH'))

    chunk_size = _get_int(values, 'CHUNK_SIZE', 800)
    chunk_overlap = _get_int(values, 'CHUNK_OVERLAP', 150)
    if chunk_overlap >= chunk_size:
        raise SettingsError('CHUNK_OVERLAP 必须小于 CHUNK_SIZE')

    vector_top_k = _get_int(values, 'VECTOR_TOP_K', 12)
    rerank_top_n = _get_int(values, 'RERANK_TOP_N', 5)
    if rerank_top_n > vector_top_k:
        raise SettingsError('RERANK_TOP_N 不能大于 VECTOR_TOP_K')

    return BackendSettings(
        app_env=app_env,
        app_name=values.get('APP_NAME', 'RAG智能文档检索助手').strip() or 'RAG智能文档检索助手',
        api_prefix=values.get('API_PREFIX', '/api').strip() or '/api',
        database_url=_require(values, 'DATABASE_URL'),
        redis_url=_require(values, 'REDIS_URL'),
        dashscope_api_key=dashscope_api_key,
        llm_provider=values.get('LLM_PROVIDER', 'dashscope').strip() or 'dashscope',
        llm_mode=llm_mode,
        llm_base_url=values.get('LLM_BASE_URL', '').strip() or None,
        qwen_chat_model=values.get('QWEN_CHAT_MODEL', 'qwen-plus').strip() or 'qwen-plus',
        qwen_vl_model=values.get('QWEN_VL_MODEL', 'qwen-vl-max-latest').strip() or 'qwen-vl-max-latest',
        embedding_model=values.get('DASHSCOPE_EMBEDDING_MODEL', 'text-embedding-v1').strip() or 'text-embedding-v1',
        reranker_model=values.get('RERANKER_MODEL', 'gte-rerank-v2').strip() or 'gte-rerank-v2',
        search_provider=values.get('SEARCH_PROVIDER', 'brave').strip().lower() or 'brave',
        search_api_key=values.get('SEARCH_API_KEY', '').strip() or None,
        search_base_url=values.get('SEARCH_BASE_URL', '').strip() or None,
        search_timeout_seconds=_get_float(values, 'SEARCH_TIMEOUT_SECONDS', 8.0),
        multimodal_enabled=_get_bool(values, 'MULTIMODAL_ENABLED', True),
        max_visual_assets_per_document=_get_int(values, 'MAX_VISUAL_ASSETS_PER_DOCUMENT', 8),
        visual_caption_timeout_seconds=_get_float(values, 'VISUAL_CAPTION_TIMEOUT_SECONDS', 12.0),
        file_storage_path=file_storage_path,
        max_upload_size_mb=_get_int(values, 'MAX_UPLOAD_SIZE_MB', 50),
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        vector_top_k=vector_top_k,
        rerank_top_n=rerank_top_n,
    )


@lru_cache(maxsize=1)
def get_backend_settings() -> BackendSettings:
    return load_backend_settings()


def clear_backend_settings_cache() -> None:
    get_backend_settings.cache_clear()
