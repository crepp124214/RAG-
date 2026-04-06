from __future__ import annotations

from pathlib import Path

from dashscope import MultiModalConversation

from backend.app.exceptions import AppError


class QwenVisionCaptionClient:
    def __init__(self, *, api_key: str, model: str, timeout_seconds: float) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    def describe_image(self, *, image_path: str, asset_label: str) -> str:
        normalized_path = Path(image_path).resolve()
        response = MultiModalConversation.call(
            model=self.model,
            api_key=self.api_key,
            request_timeout=self.timeout_seconds,
            messages=[
                {
                    "role": "system",
                    "content": [
                        {
                            "text": "你是文档视觉理解助手。请用简洁中文描述图像中的关键信息，优先保留图表结论、标题、坐标轴、图例和显著数字。不要编造无法确认的细节。"
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {"image": f"file://{normalized_path.as_posix()}"},
                        {"text": f"请描述这张文档视觉内容：{asset_label}"},
                    ],
                },
            ],
        )
        return self._extract_text(response)

    def _extract_text(self, response: object) -> str:
        status_code = getattr(response, "status_code", 500)
        if status_code != 200:
            message = getattr(response, "message", "vision request failed")
            raise AppError(f"视觉描述失败: {message}", code="visual_caption_failed", status_code=502)

        output = getattr(response, "output", {}) or {}
        choices = output.get("choices", []) if isinstance(output, dict) else getattr(output, "choices", [])
        if not choices:
            raise AppError("视觉描述结果为空", code="visual_caption_empty", status_code=502)

        first_choice = choices[0]
        message = first_choice.get("message", {}) if isinstance(first_choice, dict) else getattr(first_choice, "message", {})
        content = message.get("content", []) if isinstance(message, dict) else getattr(message, "content", [])

        if isinstance(content, str):
            text = content.strip()
        else:
            text_parts: list[str] = []
            for item in content:
                if isinstance(item, dict):
                    text_value = item.get("text")
                    if isinstance(text_value, str) and text_value.strip():
                        text_parts.append(text_value.strip())
                elif isinstance(item, str) and item.strip():
                    text_parts.append(item.strip())
            text = "\n".join(text_parts).strip()

        if not text:
            raise AppError("视觉描述结果为空", code="visual_caption_empty", status_code=502)
        return text
