from __future__ import annotations

from backend.app.services.system_service import ReadinessComponent, build_readiness_summary


def test_build_readiness_summary_returns_ready_when_required_components_are_healthy() -> None:
    summary = build_readiness_summary(
        app_name='RAG测试应用',
        app_env='test',
        llm_mode='production',
        components=[
            ReadinessComponent(name='database', label='PostgreSQL', status='ready', required=True),
            ReadinessComponent(name='redis', label='Redis', status='ready', required=True),
            ReadinessComponent(name='storage', label='文件存储', status='ready', required=True),
            ReadinessComponent(name='neo4j', label='Neo4j', status='skipped', required=False),
        ],
    )

    assert summary.status == 'ready'
    assert summary.http_status == 200
    assert summary.ready is True
    assert summary.degraded is False


def test_build_readiness_summary_returns_degraded_when_only_optional_component_fails() -> None:
    summary = build_readiness_summary(
        app_name='RAG测试应用',
        app_env='test',
        llm_mode='production',
        components=[
            ReadinessComponent(name='database', label='PostgreSQL', status='ready', required=True),
            ReadinessComponent(name='redis', label='Redis', status='ready', required=True),
            ReadinessComponent(name='storage', label='文件存储', status='ready', required=True),
            ReadinessComponent(
                name='neo4j',
                label='Neo4j',
                status='failed',
                required=False,
                detail='bolt connection failed',
            ),
        ],
    )

    assert summary.status == 'degraded'
    assert summary.http_status == 200
    assert summary.ready is True
    assert summary.degraded is True


def test_build_readiness_summary_returns_not_ready_when_required_component_fails() -> None:
    summary = build_readiness_summary(
        app_name='RAG测试应用',
        app_env='test',
        llm_mode='production',
        components=[
            ReadinessComponent(
                name='database',
                label='PostgreSQL',
                status='failed',
                required=True,
                detail='connection refused',
            ),
            ReadinessComponent(name='redis', label='Redis', status='ready', required=True),
            ReadinessComponent(name='storage', label='文件存储', status='ready', required=True),
        ],
    )

    assert summary.status == 'not_ready'
    assert summary.http_status == 503
    assert summary.ready is False
    assert summary.degraded is False
