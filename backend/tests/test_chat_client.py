from __future__ import annotations

import pytest

from backend.app.exceptions import AppError
from backend.infrastructure.llm.chat_client import QwenChatClient


class FakeResponse:
    def __init__(self, *, status_code: int, content: str = "", message: str = "") -> None:
        self.status_code = status_code
        self.message = message
        self.output = {
            "choices": [{"message": {"content": content}}],
        }


def test_generate_returns_message_content(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "backend.infrastructure.llm.chat_client.Generation.call",
        lambda **kwargs: FakeResponse(status_code=200, content="这是答案"),
    )

    client = QwenChatClient(api_key="test-key", model="qwen-plus")

    result = client.generate(system_prompt="s", user_prompt="u")

    assert result == "这是答案"


def test_generate_raises_when_provider_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "backend.infrastructure.llm.chat_client.Generation.call",
        lambda **kwargs: FakeResponse(status_code=500, message="provider down"),
    )

    client = QwenChatClient(api_key="test-key", model="qwen-plus")

    with pytest.raises(AppError) as exc_info:
        client.generate(system_prompt="s", user_prompt="u")

    assert exc_info.value.code == "chat_generation_failed"


def test_generate_raises_when_content_is_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "backend.infrastructure.llm.chat_client.Generation.call",
        lambda **kwargs: FakeResponse(status_code=200, content="   "),
    )

    client = QwenChatClient(api_key="test-key", model="qwen-plus")

    with pytest.raises(AppError) as exc_info:
        client.generate(system_prompt="s", user_prompt="u")

    assert exc_info.value.code == "chat_generation_empty"


def test_stream_generate_yields_incremental_chunks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "backend.infrastructure.llm.chat_client.Generation.call",
        lambda **kwargs: iter(
            [
                FakeResponse(status_code=200, content="你好"),
                FakeResponse(status_code=200, content="，世界"),
            ]
        ),
    )

    client = QwenChatClient(api_key="test-key", model="qwen-plus")

    result = list(client.stream_generate(system_prompt="s", user_prompt="u"))

    assert result == ["你好", "，世界"]


def test_stream_generate_raises_when_provider_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "backend.infrastructure.llm.chat_client.Generation.call",
        lambda **kwargs: iter([FakeResponse(status_code=500, message="provider down")]),
    )

    client = QwenChatClient(api_key="test-key", model="qwen-plus")

    with pytest.raises(AppError) as exc_info:
        list(client.stream_generate(system_prompt="s", user_prompt="u"))

    assert exc_info.value.code == "chat_generation_failed"
