# Graph Report - live-stream-tui  (2026-08-03)

## Corpus Check
- 29 files · ~133,884 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 136 nodes · 240 edges · 10 communities (8 shown, 2 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 5 edges (avg confidence: 0.56)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `84485bab`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- GraphApp
- LiveStreamApp
- chart.py
- cli.py
- StreamMetrics
- graph_app.py
- smoke_test.py
- __init__.py
- live-stream-tui
- README.md

## God Nodes (most connected - your core abstractions)
1. `GraphApp` - 18 edges
2. `LiveStreamApp` - 17 edges
3. `StreamMetrics` - 14 edges
4. `main()` - 9 edges
5. `ChartState` - 9 edges
6. `hermes_synthetic_curve()` - 9 edges
7. `measure_parse_paths()` - 8 edges
8. `RenderRateChart` - 8 edges
9. `main()` - 8 edges
10. `parse_line()` - 8 edges

## Surprising Connections (you probably didn't know these)
- `LiveStreamApp` --uses--> `StreamMetrics`  [INFERRED]
  ref/python/src/live_stream_tui/app.py → ref/python/src/live_stream_tui/metrics.py
- `test_parse()` --calls--> `parse_line()`  [EXTRACTED]
  ref/python/scripts/smoke_test.py → ref/python/src/live_stream_tui/ndjson.py
- `test_demo()` --calls--> `parse_line()`  [EXTRACTED]
  ref/python/scripts/smoke_test.py → ref/python/src/live_stream_tui/ndjson.py
- `test_demo()` --calls--> `demo_chunks()`  [EXTRACTED]
  ref/python/scripts/smoke_test.py → ref/python/src/live_stream_tui/sources.py
- `test_flood_fast()` --calls--> `parse_line()`  [EXTRACTED]
  ref/python/scripts/smoke_test.py → ref/python/src/live_stream_tui/ndjson.py

## Import Cycles
- None detected.

## Communities (10 total, 2 thin omitted)

### Community 0 - "GraphApp"
Cohesion: 0.12
Nodes (11): Mode, ChartState, Rich-renderable live chart matching the Hermes tweet layout., Live chart data for the Hermes render-rate plot., RenderRateChart, GraphApp, ComposeResult, Text (+3 more)

### Community 1 - "LiveStreamApp"
Cohesion: 0.12
Nodes (10): LiveStreamApp, ComposeResult, work, Textual TUI: never-drop-frame live markdown stream. Uses Textual's…, Stream markdown without thrashing: coalesce + incremental append., iter_events(), parse_line(), Parse Grok-style streaming-json NDJSON events. (+2 more)

### Community 2 - "chart.py"
Cohesion: 0.15
Nodes (20): Console, ConsoleOptions, _clamp(), _fill_between(), format_label(), hermes_synthetic_curve(), _plot_polyline(), Text (+12 more)

### Community 3 - "cli.py"
Cohesion: 0.23
Nodes (13): run_app(), main(), CLI entry: live-stream graph | demo | pipe | grok | flood., run_graph_app(), demo_chunks(), find_grok(), flood_chunks(), grok_stream() (+5 more)

### Community 4 - "StreamMetrics"
Cohesion: 0.19
Nodes (5): Deque, Live throughput / paint metrics for the status sparkline., Ring-buffered samples for a status-line sparkline., Sample chars/sec over the last tick interval (call ~1 Hz)., StreamMetrics

### Community 5 - "graph_app.py"
Cohesion: 0.24
Nodes (11): BenchPoint, block_stream(), _fps(), make_block(), measure_parse_paths(), Measure before/after markdown repaint cost as blocks stream in. Before: full-…, Map measured ms to display fps with a soft floor for empty noise. Prefer real…, One markdown block (settles on blank line). (+3 more)

### Community 6 - "smoke_test.py"
Cohesion: 0.36
Nodes (9): main(), Headless checks: parse, demo, metrics, flood, chart, bench., test_bench_short(), test_chart_render(), test_demo(), test_flood_fast(), test_hermes_curve(), test_metrics_spark() (+1 more)

### Community 9 - "README.md"
Cohesion: 0.29
Nodes (6): Hermes dual-line FPS graph (replay curve), live-stream-tui, Measure full re-parse vs StreamingMarkdownRenderer, Pipe any streaming-json producer, Real Grok headless stream into the TUI, Synthetic stream

## Knowledge Gaps
- **8 isolated node(s):** `live-stream-tui`, `Hermes dual-line FPS graph (replay curve)`, `Measure full re-parse vs StreamingMarkdownRenderer`, `Synthetic stream`, `Real Grok headless stream into the TUI` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LiveStreamApp` connect `LiveStreamApp` to `cli.py`, `StreamMetrics`?**
  _High betweenness centrality (0.166) - this node is a cross-community bridge._
- **Why does `GraphApp` connect `GraphApp` to `cli.py`, `graph_app.py`?**
  _High betweenness centrality (0.164) - this node is a cross-community bridge._
- **Why does `StreamMetrics` connect `StreamMetrics` to `LiveStreamApp`, `smoke_test.py`?**
  _High betweenness centrality (0.161) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `GraphApp` (e.g. with `ChartState` and `RenderRateChart`) actually correct?**
  _`GraphApp` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `LiveStreamApp` (e.g. with `StreamMetrics` and `StreamEvent`) actually correct?**
  _`LiveStreamApp` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `live-stream-tui`, `Hermes dual-line FPS graph (replay curve)`, `Measure full re-parse vs StreamingMarkdownRenderer` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `GraphApp` be split into smaller, more focused modules?**
  _Cohesion score 0.12307692307692308 - nodes in this community are weakly interconnected._