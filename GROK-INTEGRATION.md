# Grok Build integration

The Hermes stream graph is **inside the Grok pager chat TUI**, not only the
standalone `live-stream` binary.

## Already wired in `C:\Code\grok-build`

| Piece | Path |
|-------|------|
| Overlay HUD | `StreamGraphHud` on **each** `AgentView` (session-scoped) |
| Live samples | `push_chunk_to_agent` → session `scrollback.live_paint_samples` → drain into that agent's HUD |
| Slash | `/graph`, `/graph mode`, `/graph fill` (active session only) |
| Debug alias | `/debug graph` |
| Multi-session | No process-global ring. Session A paints never light session B's panel |
| Layout | Host carves reserved bottom band only; panel bg transparent (`Color::Reset`) |
| Actions | `ToggleStreamGraph`, `ToggleStreamGraphMode`, `ToggleStreamGraphFill` |
| General plots | `StreamGraphHud::note_series_point` multi-series line mode (adaptive Y) |

## Visibility (only when relevant)

| State | Behavior |
|-------|----------|
| Cold start | Off. No panel, no reserved height. |
| Agent markdown stream | **Never** opens the graph. Text paint is not a plot signal. |
| `stream_graph` tool / plot points | Auto-shows in **plot** mode (session sticky). |
| Quiet after plot | Hides after ~2.5s with no new points. Series cleared. |
| `/graph` pin | Stays until toggled off (survives idle). Default mode: plot. |
| `/graph` while on | Dismisses. Suppresses auto-show until a quiet gap, then next **plot** can show again. |
| Demo | Never auto-starts. Pin + `/graph mode` only. |
| Live paint mode | Pin + `/graph mode` only (debug). Not driven by text stream unpinned. |

Optional test pin (unit tests / env helper): truthy env to `StreamGraphHud::with_env`
starts demo-pinned. Production always uses `StreamGraphHud::new()` (off).

## Install local build (Windows)

From the grok-build tree after you change the pager:

```bat
cd /d C:\Code\grok-build
cargo build -p xai-grok-pager-bin --release
copy /Y target\release\xai-grok-pager.exe %USERPROFILE%\.grok\bin\grok.exe
```

Backup first if you want a rollback copy of the previous `grok.exe`.

## How to use in Grok

1. Start a **new** `grok` in Windows Terminal (existing sessions keep the old binary).
2. Ask for a chart, or have the agent call **`stream_graph`** with series + points.
3. Bottom band auto-shows in **plot** mode while points arrive. Hides after idle.
4. Optional pin:

```
/graph          :: pin plot band (stays until off) or dismiss if already on
/graph mode     :: plot <-> demo <-> live
/graph fill     :: toggle pink fill between curves
/debug graph    :: same toggle as /graph
```

### Agent tool: `stream_graph`

Must be on the **agent toolset** (`default_grok_build_toolset` / hashline) so the
model can call it. Registry-only registration is not enough.

```json
{ "series": "latency_ms", "points": [{"x": 0, "y": 12}, {"x": 1, "y": 18}] }
{ "series": "win_rate", "x": 3, "y": 0.62 }
{ "clear": true }
```

Pager reads tool `raw_input` → session HUD `note_series_point` / `clear_plot`.
New Grok session after rebuild is required for the model to see the tool.

## Modes

| mode | meaning |
|------|---------|
| **plot** | Named multi-series lines via `stream_graph` / `note_series_point` (default auto-show). |
| **demo** | Tweet-faithful synthetic before/after FPS curve (once; no auto-loop). Pin + mode. |
| **live** | Paint-cost debug series while **pinned** only. Not auto-driven by text stream. |

## Standalone crate (still useful)

`cargo run -p xai-live-stream-tui --release -- graph --dump`  
is the offline / pipe harness. Same visual language; not required for the in-app overlay.

## Tests

```bat
cd /d C:\Code\grok-build
cargo test -p xai-grok-pager --lib views::stream_graph
```
