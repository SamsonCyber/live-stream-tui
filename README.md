# live-stream-tui

Live markdown streaming and Hermes-style render-rate graphs in the terminal.

Reference: [NousResearch TUI never drops a frame](https://x.com/imbabybrooklyn/status/2078686371573571817). Dual-line chart: naive O(n) re-parse falls off 60 fps; per-block incremental stays flat at 60 fps while 1,024 blocks stream in.

```
 live-stream graph ──► braille dual-line chart (before pink / after cyan)
 live-stream demo ──► FPS-capped MarkdownStream coalesce
 live-stream grok ──► real Grok streaming-json
```

## Install

```bash
git clone https://github.com/SamsonCyber/live-stream-tui.git
cd live-stream-tui
pip install -e .
```

Needs Python 3.11+, `textual`, `rich` (and `markdown-it-py` via textual).

## Graph mode (the reference)

```powershell
# animated Hermes curve (matches the tweet shape)
py -3.12 -m live_stream_tui graph

# measure local markdown-it full re-parse vs append-only
py -3.12 -m live_stream_tui graph --mode bench --blocks 1024

# denser samples / faster paint
py -3.12 -m live_stream_tui graph --fps 60 --sample-every 2
```

Keys: `q` quit · `r` restart · `m` toggle bench/replay · `f` toggle fill.

Chrome is **transparent** so Windows Terminal wallpaper / opacity shows through.
Color lives on the curves: sky `#38bdf8` after, pink `#ec4899` before, soft fill in the gap.

Chart:

| series | meaning |
|--------|---------|
| cyan **after** | per-block incremental: settled blocks parse once, O(tail) |
| pink **before** | stable-prefix split: O(n) re-parse each time a block settles |
| pink **fill** | area between curves (`f` or `--no-fill`) |

X = markdown blocks rendered (0…1024). Y = effective render rate (fps).

## Markdown stream mode

```powershell
py -3.12 -m live_stream_tui demo
py -3.12 -m live_stream_tui demo --stress
py -3.12 -m live_stream_tui flood --chars 20000
py -3.12 -m live_stream_tui grok "Explain RoPE in 3 bullets with a tiny code sample"
grok -p "hello" --output-format streaming-json | py -3.12 -m live_stream_tui pipe
```

Keys: `q` quit · `a` autoscroll · `p` pause.

Stream path uses Textual `MarkdownStream` so token floods coalesce into
incremental `append` (no full-document `update` thrash).

## Event format (pipe / grok)

```json
{"type":"text","data":"Hello"}
{"type":"thought","data":"..."}
{"type":"end","stopReason":"EndTurn"}
{"type":"error","message":"..."}
```

## Layout

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

## License

MIT. See [LICENSE](LICENSE).

