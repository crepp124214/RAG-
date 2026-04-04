from __future__ import annotations


def run_success_task(payload: dict[str, str]) -> dict[str, str]:
    return {
        "status": "ok",
        "value": payload["value"],
    }


def run_failure_task(message: str = "intentional failure") -> None:
    raise RuntimeError(message)
