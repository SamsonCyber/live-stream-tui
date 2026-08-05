from pathlib import Path
import json, re
base = Path(r"C:\Users\shotg\.grok\sessions\C%3A%5CCode\019fc54c-3ad8-7530-9a19-8f4b208a126e")
for name in ["resources_state.json", "summary.json", "announcement_state.json"]:
    p = base / name
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8", errors="replace")
    print("===", name, "len", len(t), "stream_graph", "stream_graph" in t)
    if "tool" in t.lower()[:5000] or "stream_graph" in t:
        print(t[:1500])
# scan updates for available tools list
up = base / "updates.jsonl"
if up.exists():
    text = up.read_text(encoding="utf-8", errors="replace")
    # find available tools
    for pat in ["available_tools", "toolDefinitions", "stream_graph", "ListTools"]:
        print(pat, text.count(pat))
