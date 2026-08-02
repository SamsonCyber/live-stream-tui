"""Parse Grok-style streaming-json NDJSON events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterator, Optional


@dataclass(frozen=True)
class StreamEvent:
    kind: str  # text | thought | end | error | other
    data: str = ""
    raw: Optional[dict[str, Any]] = None


def parse_line(line: str) -> Optional[StreamEvent]:
    line = line.strip()
    if not line:
        return None
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        # plain text line fallback
        return StreamEvent(kind="text", data=line + "\n", raw=None)
    if not isinstance(obj, dict):
        return None
    t = str(obj.get("type") or obj.get("event") or "other")
    if t == "text":
        return StreamEvent(kind="text", data=str(obj.get("data") or ""), raw=obj)
    if t == "thought":
        return StreamEvent(kind="thought", data=str(obj.get("data") or ""), raw=obj)
    if t == "end":
        return StreamEvent(kind="end", data="", raw=obj)
    if t == "error":
        msg = str(obj.get("message") or obj.get("data") or "error")
        return StreamEvent(kind="error", data=msg, raw=obj)
    # unknown: ignore or surface as other
    return StreamEvent(kind="other", data="", raw=obj)


def iter_events(lines: Iterator[str]) -> Iterator[StreamEvent]:
    for line in lines:
        ev = parse_line(line)
        if ev is not None:
            yield ev
