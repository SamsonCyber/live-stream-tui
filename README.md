# live-stream-tui

<<<<<<< HEAD
Live **markdown stream** TUI + Hermes-style **render-rate graph**, as a
**Grok Build harness add-on**.

The real binary is Rust. It sits inside a local [xai-org/grok-build](https://github.com/xai-org/grok-build)
checkout and uses the same `StreamingMarkdownRenderer` the pager uses for
incremental markdown (checkpoint freeze, O(tail) re-render).

Upstream grok-build does **not** accept external PRs. This repo is the public
surface + docs + prototype archive. Implementation lives as a local crate in
your harness tree:

```
grok-build/crates/codegen/xai-live-stream-tui/
=======
Live markdown streaming and Hermes-style render-rate graphs in the terminal.

Reference: [NousResearch TUI never drops a frame](https://x.com/imbabybrooklyn/status/2078686371573571817). Dual-line chart: naive O(n) re-parse falls off 60 fps; per-block incremental stays flat at 60 fps while 1,024 blocks stream in.

```
 live-stream graph â”€â”€â–º braille dual-line chart (before pink / after cyan)
 live-stream demo â”€â”€â–º FPS-capped MarkdownStream coalesce
 live-stream grok â”€â”€â–º real Grok streaming-json
>>>>>>> origin/main
```

## Why not the Python prototype?

`ref/python/` is the old Textual demo. Headless smokes passed; the live TUI
could crash on stream end, and it never used Grok Build's real markdown path.
Rust + `xai-grok-markdown` is the product.

## In Grok (primary)

The graph is **embedded in the Grok pager chat** as an intentional data
stream. It auto-shows when the agent calls **`stream_graph`** (or other
code feeds plot points). Markdown text streaming does **not** open it.
Optional pin:

```
/graph              pin plot band (stays) or dismiss (suppress until quiet)
/graph mode         plot <-> demo <-> live
/graph fill         pink fill on/off
/debug graph        same as /graph
```

See [GROK-INTEGRATION.md](GROK-INTEGRATION.md).

## Standalone binary (requires local grok-build)

```bat
cd /d C:\Code\grok-build
cargo build -p xai-live-stream-tui --release
target\release\live-stream.exe graph --dump
```

## Use

```powershell
# Hermes dual-line FPS graph (replay curve)

cargo run -p xai-live-stream-tui -- graph

# Measure full re-parse vs StreamingMarkdownRenderer

cargo run -p xai-live-stream-tui -- graph --mode bench --blocks 128

# Synthetic stream

cargo run -p xai-live-stream-tui -- demo
cargo run -p xai-live-stream-tui -- flood --chars 20000

# Real Grok headless stream into the TUI

cargo run -p xai-live-stream-tui -- grok "Explain RoPE in 3 bullets" --yolo

# Pipe any streaming-json producer

grok -p "hello" --output-format streaming-json | cargo run -p xai-live-stream-tui -- pipe
```

<<<<<<< HEAD
Keys (stream): `q` quit Ã‚Â· `a` autoscroll Ã‚Â· `p` pause Ã‚Â· arrows scroll  
Keys (graph): `q` quit Ã‚Â· `r` restart Ã‚Â· `m` toggle replay/bench Ã‚Â· `f` fill
=======
Keys: `q` quit Â· `r` restart Â· `m` toggle bench/replay Â· `f` toggle fill.

Chrome is **transparent** so Windows Terminal wallpaper / opacity shows through.
Color lives on the curves: sky `#38bdf8` after, pink `#ec4899` before, soft fill in the gap.

Chart:

| series | meaning |
|--------|---------|
| cyan **after** | per-block incremental: settled blocks parse once, O(tail) |
| pink **before** | stable-prefix split: O(n) re-parse each time a block settles |
| pink **fill** | area between curves (`f` or `--no-fill`) |

X = markdown blocks rendered (0â€¦1024). Y = effective render rate (fps).

## Markdown stream mode

```powershell
py -3.12 -m live_stream_tui demo
py -3.12 -m live_stream_tui demo --stress
py -3.12 -m live_stream_tui flood --chars 20000
py -3.12 -m live_stream_tui grok "Explain RoPE in 3 bullets with a tiny code sample"
grok -p "hello" --output-format streaming-json | py -3.12 -m live_stream_tui pipe
```

Keys: `q` quit Â· `a` autoscroll Â· `p` pause.

Stream path uses Textual `MarkdownStream` so token floods coalesce into
incremental `append` (no full-document `update` thrash).
>>>>>>> origin/main

## Event format (pipe / grok)

Same as Grok Build headless emitter (`xai-grok-pager` headless):

```json
{"type":"text","data":"Hello"}
{"type":"thought","data":"..."}
{"type":"end","stopReason":"EndTurn"}
{"type":"error","message":"..."}
```

Other types (`available_commands`, `usage`, Ã¢â‚¬Â¦) are ignored.

## Architecture

```
grok --output-format streaming-json
        Ã¢â€â€š  NDJSON text/thought/end
        Ã¢â€“Â¼
  live-stream (this crate)
        Ã¢â€â€š  coalesce at --fps
        Ã¢â€“Â¼
  xai_grok_markdown::StreamingMarkdownRenderer
        Ã¢â€â€š  freeze settled blocks, re-render tail
        Ã¢â€“Â¼
  ratatui (stream view + Hermes graph)
```

Graph series:

| series | meaning |
|--------|---------|
| cyan **after** | streaming renderer (O(tail)) |
| pink **before** | full `render_markdown_ratatui_full` each update (O(n)) |

## Layout

<<<<<<< HEAD
| path | role |
|------|------|
| `../grok-build/crates/codegen/xai-live-stream-tui/` | Rust implementation |
| `ref/` | Hermes tweet frames / video |
| `ref/python/` | retired Textual prototype |
=======
```
src/live_stream_tui/
 theme.py Hermes truecolor palette + transparent CSS
 chart.py braille dual-series renderer (Hermes layout + fill)
 graph_app.py live graph TUI
 bench.py before/after parse cost sampler
 app.py markdown stream TUI
 sources.py demo / flood / grok / stdin
 metrics.py thr/lat sparklines for stream mode
```


## Roadmap

- [x] Shade fill between before/after curves
- [x] Transparent chrome (host terminal background shows through)
- [x] Truecolor Hermes pink / cyan palette
- [ ] Overlay real Textual paint ms from stream mode onto the same chart
- [ ] Tool-call panels from richer event streams
- [ ] ratatui + mdstream backend
>>>>>>> origin/main

## License

MIT for this packaging repo. The harness crate is Apache-2.0 like Grok Build
(local add-on; not an upstream contribution).
