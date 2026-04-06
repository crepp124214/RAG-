from __future__ import annotations

from backend.app.settings import BackendSettings


def create_graph_driver(settings: BackendSettings):
    if not settings.neo4j_uri:
        return None

    try:
        from neo4j import GraphDatabase
    except ImportError:
        return None

    auth = None
    if settings.neo4j_username and settings.neo4j_password:
        auth = (settings.neo4j_username, settings.neo4j_password)
    return GraphDatabase.driver(settings.neo4j_uri, auth=auth)
