from pathlib import Path

recap = Path(r"C:\Users\shotg\.grok\sessions\C%3A%5CCode\019fc54c-3ad8-7530-9a19-8f4b208a126e")
needles = ['"name": "stream_graph"', '"name":"stream_graph"']
hits = []
for p in recap.rglob("*.json"):
    try:
        t = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        continue
    if any(n in t for n in needles):
        hits.append((str(p), t.count("stream_graph")))
print("stream_graph name hits:", hits[:20])

for p in recap.rglob("*.json"):
    try:
        t = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        continue
    if "image_gen" in t and "stream_graph" in t and p.stat().st_size < 5_000_000:
        print(
            "both image_gen+stream_graph:",
            p,
            "img",
            t.count("image_gen"),
            "sg",
            t.count("stream_graph"),
            "size",
            p.stat().st_size,
        )
