from pathlib import Path

root = Path(r"C:\Users\shotg\.grok\sessions")
needles = (
    'title":"stream_graph"',
    'name":"stream_graph"',
    '"stream_graph"',
)
hits = []
for p in root.rglob("updates.jsonl"):
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        continue
    if any(n in text for n in needles[:2]):
        hits.append(p)

print("hits", len(hits))
for h in hits[:20]:
    print(h)
    # show a short snippet around stream_graph tool call
    idx = h.read_text(encoding="utf-8", errors="replace").find("stream_graph")
    if idx >= 0:
        snippet = h.read_text(encoding="utf-8", errors="replace")[max(0, idx - 80) : idx + 120]
        print(" ", snippet.replace("\n", " ")[:200])
