from __future__ import annotations


_REALTIME_KEYWORDS = ("今天", "最新", "最近", "实时", "刚刚", "news", "latest", "today")
_DOCUMENT_KEYWORDS = ("文档", "文件", "任务", "状态", "第几页", "页", "document", "task")


def determine_allowed_tools(query: str) -> list[str]:
    normalized = query.lower()
    allowed: list[str] = []

    if any(keyword in query or keyword in normalized for keyword in _REALTIME_KEYWORDS):
        allowed.append("web_search")

    if any(keyword in query or keyword in normalized for keyword in _DOCUMENT_KEYWORDS):
        allowed.append("document_lookup")

    return allowed
