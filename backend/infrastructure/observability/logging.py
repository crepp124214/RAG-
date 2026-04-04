from __future__ import annotations

import json
import logging
from typing import Any

from backend.infrastructure.observability.request_context import get_request_id


def configure_logging() -> None:
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    logging.basicConfig(level=logging.INFO, format="%(message)s")


def log_event(logger: logging.Logger, level: int, event: str, **fields: Any) -> None:
    payload = {
        "event": event,
        **fields,
    }

    request_id = get_request_id()
    if request_id:
        payload["request_id"] = request_id

    logger.log(level, json.dumps(payload, ensure_ascii=False, default=str))
