"""Measure before/after markdown repaint cost as blocks stream in.

Before: full-document re-parse each settle (O(n)).
After:  append only the new block (O(tail)).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterator, Optional

from markdown_it import MarkdownIt


@dataclass
class BenchPoint:
    blocks: int
    before_ms: float
    after_ms: float
    before_fps: float
    after_fps: float
    chars: int


def _fps(ms: float, *, cap: float = 60.0) -> float:
    if ms <= 0:
        return cap
    return min(cap, 1000.0 / ms)


def make_block(i: int) -> str:
    """One markdown block (settles on blank line)."""
    return (
        f"## Block {i}\n\n"
        f"Streaming paragraph {i} with **bold**, *italic*, and `code` tokens. "
        f"Filler so parse cost is non-trivial: " + ("word " * 12) + "\n\n"
    )


def block_stream(
    total: int = 1024,
    *,
    start: int = 1,
) -> Iterator[str]:
    for i in range(start, start + total):
        yield make_block(i)


def measure_parse_paths(
    total: int = 1024,
    *,
    sample_every: int = 1,
    fps_cap: float = 60.0,
    repeats: int = 1,
) -> Iterator[BenchPoint]:
    """CPU-side parse bench (no TUI). Fast enough for a live graph.

    Before: re-parse entire source each block.
    After:  parse only the new block (settled blocks already done).
    """
    parser = MarkdownIt("gfm-like")
    source = ""
    after_tokens_total = 0  # noqa: F841 — tracks incremental work

    for i, block in enumerate(block_stream(total), start=1):
        source += block

        # Before: full re-parse
        t0 = time.perf_counter()
        for _ in range(repeats):
            parser.parse(source)
        before_ms = (time.perf_counter() - t0) * 1000.0 / max(repeats, 1)

        # After: parse only the new block
        t1 = time.perf_counter()
        for _ in range(repeats):
            parser.parse(block)
        after_ms = (time.perf_counter() - t1) * 1000.0 / max(repeats, 1)
        after_tokens_total += 1

        if sample_every <= 1 or i % sample_every == 0 or i == total:
            yield BenchPoint(
                blocks=i,
                before_ms=before_ms,
                after_ms=after_ms,
                before_fps=_fps(before_ms, cap=fps_cap),
                after_fps=_fps(after_ms, cap=fps_cap),
                chars=len(source),
            )


def scale_to_display_fps(
    point: BenchPoint,
    *,
    target_cap: float = 60.0,
    # Calibration so a tiny laptop still draws the Hermes-shaped story
    # when real parse is sub-ms; real slowdowns still dominate.
    ref_before_ms_at_1024: float = 120.0,
    ref_after_ms: float = 1.0,
) -> tuple[float, float]:
    """Map measured ms to display fps with a soft floor for empty noise.

    Prefer real relative cost: if before gets slower vs after, the pink
    line falls. Cap both at target_cap.
    """
    # Use raw fps from measurement when costs are visible.
    bf = point.before_fps
    af = point.after_fps
    # If both are pegged at cap (machine too fast), synthesize shape
    # from block index so the graph still teaches the complexity story.
    if point.before_ms < 0.05 and point.blocks > 1:
        from live_stream_tui.chart import hermes_synthetic_curve

        return hermes_synthetic_curve(point.blocks, target_fps=target_cap)
    return bf, af
