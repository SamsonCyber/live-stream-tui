"""CLI entry: live-stream graph | demo | pipe | grok | flood."""

from __future__ import annotations

import argparse
import sys

from live_stream_tui.app import run_app
from live_stream_tui.graph_app import run_graph_app
from live_stream_tui.sources import demo_chunks, flood_chunks, grok_stream, stdin_lines


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="live-stream",
        description=(
            "Live markdown stream TUI + Hermes-style render-rate graphs. "
            "Token floods coalesce; graphs show before/after FPS as blocks stream."
        ),
    )
    p.add_argument(
        "--fps",
        type=float,
        default=30.0,
        help="max paint drain rate (default 30).",
    )
    p.add_argument(
        "--thoughts",
        action="store_true",
        help="show thought events (markdown modes only)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    gr = sub.add_parser(
        "graph",
        help="live dual-line FPS chart (Hermes tweet: before O(n) vs after O(tail))",
    )
    gr.add_argument(
        "--blocks",
        type=int,
        default=1024,
        help="markdown blocks to stream on the X axis (default 1024)",
    )
    gr.add_argument(
        "--mode",
        choices=("bench", "replay"),
        default="replay",
        help="replay = Hermes curve shape; bench = measure local markdown-it parse",
    )
    gr.add_argument(
        "--sample-every",
        type=int,
        default=4,
        help="sample every N blocks (default 4)",
    )
    gr.add_argument(
        "--no-fill",
        action="store_true",
        help="disable soft pink fill between before/after curves",
    )

    d = sub.add_parser("demo", help="synthetic markdown stream (no grok)")
    d.add_argument("--delay", type=float, default=0.025, help="seconds between chunks")
    d.add_argument(
        "--stress",
        action="store_true",
        help="longer markdown body to stress incremental parse",
    )

    f = sub.add_parser(
        "flood",
        help="max-rate char flood (proves coalesce; status thr/lat sparklines)",
    )
    f.add_argument("--chars", type=int, default=8000, help="total characters")
    f.add_argument("--chunk", type=int, default=1, help="chars per NDJSON event")
    f.add_argument("--delay", type=float, default=0.0, help="sleep between events")

    sub.add_parser("pipe", help="read streaming-json NDJSON from stdin")

    g = sub.add_parser("grok", help="run: grok -p PROMPT --output-format streaming-json")
    g.add_argument("prompt", help="prompt string")
    g.add_argument("-m", "--model", default=None, help="model id for grok -m")
    g.add_argument(
        "--yolo",
        action="store_true",
        help="pass --yolo to grok (auto-approve tools)",
    )

    args = p.parse_args(argv)

    if args.cmd == "graph":
        run_graph_app(
            total_blocks=args.blocks,
            fps=args.fps,
            mode=args.mode,
            sample_every=args.sample_every,
            show_fill=not args.no_fill,
        )
        return 0

    if args.cmd == "demo":
        run_app(
            demo_chunks(delay=args.delay, stress=args.stress),
            fps=args.fps,
            show_thoughts=args.thoughts,
            title="live-stream · demo",
        )
        return 0

    if args.cmd == "flood":
        run_app(
            flood_chunks(
                total_chars=args.chars,
                chunk_size=max(1, args.chunk),
                delay=args.delay,
            ),
            fps=args.fps,
            show_thoughts=args.thoughts,
            title="live-stream · flood",
        )
        return 0

    if args.cmd == "pipe":
        if sys.stdin.isatty():
            print(
                "pipe mode needs stdin. Example:\n"
                '  grok -p "explain RoPE" --output-format streaming-json | live-stream pipe',
                file=sys.stderr,
            )
            return 2
        run_app(
            stdin_lines(),
            fps=args.fps,
            show_thoughts=args.thoughts,
            title="live-stream · pipe",
        )
        return 0

    if args.cmd == "grok":
        extra = ["--yolo"] if args.yolo else None
        try:
            it = grok_stream(args.prompt, model=args.model, extra_args=extra)
        except FileNotFoundError as e:
            print(str(e), file=sys.stderr)
            return 1
        run_app(
            it,
            fps=args.fps,
            show_thoughts=args.thoughts,
            title="live-stream · grok",
        )
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
