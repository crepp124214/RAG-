from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Iterator

from backend.app.tools.base import ToolCallDecision


_ACCEPTANCE_PREFIX = '【验收模式】以下回答由本地确定性验收模式生成，仅用于验证第29步端到端链路，不代表正式模型输出。'
_TOKEN_PATTERN = re.compile(r'\w+', re.UNICODE)
_VECTOR_DIMENSION = 16


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_PATTERN.findall(text)]


def _build_vector(text: str, *, dimension: int = _VECTOR_DIMENSION) -> list[float]:
    digest = hashlib.sha256(text.encode('utf-8')).digest()
    buckets = [0.0] * dimension
    for index, value in enumerate(digest):
        bucket = index % dimension
        buckets[bucket] += (value / 255.0) - 0.5

    norm = math.sqrt(sum(item * item for item in buckets))
    if norm == 0:
        return [0.0] * dimension
    return [round(item / norm, 8) for item in buckets]


def _extract_context_lines(user_prompt: str) -> list[str]:
    return [line.strip() for line in user_prompt.splitlines() if line.strip().startswith('[')]


class AcceptanceEmbeddingClient:
    def __init__(self, *, model: str) -> None:
        self.model = model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [_build_vector(text) for text in texts]


class AcceptanceRerankerClient:
    def __init__(self, *, model: str) -> None:
        self.model = model

    def rerank(self, *, query: str, documents: list[str], top_n: int) -> list[int]:
        query_tokens = set(_tokenize(query))
        scored_indexes: list[tuple[int, tuple[int, int, int]]] = []
        for index, document in enumerate(documents):
            document_tokens = _tokenize(document)
            overlap = len(query_tokens.intersection(document_tokens))
            scored_indexes.append((index, (overlap, -len(document_tokens), -index)))

        ranked = sorted(scored_indexes, key=lambda item: item[1], reverse=True)
        return [index for index, _ in ranked[:top_n]]


class AcceptanceChatClient:
    def __init__(self, *, model: str) -> None:
        self.model = model

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        del system_prompt
        return self._build_answer(user_prompt)

    def stream_generate(self, *, system_prompt: str, user_prompt: str) -> Iterator[str]:
        del system_prompt
        answer = self._build_answer(user_prompt)
        for start in range(0, len(answer), 24):
            yield answer[start : start + 24]

    def decide_tool_call(self, *, query: str, tool_schemas: list[dict[str, object]]) -> ToolCallDecision | None:
        tool_names = {str(item.get("name", "")) for item in tool_schemas}
        lowered = query.lower()

        if "web_search" in tool_names and any(token in query or token in lowered for token in ["今天", "最新", "最近", "实时", "latest", "today"]):
            return ToolCallDecision(tool_name="web_search", arguments={"query": query, "top_k": 5})

        if "document_lookup" in tool_names and any(token in query or token in lowered for token in ["文档", "文件", "任务", "状态", "页", "document", "task"]):
            if "任务" in query or "task" in lowered:
                return ToolCallDecision(tool_name="document_lookup", arguments={"lookup_type": "status", "query": query})
            return ToolCallDecision(tool_name="document_lookup", arguments={"lookup_type": "content", "query": query, "limit": 5})

        return None

    def _build_answer(self, user_prompt: str) -> str:
        context_lines = _extract_context_lines(user_prompt)
        if not context_lines:
            return f'{_ACCEPTANCE_PREFIX}\n当前没有可用上下文，请先上传并处理文档。'

        summary_lines = context_lines[:3]
        body = '\n'.join(f'- {line}' for line in summary_lines)
        return f'{_ACCEPTANCE_PREFIX}\n我已基于已检索片段生成回答，请重点核对下面这些引用片段：\n{body}'


class AcceptanceVisionCaptionClient:
    def __init__(self, *, model: str) -> None:
        self.model = model

    def describe_image(self, *, image_path: str, asset_label: str) -> str:
        image_name = image_path.split("/")[-1].split("\\")[-1]
        return (
            f"【验收模式视觉描述】{asset_label}。"
            f"图像文件：{image_name}。"
            "该视觉内容用于验证第三阶段多模态入库、检索与引用链路。"
        )


class AcceptanceGraphExtractorClient:
    def __init__(self, *, model: str) -> None:
        self.model = model

    def extract_triples(self, *, text: str) -> list[dict[str, object]]:
        tokens = _tokenize(text)
        if len(tokens) < 2:
            return []
        if len(tokens) >= 3:
            return [
                {
                    "subject": tokens[0],
                    "predicate": "related_to",
                    "object": tokens[-1],
                    "entity_type": "concept",
                }
            ]
        return []
