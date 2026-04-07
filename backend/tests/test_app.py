from __future__ import annotations

from backend.app.exceptions import AppError
from backend.app.services.system_service import ReadinessComponent, ReadinessSummary
from backend.tests.support import create_initialized_test_client


def test_health_check_returns_success_payload() -> None:
    with create_initialized_test_client() as (client, _, _):
        response = client.get('/api/health')

    assert response.status_code == 200
    payload = response.json()
    assert payload['success'] is True
    assert payload['data']['status'] == 'ok'
    assert payload['data']['app_env'] == 'test'
    assert payload['data']['llm_mode'] == 'production'


def test_health_check_exposes_acceptance_mode_when_enabled() -> None:
    with create_initialized_test_client(overrides={'LLM_MODE': 'acceptance'}) as (client, _, _):
        response = client.get('/api/health')

    assert response.status_code == 200
    payload = response.json()
    assert payload['data']['llm_mode'] == 'acceptance'


def test_ready_check_returns_ready_payload() -> None:
    with create_initialized_test_client() as (client, _, _):
        from backend.api.routes import system

        original = system.build_readiness_report
        system.build_readiness_report = lambda **_: ReadinessSummary(
            app_name='RAG测试应用',
            app_env='test',
            llm_mode='production',
            status='ready',
            ready=True,
            degraded=False,
            http_status=200,
            components=[
                ReadinessComponent(name='database', label='PostgreSQL', status='ready', required=True),
                ReadinessComponent(name='redis', label='Redis', status='ready', required=True),
            ],
        )
        try:
            response = client.get('/api/ready')
        finally:
            system.build_readiness_report = original

    assert response.status_code == 200
    payload = response.json()
    assert payload['success'] is True
    assert payload['data']['status'] == 'ready'
    assert payload['data']['ready'] is True


def test_ready_check_returns_degraded_payload_without_blocking() -> None:
    with create_initialized_test_client() as (client, _, _):
        from backend.api.routes import system

        original = system.build_readiness_report
        system.build_readiness_report = lambda **_: ReadinessSummary(
            app_name='RAG测试应用',
            app_env='test',
            llm_mode='production',
            status='degraded',
            ready=True,
            degraded=True,
            http_status=200,
            components=[
                ReadinessComponent(name='database', label='PostgreSQL', status='ready', required=True),
                ReadinessComponent(name='neo4j', label='Neo4j', status='failed', required=False),
            ],
        )
        try:
            response = client.get('/api/ready')
        finally:
            system.build_readiness_report = original

    assert response.status_code == 200
    payload = response.json()
    assert payload['success'] is True
    assert payload['data']['status'] == 'degraded'
    assert payload['data']['degraded'] is True


def test_ready_check_returns_503_when_required_dependency_is_not_ready() -> None:
    with create_initialized_test_client() as (client, _, _):
        from backend.api.routes import system

        original = system.build_readiness_report
        system.build_readiness_report = lambda **_: ReadinessSummary(
            app_name='RAG测试应用',
            app_env='test',
            llm_mode='production',
            status='not_ready',
            ready=False,
            degraded=False,
            http_status=503,
            components=[
                ReadinessComponent(
                    name='database',
                    label='PostgreSQL',
                    status='failed',
                    required=True,
                    detail='connection refused',
                ),
            ],
        )
        try:
            response = client.get('/api/ready')
        finally:
            system.build_readiness_report = original

    assert response.status_code == 503
    payload = response.json()
    assert payload['success'] is True
    assert payload['data']['status'] == 'not_ready'
    assert payload['data']['ready'] is False


def test_missing_route_returns_standard_error_response() -> None:
    with create_initialized_test_client() as (client, _, _):
        response = client.get('/api/not-found')

    assert response.status_code == 404
    payload = response.json()
    assert payload['success'] is False
    assert payload['error']['code'] == 'not_found'


def test_docs_page_is_available() -> None:
    with create_initialized_test_client() as (client, _, _):
        response = client.get('/docs')

    assert response.status_code == 200
    assert 'Swagger UI' in response.text


def test_cors_preflight_is_supported_for_local_frontend_origins() -> None:
    with create_initialized_test_client() as (client, _, _):
        response = client.options(
            '/api/health',
            headers={
                'Origin': 'http://127.0.0.1:4174',
                'Access-Control-Request-Method': 'GET',
            },
        )

    assert response.status_code == 200
    assert response.headers['access-control-allow-origin'] == 'http://127.0.0.1:4174'
    assert 'GET' in response.headers['access-control-allow-methods']


def test_app_error_uses_standard_error_shape() -> None:
    with create_initialized_test_client() as (client, _, _):
        @client.app.get('/api/test/app-error')
        async def raise_app_error() -> None:
            raise AppError('业务校验失败', code='app_error', status_code=409)

        response = client.get('/api/test/app-error')

    assert response.status_code == 409
    payload = response.json()
    assert payload['success'] is False
    assert payload['error']['code'] == 'app_error'
    assert payload['error']['detail'] == '业务校验失败'


def test_unhandled_error_is_converted_to_standard_error_response() -> None:
    with create_initialized_test_client() as (client, _, _):
        @client.app.get('/api/test/system-error')
        async def raise_system_error() -> None:
            raise RuntimeError('unexpected')

        response = client.get('/api/test/system-error')

    assert response.status_code == 500
    payload = response.json()
    assert payload['success'] is False
    assert payload['error']['code'] == 'internal_server_error'
