"""Textual TUI: never-drop-frame live markdown stream.

Uses Textual's MarkdownStream so token floods coalesce into appends the
widget can keep up with (incremental line parse, not full re-render).
"""

from __future__ import annotations

import threading
from time import monotonic
from typing import Iterator, Optional

from textual import work
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.widgets import Footer, Header, Markdown, Static
from textual.widgets.markdown import MarkdownStream

from live_stream_tui.metrics import StreamMetrics
from live_stream_tui.ndjson import StreamEvent, parse_line
from live_stream_tui.theme import TRANSPARENT_CSS


class LiveStreamApp(App[None]):
    """Stream markdown without thrashing: coalesce + incremental append."""

    CSS = (
        TRANSPARENT_CSS
        + """
    #status {
        dock: top;
        height: 1;
        padding: 0 1;
        background: transparent;
        color: #38bdf8;
        text-style: bold;
    }
    #body_scroll {
        padding: 0 1;
        background: transparent;
    }
    #body {
        padding: 0 1 1 1;
        height: auto;
        background: transparent;
        color: #e2e8f0;
    }
    #thought {
        color: #a78bfa;
        padding: 0 2 1 2;
        display: none;
        height: auto;
        max-height: 4;
        background: transparent;
    }
    #thought.visible {
        display: block;
    }
    """
    )

    TITLE = "live-stream"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
        ("a", "toggle_autoscroll", "Autoscroll"),
        ("p", "toggle_pause", "Pause feed"),
    ]

    status_text: reactive[str] = reactive("starting…")

    def __init__(
        self,
        line_iter: Iterator[str],
        *,
        fps: float = 30.0,
        show_thoughts: bool = False,
        title: str = "live-stream",
    ) -> None:
        super().__init__()
        self._line_iter = line_iter
        # fps is a soft drain rate for the pending queue; MarkdownStream
        # also coalesces under backpressure.
        self._fps = max(5.0, min(fps, 120.0))
        self._show_thoughts = show_thoughts
        self._pending: list[str] = []
        self._pending_thought = ""
        self._done = False
        self._error: Optional[str] = None
        self._autoscroll = True
        self._paused = False
        self._lock = threading.Lock()
        self._stream: Optional[MarkdownStream] = None
        self._metrics = StreamMetrics()
        self._writing = False
        self._flush_event = threading.Event()
        self.title = title

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(id="status")
        yield Static(id="thought")
        with VerticalScroll(id="body_scroll"):
            yield Markdown("", id="body")
        yield Footer()

    def on_mount(self) -> None:
        md = self.query_one("#body", Markdown)
        self._stream = Markdown.get_stream(md)
        self.query_one("#status", Static).update(self.status_text)
        # Drain pending chunks at fps; stream still coalesces if paint lags.
        self.set_interval(1.0 / self._fps, self._kick_flush)
        # Throughput samples for the live sparkline graph.
        self.set_interval(0.25, self._tick_metrics)
        self._run_ingest()

    def on_unmount(self) -> None:
        stream = self._stream
        self._stream = None
        if stream is not None:
            self.run_worker(stream.stop(), exclusive=False, name="stream_stop")

    def watch_status_text(self, value: str) -> None:
        try:
            self.query_one("#status", Static).update(value)
        except Exception:
            pass

    def _tick_metrics(self) -> None:
        self._metrics.tick()
        with self._lock:
            done = self._done
            err = self._error
            paused = self._paused
        line = self._metrics.status_line(fps_cap=self._fps, done=done, err=err)
        if paused and not done:
            line = "paused · " + line
        self.status_text = line

    def _kick_flush(self) -> None:
        if self._writing or self._paused:
            return
        with self._lock:
            if not self._pending and not (
                self._done and self._stream is not None
            ):
                # still refresh thought / status on done edge
                if not self._done and not self._error:
                    return
            pending = self._pending
            self._pending = []
            thought = self._pending_thought
            err = self._error
            done = self._done
        if not pending and not done and not err and not thought:
            return
        self._writing = True
        self._flush_to_stream("".join(pending), thought, err, done)

    @work(exclusive=True, name="md_flush")
    async def _flush_to_stream(
        self,
        delta: str,
        thought: str,
        err: Optional[str],
        done: bool,
    ) -> None:
        try:
            stream = self._stream
            t0 = monotonic()
            if stream is not None and delta:
                await stream.write(delta)
            paint_ms = (monotonic() - t0) * 1000.0
            if delta:
                self._metrics.note_paint(paint_ms)

            th = self.query_one("#thought", Static)
            if self._show_thoughts and thought:
                th.add_class("visible")
                th.update(f"thought  {thought[-400:]}")
            else:
                th.remove_class("visible")

            if err:
                self.status_text = f"error · {err[:120]}"
            elif done and stream is not None:
                await stream.stop()
                self._stream = None
                self.status_text = self._metrics.status_line(
                    fps_cap=self._fps, done=True, err=None
                )

            if self._autoscroll:
                scroll = self.query_one("#body_scroll", VerticalScroll)
                scroll.scroll_end(animate=False)
        finally:
            self._writing = False
            # If more arrived while we painted, kick again next interval.
            # No busy-loop: the fps timer owns the schedule.

    @work(thread=True, name="ingest")
    def _run_ingest(self) -> None:
        def set_status(s: str) -> None:
            self.status_text = s

        self.call_from_thread(set_status, "streaming…")
        try:
            for line in self._line_iter:
                if self._done:
                    break
                # Pause: block ingest so demo/pipe backpressure freezes too.
                while self._paused and not self._done:
                    self._flush_event.wait(0.05)
                    self._flush_event.clear()
                ev = parse_line(line)
                if ev is None:
                    continue
                self._handle_event(ev)
                if ev.kind in ("end", "error"):
                    break
        except Exception as e:
            with self._lock:
                self._error = str(e)
                self._done = True
            return
        with self._lock:
            self._done = True

    def _handle_event(self, ev: StreamEvent) -> None:
        with self._lock:
            if ev.kind == "text":
                if ev.data:
                    self._pending.append(ev.data)
                    self._metrics.note_chunk(len(ev.data))
            elif ev.kind == "thought" and self._show_thoughts:
                self._pending_thought += ev.data
            elif ev.kind == "error":
                self._error = ev.data
                self._done = True
            elif ev.kind == "end":
                self._done = True

    def action_toggle_autoscroll(self) -> None:
        self._autoscroll = not self._autoscroll

    def action_toggle_pause(self) -> None:
        self._paused = not self._paused
        if not self._paused:
            self._flush_event.set()


def run_app(
    line_iter: Iterator[str],
    *,
    fps: float = 30.0,
    show_thoughts: bool = False,
    title: str = "live-stream",
) -> None:
    app = LiveStreamApp(
        line_iter,
        fps=fps,
        show_thoughts=show_thoughts,
        title=title,
    )
    app.run()
