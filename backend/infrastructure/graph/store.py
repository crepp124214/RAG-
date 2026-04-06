from __future__ import annotations

import re
from dataclasses import asdict
from typing import Any

from backend.app.services.graph_service import GraphEvidence, GraphTriple
from backend.app.settings import BackendSettings
from backend.infrastructure.graph.client import create_graph_driver

_QUERY_TOKEN_PATTERN = re.compile(r"[\w\u4e00-\u9fff]+", re.UNICODE)
_QUERY_STOPWORDS = {"关系", "什么", "之间", "和", "与", "的", "是"}
_QUERY_SPLIT_PATTERN = re.compile(r"之间|是什么|什么|关系|和|与|的|是|吗|？|\?")
_QUERY_RELATION_MARKERS = ("依赖", "关联", "影响", "调用", "连接", "包含", "属于", "related_to")


def _split_query_token(token: str) -> list[str]:
    parts = [token]
    for marker in _QUERY_RELATION_MARKERS:
        next_parts: list[str] = []
        for part in parts:
            if marker in part:
                next_parts.extend(piece for piece in part.split(marker) if piece)
                next_parts.append(marker)
            else:
                next_parts.append(part)
        parts = next_parts
    split_parts: list[str] = []
    for part in parts:
        split_parts.extend(piece for piece in _QUERY_SPLIT_PATTERN.split(part) if piece)
    return split_parts


def _build_query_terms(query: str) -> list[str]:
    terms: list[str] = []
    seen: set[str] = set()
    for token in _QUERY_TOKEN_PATTERN.findall(query.casefold()):
        for normalized in _split_query_token(token.strip()):
            if len(normalized) < 2 or normalized in _QUERY_STOPWORDS or normalized in seen:
                continue
            terms.append(normalized)
            seen.add(normalized)
    return terms


class NullGraphStore:
    def query_relations(self, *, query: str, limit: int) -> list[GraphEvidence]:
        del query, limit
        return []

    def write_document_graph(self, *, document_id: str, triples: list[GraphTriple]) -> int:
        del document_id, triples
        return 0

    def delete_document_graph(self, *, document_id: str) -> None:
        del document_id


class GraphStore:
    def __init__(self, *, driver: Any | None) -> None:
        self.driver = driver

    def query_relations(self, *, query: str, limit: int) -> list[GraphEvidence]:
        if self.driver is None:
            return []
        query_terms = _build_query_terms(query)
        if not query_terms:
            return []

        cypher = """
        MATCH (s:Entity)-[r:RELATED_TO]->(o:Entity)
        WHERE any(term IN $query_terms WHERE
          s.normalized_name CONTAINS term OR
          o.normalized_name CONTAINS term OR
          toLower(r.predicate) CONTAINS term
        )
        RETURN r.relation_id AS relation_id,
               r.document_id AS document_id,
               r.document_name AS document_name,
               r.chunk_id AS chunk_id,
               r.content AS content,
               r.page_number AS page_number,
               r.predicate AS relation_label,
               (s.name + ' -> ' + r.predicate + ' -> ' + o.name) AS entity_path,
               1.0 AS score
        LIMIT $limit
        """
        with self.driver.session() as session:
            rows = session.run(cypher, query_terms=query_terms, limit=limit)
            return [GraphEvidence(**dict(row)) for row in rows]

    def write_document_graph(self, *, document_id: str, triples: list[GraphTriple]) -> int:
        if self.driver is None or not triples:
            return 0

        payload = [asdict(triple) for triple in triples]
        cypher = """
        UNWIND $triples AS triple
        MERGE (s:Entity {normalized_name: toLower(triple.subject)})
          ON CREATE SET s.name = triple.subject, s.entity_type = triple.entity_type
          ON MATCH SET s.name = triple.subject
        MERGE (o:Entity {normalized_name: toLower(triple.object)})
          ON CREATE SET o.name = triple.object, o.entity_type = triple.entity_type
          ON MATCH SET o.name = triple.object
        MERGE (s)-[r:RELATED_TO {
          document_id: triple.document_id,
          chunk_id: triple.source_chunk_id,
          predicate: triple.predicate,
          object_name: triple.object,
          subject_name: triple.subject
        }]->(o)
        SET r.relation_id = triple.document_id + ':' + triple.source_chunk_id + ':' + triple.predicate + ':' + triple.object,
            r.document_name = coalesce(r.document_name, ''),
            r.content = triple.subject + triple.predicate + triple.object,
            r.page_number = triple.page_number
        """
        with self.driver.session() as session:
            session.run("MATCH ()-[r:RELATED_TO {document_id: $document_id}]-() DELETE r", document_id=document_id)
            session.run(cypher, triples=payload)
        return len(triples)

    def delete_document_graph(self, *, document_id: str) -> None:
        if self.driver is None:
            return
        with self.driver.session() as session:
            session.run("MATCH ()-[r:RELATED_TO {document_id: $document_id}]-() DELETE r", document_id=document_id)
            session.run(
                "MATCH (n:Entity) WHERE NOT (n)--() DELETE n"
            )


def create_graph_store(settings: BackendSettings) -> GraphStore | NullGraphStore:
    driver = create_graph_driver(settings)
    if driver is None:
        return NullGraphStore()
    return GraphStore(driver=driver)
