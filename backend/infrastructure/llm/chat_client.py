from __future__ import annotations

from collections.abc import Iterator

from dashscope import Generation

from backend.app.exceptions import AppError


class QwenChatClient:
    def __init__(self, *, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        response = Generation.call(
            **self._build_request_kwargs(system_prompt=system_prompt, user_prompt=user_prompt),
        )
        content = self._extract_content(response).strip()
        if not content:
            raise AppError("问答生成结果为空", code="chat_generation_empty", status_code=502)
        return content

    def stream_generate(self, *, system_prompt: str, user_prompt: str) -> Iterator[str]:
        responses = Generation.call(
            **self._build_request_kwargs(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                stream=True,
                incremental_output=False,
            ),
        )

        for response in responses:
            chunk = self._extract_content(response)
            if chunk:
                yield chunk

    def _build_request_kwargs(self, *, system_prompt: str, user_prompt: str, **kwargs: object) -> dict[str, object]:
        return {
            "model": self.model,
            "api_key": self.api_key,
            "result_format": "message",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            **kwargs,
        }

    def _extract_content(self, response: object) -> str:
        status_code = getattr(response, "status_code", 500)
        if status_code != 200:
            message = getattr(response, "message", "chat request failed")
            raise AppError(f"问答生成失败: {message}", code="chat_generation_failed", status_code=502)

        output = getattr(response, "output", {}) or {}
        choices = output.get("choices", []) if isinstance(output, dict) else getattr(output, "choices", [])
        if not choices:
            raise AppError("问答生成结果为空", code="chat_generation_empty", status_code=502)

        first_choice = choices[0]
        if isinstance(first_choice, dict):
            message = first_choice.get("message", {})
        else:
            message = getattr(first_choice, "message", {})

        if isinstance(message, dict):
            content = message.get("content", "")
        else:
            content = getattr(message, "content", "")

        if isinstance(content, list):
            return "".join(str(item) for item in content).strip()
        return str(content).strip()
