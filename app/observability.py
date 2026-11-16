from datetime import UTC, datetime
from typing import Any
from .schemas import TraceEvent


def event(node: str, detail: str) -> dict[str, Any]:
    """Structured trace consumed by Redis and, when configured, LangSmith callbacks."""
    return TraceEvent(node=node, at=datetime.now(UTC), detail=detail).model_dump(mode="json")
