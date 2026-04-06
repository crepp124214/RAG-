from __future__ import annotations

from collections.abc import Iterator
import json

from dashscope import Generation

from backend.app.exceptions import AppError
from backend.app.tools.base import ToolCallDecision


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

    def decide_tool_call(self, *, query: str, tool_schemas: list[dict[str, object]]) -> ToolCallDecision | None:
        if not tool_schemas:
            return None

        response = Generation.call(
            model=self.model,
            api_key=self.api_key,
            result_format="message",
            messages=[
                {"role": "system", "content": "你是工具调度助手。只有在确实需要时才调用工具，否则直接回答。"},
                {"role": "user", "content": query},
            ],
            tools=[{"type": "function", "function": schema} for schema in tool_schemas],
        )
        return self._extract_tool_call(response)

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

    def _extract_tool_call(self, response: object) -> ToolCallDecision | None:
        status_code = getattr(response, "status_code", 500)
        if status_code != 200:
            message = getattr(response, "message", "chat request failed")
            raise AppError(f"问答生成失败: {message}", code="chat_generation_failed", status_code=502)

        output = getattr(response, "output", {}) or {}
        choices = output.get("choices", []) if isinstance(output, dict) else getattr(output, "choices", [])
        if not choices:
            return None

        first_choice = choices[0]
        if isinstance(first_choice, dict):
            message = first_choice.get("message", {})
        else:
            message = getattr(first_choice, "message", {})

        tool_calls = message.get("tool_calls", []) if isinstance(message, dict) else getattr(message, "tool_calls", [])
        if not tool_calls:
            return None

        first_call = tool_calls[0]
        function_payload = first_call.get("function", {}) if isinstance(first_call, dict) else getattr(first_call, "function", {})
        name = function_payload.get("name", "") if isinstance(function_payload, dict) else getattr(function_payload, "name", "")
        raw_arguments = function_payload.get("arguments", "{}") if isinstance(function_payload, dict) else getattr(function_payload, "arguments", "{}")

        if isinstance(raw_arguments, str):
            try:
                arguments = json.loads(raw_arguments or "{}")
            except json.JSONDecodeError as exc:
                raise AppError("工具参数解析失败", code="TOOL_BAD_ARGUMENTS", status_code=400) from exc
        elif isinstance(raw_arguments, dict):
            arguments = raw_arguments
        else:
            arguments = {}

        return ToolCallDecision(tool_name=str(name), arguments=arguments)
