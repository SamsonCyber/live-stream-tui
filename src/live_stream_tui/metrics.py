"""Live throughput / paint metrics for the status sparkline."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from time import monotonic
from typing import Deque


SPARK = "▁▂▃▄▅▆▇█"


@dataclass
class StreamMetrics:
    """Ring-buffered samples for a status-line sparkline."""

    capacity: int = 24
    chars: int = 0
    chunks: int = 0
    paints: int = 0
    last_paint_ms: float = 0.0
    max_paint_ms: float = 0.0
    _char_samples: Deque[float] = field(default_factory=lambda: deque(maxlen=24))
    _paint_samples: Deque[float] = field(default_factory=lambda: deque(maxlen=24))
    _last_tick_chars: int = 0
    _last_tick_t: float = field(default_factory=monotonic)

    def __post_init__(self) -> None:
        self._char_samples = deque(maxlen=self.capacity)
        self._paint_samples = deque(maxlen=self.capacity)

    def note_chunk(self, n_chars: int) -> None:
        self.chunks += 1
        self.chars += n_chars

    def note_paint(self, elapsed_ms: float) -> None:
        self.paints += 1
        self.last_paint_ms = elapsed_ms
        if elapsed_ms > self.max_paint_ms:
            self.max_paint_ms = elapsed_ms
        self._paint_samples.append(elapsed_ms)

    def tick(self) -> None:
        """Sample chars/sec over the last tick interval (call ~1 Hz)."""
        now = monotonic()
        dt = max(now - self._last_tick_t, 1e-6)
        delta = self.chars - self._last_tick_chars
        self._char_samples.append(delta / dt)
        self._last_tick_chars = self.chars
        self._last_tick_t = now

    @staticmethod
    def sparkline(samples: Deque[float] | list[float], width: int = 16) -> str:
        if not samples:
            return SPARK[0] * width
        data = list(samples)[-width:]
        while len(data) < width:
            data.insert(0, 0.0)
        peak = max(data) or 1.0
        out: list[str] = []
        last = len(SPARK) - 1
        for v in data:
            idx = int(round((v / peak) * last))
            out.append(SPARK[max(0, min(last, idx))])
        return "".join(out)

    def chars_spark(self, width: int = 16) -> str:
        return self.sparkline(self._char_samples, width)

    def paint_spark(self, width: int = 12) -> str:
        return self.sparkline(self._paint_samples, width)

    def status_line(self, *, fps_cap: float, done: bool, err: str | None) -> str:
        spark = self.chars_spark(16)
        paint = self.paint_spark(10)
        if err:
            return f"error · {err[:100]}"
        phase = "done" if done else "streaming"
        return (
            f"{phase} · {self.chars}c · {self.chunks} chunks · "
            f"cap {fps_cap:.0f}fps · paint {self.last_paint_ms:.0f}ms "
            f"(max {self.max_paint_ms:.0f}) · thr {spark} · lat {paint}"
        )
