from __future__ import annotations

from dataclasses import dataclass


MAX_GRAPH_FIELD_LENGTH = 255


@dataclass(frozen=True)
class GraphTriple:
    subject: str
    predicate: str
    object: str
    source_chunk_id: str
    document_id: str
    page_number: int | None
    entity_type: str | None = None


@dataclass(frozen=True)
class GraphEvidence:
    relation_id: str
    document_id: str
    document_name: str
    chunk_id: str
    content: str
    page_number: int | None
    relation_label: str
    entity_path: str
    score: float


class GraphTripleExtractionService:
    def __init__(self, *, extractor_client: object) -> None:
        self.extractor_client = extractor_client

    def extract_from_chunk(
        self,
        *,
        chunk_id: str,
        document_id: str,
        page_number: int | None,
        content: str,
    ) -> list[GraphTriple]:
        raw_triples = self.extractor_client.extract_triples(text=content)
        normalized: list[GraphTriple] = []
        seen: set[tuple[str, str, str, str]] = set()

        for item in raw_triples:
            subject = self._normalize_text(item.get("subject"))
            predicate = self._normalize_text(item.get("predicate"))
            obj = self._normalize_text(item.get("object"))
            entity_type = self._normalize_text(item.get("entity_type"))
            if not subject or not predicate or not obj:
                continue
            dedupe_key = (subject.casefold(), predicate.casefold(), obj.casefold(), chunk_id)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            normalized.append(
                GraphTriple(
                    subject=subject,
                    predicate=predicate,
                    object=obj,
                    source_chunk_id=chunk_id,
                    document_id=document_id,
                    page_number=page_number,
                    entity_type=entity_type,
                )
            )

        return normalized

    def _normalize_text(self, value: object) -> str | None:
        if value is None:
            return None
        text = " ".join(str(value).split()).strip()
        if not text or len(text) > MAX_GRAPH_FIELD_LENGTH:
            return None
        return text
