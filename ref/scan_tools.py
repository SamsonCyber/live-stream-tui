from pathlib import Path
import re
import json

p = Path(r"C:\Users\shotg\.grok\sessions\C%3A%5CCode\019fc54c-3ad8-7530-9a19-8f4b208a126e\chat_history.jsonl")
if not p.exists():
    print("missing", p)
    raise SystemExit(1)
text = p.read_text(encoding="utf-8", errors="replace")
print("chat len", len(text))
print("stream_graph in chat", "stream_graph" in text)
# Tool call titles from updates style
titles = re.findall(r'"title":"([a-zA-Z0-9_-]+)"', text)
from collections import Counter
c = Counter(titles)
print("top titles", c.most_common(30))
print("has stream_graph title", "stream_graph" in c)

# Also look in system message area for Available Tools
idx = text.find("stream_graph")
print("first stream_graph idx", idx)
if idx >= 0:
    print(text[idx - 40 : idx + 80].replace("\n", " "))
