from __future__ import annotations

import pytest

from backend.app.exceptions import AppError
from backend.app.tools.base import ToolDefinition
from backend.app.tools.registry import ToolRegistry


def test_registry_exposes_registered_tool_schemas() -> None:
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="demo_tool",
            description="demo",
            parameters={"type": "object", "properties": {"query": {"type": "string"}}},
            handler=lambda db_session, arguments: arguments,
        )
    )

    schemas = registry.list_schemas()

    assert schemas == [
        {
            "name": "demo_tool",
            "description": "demo",
            "parameters": {"type": "object", "properties": {"query": {"type": "string"}}},
        }
    ]


def test_registry_rejects_unregistered_tool_lookup() -> None:
    registry = ToolRegistry()

    with pytest.raises(AppError) as exc_info:
        registry.get("missing_tool")

    assert exc_info.value.code == "tool_not_registered"
