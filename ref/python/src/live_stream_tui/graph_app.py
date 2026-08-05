"""Live dual-line FPS graph TUI (the Hermes tweet chart).

Transparent chrome: host terminal background (Windows Terminal wallpaper /
opacity) shows through. Color lives on the curves, fill, and tips only.
"""

from __future__ import annotations

import threading
from typing import Literal

from rich.text import Text
from textual import work
from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual.widgets import Footer, Header, Static

from live_stream_tui.bench import measure_parse_paths, scale_to_display_fps
from live_stream_tui.chart import ChartState, RenderRateChart, hermes_synthetic_curve
from live_stream_tui.theme import (
    AFTER,
    BEFORE,
    STATUS_MUTED,
    STATUS_OK,
    STATUS_STREAM,
    TRANSPARENT_CSS,
)


Mode = Literal["bench", "replay"]


class GraphApp(App[None]):
    """Animate the Hermes-style before/after render-rate chart live."""

    CSS = (
        TRANSPARENT_CSS
        + """
    #chart {
        height: 1fr;
        padding: 1 2;
        background: transparent;
        color: #e2e8f0;
    }
    #status {
        dock: bottom;
        height: 3;
        padding: 0 2;
        background: transparent;
        color: #94a3b8;
        border-top: solid #ec489940;
    }
    """
    )

    TITLE = "live-stream · graph"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
        ("r", "restart", "Restart"),
        ("m", "toggle_mode", "Mode"),
        ("f", "toggle_fill", "Fill"),
    ]

    status_text: reactive[str] = reactive("starting…")

    def __init__(
        self,
        *,
        total_blocks: int = 1024,
        fps: float = 30.0,
        mode: Mode = "bench",
        sample_every: int = 4,
        title: str = "live-stream · graph",
        show_fill: bool = True,
    ) -> None:
        super().__init__()
        self._total = max(16, total_blocks)
        self._fps = max(5.0, min(fps, 120.0))
        self._mode: Mode = mode
        self._sample_every = max(1, sample_every)
        self._show_fill = show_fill
        self._state = ChartState(x_max=float(self._total), show_fill=show_fill)
        self._pending: list[tuple[float, float, float]] = []  # x, before, after
        self._lock = threading.Lock()
        self._done = False
        self._gen = 0  # bump to cancel in-flight worker on restart
        self.title = title

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(id="chart")
        yield Static(id="status")
        yield Footer()

    def on_mount(self) -> None:
        self._paint_chart()
        self.set_interval(1.0 / self._fps, self._drain)
        self._start_feed()

    def watch_status_text(self, value: str) -> None:
        try:
            self.query_one("#status", Static).update(self._status_rich(value))
        except Exception:
            pass

    def _status_rich(self, value: str) -> Text:
        t = Text()
        if "done" in value:
            t.append("● ", style=f"bold {STATUS_OK}")
        elif "streaming" in value or "starting" in value:
            t.append("● ", style=f"bold {STATUS_STREAM}")
        else:
            t.append("● ", style=STATUS_MUTED)
        # color mode token
        if value.startswith("bench") or "bench ·" in value:
            t.append("bench", style=f"bold {BEFORE}")
        elif value.startswith("replay") or "replay ·" in value:
            t.append("replay", style=f"bold {AFTER}")
        # rest of line after first word
        parts = value.split(" · ", 1)
        if len(parts) == 2:
            t.append(" · ", style=STATUS_MUTED)
            rest = parts[1]
            # highlight after/before numbers
            if "after " in rest and "before " in rest:
                # e.g. "64/64 blocks · after 60 fps · before 8 fps · done"
                segs = rest.split(" · ")
                for i, seg in enumerate(segs):
                    if i:
                        t.append(" · ", style=STATUS_MUTED)
                    if seg.startswith("after "):
                        t.append(seg, style=f"bold {AFTER}")
                    elif seg.startswith("before "):
                        t.append(seg, style=f"bold {BEFORE}")
                    elif seg == "done":
                        t.append(seg, style=f"bold {STATUS_OK}")
                    elif seg == "streaming":
                        t.append(seg, style=f"bold {STATUS_STREAM}")
                    else:
                        t.append(seg, style=STATUS_MUTED)
            else:
                t.append(rest, style=STATUS_MUTED)
        else:
            t.append(value, style=STATUS_MUTED)
        fill = "on" if self._show_fill else "off"
        t.append(f"  · fill {fill}", style=STATUS_MUTED)
        return t

    def _paint_chart(self) -> None:
        h = max(10, self.size.height - 12) if self.size.height else 14
        self._state.show_fill = self._show_fill
        chart = RenderRateChart(self._state, plot_height=min(18, h))
        self.query_one("#chart", Static).update(chart)

    def _drain(self) -> None:
        with self._lock:
            if not self._pending:
                if self._done:
                    self._paint_chart()
                return
            batch = self._pending
            self._pending = []
        for x, b, a in batch:
            self._state.push(x, b, a)
        self._paint_chart()
        if self._state.xs:
            x = self._state.xs[-1]
            bf = self._state.before.ys[-1]
            af = self._state.after.ys[-1]
            mode = self._mode
            self.status_text = (
                f"{mode} · {int(x)}/{self._total} blocks · "
                f"after {af:.0f} fps · before {bf:.0f} fps · "
                f"{'done' if self._done else 'streaming'}"
            )

    def _start_feed(self) -> None:
        self._gen += 1
        gen = self._gen
        with self._lock:
            self._pending.clear()
            self._done = False
        self._state = ChartState(
            x_max=float(self._total),
            show_fill=self._show_fill,
        )
        self._paint_chart()
        self.status_text = f"{self._mode} · streaming…"
        if self._mode == "replay":
            self._feed_replay(gen)
        else:
            self._feed_bench(gen)

    @work(thread=True, exclusive=True, name="graph_feed")
    def _feed_bench(self, gen: int) -> None:
        try:
            for pt in measure_parse_paths(
                self._total,
                sample_every=self._sample_every,
                fps_cap=60.0,
            ):
                if gen != self._gen:
                    return
                bf, af = scale_to_display_fps(pt)
                with self._lock:
                    self._pending.append((float(pt.blocks), bf, af))
        finally:
            if gen == self._gen:
                with self._lock:
                    self._done = True

    @work(thread=True, exclusive=True, name="graph_replay")
    def _feed_replay(self, gen: int) -> None:
        """Replay the Hermes tweet curve shape (no CPU bench)."""
        import time

        step = max(1, self._sample_every)
        try:
            for blocks in range(step, self._total + 1, step):
                if gen != self._gen:
                    return
                bf, af = hermes_synthetic_curve(blocks, total=self._total)
                with self._lock:
                    self._pending.append((float(blocks), bf, af))
                # Pace so a full run is ~4s of animation at 30fps-ish
                time.sleep(0.012)
            bf, af = hermes_synthetic_curve(self._total, total=self._total)
            with self._lock:
                self._pending.append((float(self._total), bf, af))
        finally:
            if gen == self._gen:
                with self._lock:
                    self._done = True

    def action_restart(self) -> None:
        self._start_feed()

    def action_toggle_mode(self) -> None:
        self._mode = "replay" if self._mode == "bench" else "bench"
        self._start_feed()

    def action_toggle_fill(self) -> None:
        self._show_fill = not self._show_fill
        self._state.show_fill = self._show_fill
        self._paint_chart()
        # refresh status to show fill on/off
        self.status_text = self.status_text


def run_graph_app(
    *,
    total_blocks: int = 1024,
    fps: float = 30.0,
    mode: Mode = "bench",
    sample_every: int = 4,
    show_fill: bool = True,
) -> None:
    GraphApp(
        total_blocks=total_blocks,
        fps=fps,
        mode=mode,
        sample_every=sample_every,
        show_fill=show_fill,
    ).run()
