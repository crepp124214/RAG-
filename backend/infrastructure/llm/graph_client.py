from __future__ import annotations

import json
import re

from dashscope import Generation

from backend.app.exceptions import AppError


_JSON_FENCE_PATTERN = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL | re.IGNORECASE)


def _normalize_json_content(content: object) -> str:
    if isinstance(content, list):
        content = "".join(str(item) for item in content)
    text = str(content).strip()
    fence_match = _JSON_FENCE_PATTERN.match(text)
    if fence_match:
        return fence_match.group(1).strip()
    return text


class QwenGraphExtractorClient:
    def __init__(self, *, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def extract_triples(self, *, text: str) -> list[dict[str, object]]:
        response = Generation.call(
            model=self.model,
            api_key=self.api_key,
            result_format="message",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "请从文本中提取三元组，输出 JSON 数组，元素字段为 "
                        "subject,predicate,object,entity_type。"
                    ),
                },
                {"role": "user", "content": text},
            ],
        )
        status_code = getattr(response, "status_code", 500)
        if status_code != 200:
            message = getattr(response, "message", "graph extraction request failed")
            raise AppError(f"图谱抽取失败: {message}", code="graph_extraction_failed", status_code=502)

        output = getattr(response, "output", {}) or {}
        choices = output.get("choices", []) if isinstance(output, dict) else getattr(output, "choices", [])
        if not choices:
            return []
        first_choice = choices[0]
        message = first_choice.get("message", {}) if isinstance(first_choice, dict) else getattr(first_choice, "message", {})
        content = message.get("content", "[]") if isinstance(message, dict) else getattr(message, "content", "[]")
        try:
            parsed = json.loads(_normalize_json_content(content))
        except json.JSONDecodeError:
            return []
        return parsed if isinstance(parsed, list) else []
