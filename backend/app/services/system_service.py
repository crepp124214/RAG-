from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile

from sqlalchemy.engine import Engine

from backend.app.settings import BackendSettings
from backend.infrastructure.database import check_database_connection
from backend.infrastructure.graph import create_graph_driver
from backend.infrastructure.queue import check_redis_connection, create_redis_client


@dataclass(frozen=True)
class ReadinessComponent:
    name: str
    label: str
    status: str
    required: bool
    detail: str | None = None


@dataclass(frozen=True)
class ReadinessSummary:
    app_name: str
    app_env: str
    llm_mode: str
    status: str
    ready: bool
    degraded: bool
    http_status: int
    components: list[ReadinessComponent]

    def to_payload(self) -> dict[str, object]:
        return {
            'status': self.status,
            'ready': self.ready,
            'degraded': self.degraded,
            'app_name': self.app_name,
            'app_env': self.app_env,
            'llm_mode': self.llm_mode,
            'components': [asdict(component) for component in self.components],
        }


def build_readiness_summary(
    *,
    app_name: str,
    app_env: str,
    llm_mode: str,
    components: list[ReadinessComponent],
) -> ReadinessSummary:
    required_failed = any(component.required and component.status == 'failed' for component in components)
    optional_failed = any((not component.required) and component.status == 'failed' for component in components)

    if required_failed:
        status = 'not_ready'
        ready = False
        degraded = False
        http_status = 503
    elif optional_failed:
        status = 'degraded'
        ready = True
        degraded = True
        http_status = 200
    else:
        status = 'ready'
        ready = True
        degraded = False
        http_status = 200

    return ReadinessSummary(
        app_name=app_name,
        app_env=app_env,
        llm_mode=llm_mode,
        status=status,
        ready=ready,
        degraded=degraded,
        http_status=http_status,
        components=components,
    )


def build_readiness_report(*, settings: BackendSettings, db_engine: Engine) -> ReadinessSummary:
    components = [
        _check_database_component(db_engine),
        _check_redis_component(settings),
        _check_storage_component(settings.file_storage_path),
        _check_neo4j_component(settings),
    ]
    return build_readiness_summary(
        app_name=settings.app_name,
        app_env=settings.app_env,
        llm_mode=settings.llm_mode,
        components=components,
    )


def _check_database_component(db_engine: Engine) -> ReadinessComponent:
    try:
        check_database_connection(db_engine)
    except Exception as exc:  # pragma: no cover
        return ReadinessComponent(
            name='database',
            label='PostgreSQL',
            status='failed',
            required=True,
            detail=str(exc),
        )
    return ReadinessComponent(name='database', label='PostgreSQL', status='ready', required=True)


def _check_redis_component(settings: BackendSettings) -> ReadinessComponent:
    try:
        redis_client = create_redis_client(settings.redis_url)
        try:
            check_redis_connection(redis_client)
        finally:
            redis_client.close()
    except Exception as exc:  # pragma: no cover
        return ReadinessComponent(
            name='redis',
            label='Redis',
            status='failed',
            required=True,
            detail=str(exc),
        )
    return ReadinessComponent(name='redis', label='Redis', status='ready', required=True)


def _check_storage_component(storage_path: Path) -> ReadinessComponent:
    try:
        storage_path.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(dir=storage_path, prefix='ready-', delete=True):
            pass
    except Exception as exc:  # pragma: no cover
        return ReadinessComponent(
            name='storage',
            label='文件存储',
            status='failed',
            required=True,
            detail=str(exc),
        )
    return ReadinessComponent(name='storage', label='文件存储', status='ready', required=True)


def _check_neo4j_component(settings: BackendSettings) -> ReadinessComponent:
    if not settings.neo4j_uri:
        return ReadinessComponent(
            name='neo4j',
            label='Neo4j',
            status='skipped',
            required=False,
            detail='未配置 NEO4J_URI，GraphRAG 将按降级路径运行',
        )

    driver = create_graph_driver(settings)
    if driver is None:
        return ReadinessComponent(
            name='neo4j',
            label='Neo4j',
            status='failed',
            required=False,
            detail='Neo4j 驱动不可用或连接未正确初始化',
        )

    try:
        driver.verify_connectivity()
    except Exception as exc:  # pragma: no cover
        return ReadinessComponent(
            name='neo4j',
            label='Neo4j',
            status='failed',
            required=False,
            detail=str(exc),
        )
    finally:
        driver.close()

    return ReadinessComponent(name='neo4j', label='Neo4j', status='ready', required=False)
