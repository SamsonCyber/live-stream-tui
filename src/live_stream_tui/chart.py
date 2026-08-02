"""Dual-series line chart for live render-rate graphs (Hermes-style).

X = markdown blocks rendered, Y = effective repaint rate (fps).
Two series: before (O(n) re-parse) vs after (per-block incremental).
Truecolor pink / cyan on transparent cells (host terminal bg shows through).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence

from rich.console import Console, ConsoleOptions, RenderResult
from rich.text import Text

from live_stream_tui.theme import (
    AFTER,
    AFTER_TIP,
    AXIS,
    BEFORE,
    BEFORE_TIP,
    CURSOR,
    FILL_DIM,
    GRID,
    SUBTITLE,
    TITLE,
)


# Braille base + 2x4 dot bit layout (cols left/right, rows top→bottom).
_BRAILLE = 0x2800
# bits: (0,0)=1 (1,0)=8 (0,1)=2 (1,1)=16 (0,2)=4 (1,2)=32 (0,3)=64 (1,3)=128
_DOT = (
    (0x01, 0x08),
    (0x02, 0x10),
    (0x04, 0x20),
    (0x40, 0x80),
)


@dataclass
class Series:
    name: str
    ys: list[float] = field(default_factory=list)
    color: str = AFTER
    style: str = "bold"


@dataclass
class ChartState:
    """Live chart data for the Hermes render-rate plot."""

    title: str = "Hermes TUI: streamed Markdown render rate"
    subtitle: str = "Per-update repaint rate as one 1,024-block reply streams in"
    x_label: str = "Markdown blocks rendered"
    y_label: str = "Effective render rate (fps)"
    x_max: float = 1024.0
    y_max: float = 65.0
    y_min: float = 0.0
    before: Series = field(
        default_factory=lambda: Series(
            name="Before: stable-prefix split — O(n) re-parse each time a block settles",
            color=BEFORE,
        )
    )
    after: Series = field(
        default_factory=lambda: Series(
            name="After: per-block incremental — settled blocks parse once, O(tail) per update",
            color=AFTER,
        )
    )
    # Parallel x for both series (block counts at each sample).
    xs: list[float] = field(default_factory=list)
    cursor_x: Optional[float] = None
    show_fill: bool = True

    def push(self, blocks: float, before_fps: float, after_fps: float) -> None:
        self.xs.append(blocks)
        self.before.ys.append(before_fps)
        self.after.ys.append(after_fps)
        self.cursor_x = blocks


def _clamp(v: float, lo: float, hi: float) -> float:
    return lo if v < lo else hi if v > hi else v


def _scale(v: float, v0: float, v1: float, p0: int, p1: int) -> int:
    if v1 <= v0:
        return p0
    t = (v - v0) / (v1 - v0)
    return int(round(p0 + t * (p1 - p0)))


def _plot_polyline(
    grid: list[list[int]],
    xs: Sequence[float],
    ys: Sequence[float],
    *,
    pw: int,
    ph: int,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
) -> None:
    n = min(len(xs), len(ys))
    if n == 0:
        return
    pts: list[tuple[int, int]] = []
    for i in range(n):
        px = _scale(xs[i], x_min, x_max, 0, pw - 1)
        py = _scale(ys[i], y_min, y_max, ph - 1, 0)  # invert Y
        pts.append((_clamp(px, 0, pw - 1), _clamp(py, 0, ph - 1)))
    for i in range(len(pts)):
        x0, y0 = pts[i]
        grid[y0][x0] = 1
        if i == 0:
            continue
        x1, y1 = pts[i - 1]
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        x, y = x0, y0
        while True:
            if 0 <= x < pw and 0 <= y < ph:
                grid[y][x] = 1
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy


def _sample_y_at_x(
    xs: Sequence[float],
    ys: Sequence[float],
    x: float,
) -> Optional[float]:
    """Linear interpolate y at domain x. None if outside series span."""
    n = min(len(xs), len(ys))
    if n == 0:
        return None
    if n == 1:
        return float(ys[0]) if xs[0] == x else None
    if x < xs[0] or x > xs[-1]:
        return None
    for i in range(1, n):
        if xs[i] >= x:
            x0, x1 = xs[i - 1], xs[i]
            y0, y1 = ys[i - 1], ys[i]
            if x1 == x0:
                return float(y1)
            t = (x - x0) / (x1 - x0)
            return float(y0 + t * (y1 - y0))
    return float(ys[-1])


def _fill_between(
    fill: list[list[int]],
    xs: Sequence[float],
    before_ys: Sequence[float],
    after_ys: Sequence[float],
    *,
    pw: int,
    ph: int,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
) -> None:
    """Paint soft fill pixels between after (top) and before (bottom) curves."""
    if not xs:
        return
    for px in range(pw):
        # map pixel x → domain x
        if pw <= 1:
            dom_x = x_min
        else:
            dom_x = x_min + (px / (pw - 1)) * (x_max - x_min)
        # only fill under the drawn span
        if dom_x < xs[0] or dom_x > xs[-1]:
            continue
        ya = _sample_y_at_x(xs, after_ys, dom_x)
        yb = _sample_y_at_x(xs, before_ys, dom_x)
        if ya is None or yb is None:
            continue
        # pixel y: higher fps → smaller py
        py_a = _scale(ya, y_min, y_max, ph - 1, 0)
        py_b = _scale(yb, y_min, y_max, ph - 1, 0)
        top = min(py_a, py_b)
        bot = max(py_a, py_b)
        # leave a 1px gap so lines stay sharp on top of fill
        for py in range(top + 1, bot):
            if 0 <= py < ph:
                fill[py][px] = 1


def render_braille_lines(
    xs: Sequence[float],
    series_list: Sequence[tuple[Sequence[float], str]],
    *,
    width: int,
    height: int,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    cursor_x: Optional[float] = None,
    fill_between: bool = True,
) -> list[Text]:
    """Return height Text rows of braille dual-series plot with optional fill."""
    pw = max(2, width * 2)
    ph = max(4, height * 4)

    bitmaps: list[list[list[int]]] = []
    for _ys, _color in series_list:
        grid = [[0 for _ in range(pw)] for _ in range(ph)]
        bitmaps.append(grid)

    for grid, (ys, _) in zip(bitmaps, series_list):
        _plot_polyline(
            grid,
            xs,
            ys,
            pw=pw,
            ph=ph,
            x_min=x_min,
            x_max=x_max,
            y_min=y_min,
            y_max=y_max,
        )

    fill_grid: Optional[list[list[int]]] = None
    if fill_between and len(series_list) >= 2:
        # series_list[0] = before, series_list[1] = after
        fill_grid = [[0 for _ in range(pw)] for _ in range(ph)]
        _fill_between(
            fill_grid,
            xs,
            series_list[0][0],
            series_list[1][0],
            pw=pw,
            ph=ph,
            x_min=x_min,
            x_max=x_max,
            y_min=y_min,
            y_max=y_max,
        )

    cursor_col: Optional[int] = None
    if cursor_x is not None:
        cursor_col = _scale(cursor_x, x_min, x_max, 0, pw - 1)

    rows: list[Text] = []
    for row in range(height):
        line = Text()
        for col in range(width):
            ch_bits_by_series: list[int] = []
            for grid in bitmaps:
                bits = 0
                for dy in range(4):
                    for dx in range(2):
                        gy = row * 4 + dy
                        gx = col * 2 + dx
                        if gy < ph and gx < pw and grid[gy][gx]:
                            bits |= _DOT[dy][dx]
                ch_bits_by_series.append(bits)

            fill_bits = 0
            if fill_grid is not None:
                for dy in range(4):
                    for dx in range(2):
                        gy = row * 4 + dy
                        gx = col * 2 + dx
                        if gy < ph and gx < pw and fill_grid[gy][gx]:
                            fill_bits |= _DOT[dy][dx]

            is_cursor = False
            if cursor_col is not None:
                if col * 2 <= cursor_col < col * 2 + 2:
                    is_cursor = True

            # Lines win over fill. Later series (after/cyan) on overlap.
            drawn = False
            for bits, (_, color) in zip(
                reversed(ch_bits_by_series), reversed(list(series_list))
            ):
                if bits:
                    line.append(chr(_BRAILLE + bits), style=f"bold {color}")
                    drawn = True
                    break
            if not drawn:
                if fill_bits:
                    line.append(chr(_BRAILLE + fill_bits), style=FILL_DIM)
                elif is_cursor:
                    line.append("│", style=CURSOR)
                else:
                    # empty: no bg style → host terminal wallpaper shows through
                    line.append(" ")
        rows.append(line)
    return rows


def format_label(blocks: float, fps: float) -> str:
    b = int(round(blocks))
    return f"{b} blocks · {fps:.0f} fps"


def _tip_badge(label: str, color: str) -> Text:
    """Hermes-style pill tip: colored border-ish brackets around the metric."""
    t = Text()
    t.append("● ", style=f"bold {color}")
    t.append(" ", style="")
    t.append(label, style=f"bold {color}")
    return t


class RenderRateChart:
    """Rich-renderable live chart matching the Hermes tweet layout."""

    def __init__(self, state: ChartState, *, plot_height: int = 14) -> None:
        self.state = state
        self.plot_height = plot_height

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        width = max(40, options.max_width or 80)
        st = self.state
        out: list[Text] = []

        title = Text()
        title.append("◈ ", style=f"bold {AFTER}")
        title.append(st.title, style=TITLE)
        out.append(title)
        out.append(Text(st.subtitle, style=SUBTITLE))
        out.append(Text(""))

        gutter = 4
        plot_w = max(20, width - gutter - 2)
        plot_h = self.plot_height

        series_list = [
            (st.before.ys, st.before.color),
            (st.after.ys, st.after.color),
        ]
        plot_rows = render_braille_lines(
            st.xs,
            series_list,
            width=plot_w,
            height=plot_h,
            x_min=0.0,
            x_max=st.x_max,
            y_min=st.y_min,
            y_max=st.y_max,
            cursor_x=st.cursor_x,
            fill_between=st.show_fill,
        )

        y_ticks = [0, 15, 30, 45, 60]
        tick_set = {t: True for t in y_ticks}

        for i, prow in enumerate(plot_rows):
            y_val = st.y_max - (i / max(plot_h - 1, 1)) * (st.y_max - st.y_min)
            label = "    "
            for t in y_ticks:
                row_for_t = int(
                    round(
                        (st.y_max - t) / max(st.y_max - st.y_min, 1e-9) * (plot_h - 1)
                    )
                )
                if row_for_t == i and t in tick_set:
                    label = f"{t:>3} "
                    tick_set.pop(t, None)
                    break
            # faint horizontal grid tick mark
            line = Text(label, style=AXIS)
            line.append("┤", style=GRID)
            line.append_text(prow)
            out.append(line)

        axis = Text("    └" + "─" * plot_w, style=AXIS)
        out.append(axis)

        x_max_i = int(st.x_max) if st.x_max >= 1 else 1
        if x_max_i >= 1024:
            x_ticks = [0, 256, 512, 768, 1024]
        elif x_max_i >= 256:
            step = max(1, x_max_i // 4)
            x_ticks = list(range(0, x_max_i, step)) + [x_max_i]
        else:
            x_ticks = [0, x_max_i]
        label_row = [" "] * (gutter + 1 + plot_w + 6)
        for xt in x_ticks:
            col = gutter + 1 + _scale(float(xt), 0.0, st.x_max, 0, plot_w - 1)
            s = str(int(xt))
            start = max(0, min(col - len(s) // 2, len(label_row) - len(s)))
            for j, ch in enumerate(s):
                label_row[start + j] = ch
        out.append(Text("".join(label_row).rstrip(), style=AXIS))
        out.append(Text(f"    {st.x_label}", style=SUBTITLE))
        out.append(Text(""))

        if st.xs:
            b = st.xs[-1]
            bf = st.before.ys[-1] if st.before.ys else 0.0
            af = st.after.ys[-1] if st.after.ys else 0.0
            tips = Text("    ")
            tips.append_text(_tip_badge(format_label(b, af), AFTER))
            tips.append("    ")
            tips.append_text(_tip_badge(format_label(b, bf), BEFORE))
            out.append(tips)

        out.append(Text(""))
        leg_b = Text("    ─ ", style=f"bold {BEFORE}")
        leg_b.append(st.before.name, style=BEFORE)
        out.append(leg_b)
        leg_a = Text("    ─ ", style=f"bold {AFTER}")
        leg_a.append(st.after.name, style=AFTER)
        out.append(leg_a)

        for row in out:
            yield row


def hermes_synthetic_curve(
    blocks: int,
    *,
    total: int = 1024,
    target_fps: float = 60.0,
    floor_fps: float = 8.0,
    cliff: float | None = None,
) -> tuple[float, float]:
    """Approximate the Hermes tweet curves for animation without a full bench.

    Returns (before_fps, after_fps) at the given block count.
    Pink line holds ~60 fps until ~18% of the run, then decays to floor.
    Cyan line stays flat at target_fps.
    """
    after = target_fps
    cliff_n = cliff if cliff is not None else max(8.0, 0.18 * total)
    if blocks <= cliff_n:
        before = target_fps
    else:
        t = (blocks - cliff_n) / max(total - cliff_n, 1)
        decay = (1.0 - t) ** 1.35
        before = floor_fps + (target_fps - floor_fps) * decay
        wobble = 1.2 * ((blocks % 17) / 17.0 - 0.5) * t
        before = _clamp(before + wobble, floor_fps, target_fps)
    return before, after
