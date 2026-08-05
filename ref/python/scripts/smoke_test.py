"""Headless checks: parse, demo, metrics, flood, chart, bench."""

from __future__ import annotations

import time

from rich.console import Console

from live_stream_tui.bench import measure_parse_paths
from live_stream_tui.chart import ChartState, RenderRateChart, hermes_synthetic_curve
from live_stream_tui.metrics import StreamMetrics
from live_stream_tui.ndjson import parse_line
from live_stream_tui.sources import demo_chunks, find_grok, flood_chunks


def test_parse() -> None:
    assert parse_line('{"type":"text","data":"Hi"}').data == "Hi"
    assert parse_line('{"type":"end"}').kind == "end"
    assert parse_line('{"type":"error","message":"boom"}').data == "boom"
    assert parse_line("plain line").kind == "text"


def test_demo() -> None:
    n = 0
    chars = 0
    for line in demo_chunks(delay=0):
        ev = parse_line(line)
        if ev and ev.kind == "text":
            n += 1
            chars += len(ev.data)
        if ev and ev.kind == "end":
            break
    assert n > 10
    assert chars > 100
    print("ok demo chunks", n, "chars", chars)


def test_flood_fast() -> None:
    t0 = time.perf_counter()
    chars = 0
    chunks = 0
    for line in flood_chunks(total_chars=2000, chunk_size=1, delay=0):
        ev = parse_line(line)
        if ev and ev.kind == "text":
            chunks += 1
            chars += len(ev.data)
    elapsed = time.perf_counter() - t0
    assert chars >= 2000
    assert chunks >= 100
    print(f"ok flood chars={chars} chunks={chunks} in {elapsed*1000:.1f}ms")


def test_metrics_spark() -> None:
    m = StreamMetrics(capacity=8)
    for i in range(12):
        m.note_chunk(10 + i)
        m.note_paint(float(i))
        m.tick()
    s = m.chars_spark(8)
    p = m.paint_spark(8)
    assert len(s) == 8
    assert len(p) == 8
    line = m.status_line(fps_cap=30.0, done=False, err=None)
    assert "streaming" in line
    print("ok metrics", line[:80])


def test_hermes_curve() -> None:
    b0, a0 = hermes_synthetic_curve(50)
    b1, a1 = hermes_synthetic_curve(1024)
    assert a0 == 60.0 and a1 == 60.0
    assert b0 >= 55.0
    assert b1 < 20.0
    print(f"ok curve early before={b0:.1f} late before={b1:.1f}")


def test_chart_render() -> None:
    st = ChartState(show_fill=True)
    for blocks in range(4, 257, 4):
        bf, af = hermes_synthetic_curve(blocks)
        st.push(float(blocks), bf, af)
    chart = RenderRateChart(st, plot_height=10)
    console = Console(record=True, width=100, height=30, force_terminal=True, color_system="truecolor")
    console.print(chart)
    text = console.export_text(styles=False)
    assert "Hermes TUI" in text
    assert "blocks" in text.lower() or "1024" in text or "256" in text
    # fill should place braille between curves once decay starts
    assert any(ord(c) >= 0x2800 for c in text), "expected braille glyphs"
    print("ok chart render lines", text.count("\n"))


def test_bench_short() -> None:
    pts = list(measure_parse_paths(32, sample_every=8))
    assert len(pts) >= 3
    assert pts[-1].blocks == 32
    assert pts[-1].chars > 0
    print("ok bench points", len(pts), "last_before_ms", f"{pts[-1].before_ms:.3f}")


def main() -> None:
    test_parse()
    test_demo()
    test_flood_fast()
    test_metrics_spark()
    test_hermes_curve()
    test_chart_render()
    test_bench_short()
    print("grok", find_grok())
    print("ALL OK")


if __name__ == "__main__":
    main()
