from pathlib import Path
import json

up = Path(
    r"C:\Users\shotg\.grok\sessions\C%3A%5CCode\019fc54c-3ad8-7530-9a19-8f4b208a126e\updates.jsonl"
)
# Find lines that look like tool list / definitions with stream_graph
for i, line in enumerate(up.open(encoding="utf-8", errors="replace"), 1):
    if "stream_graph" not in line:
        continue
    # skip giant grep dumps
    if "workspace_result" in line or "match_count" in line:
        continue
    if len(line) > 20000:
        # maybe tool defs
        if "toolDefinitions" in line or "available_tools" in line or "ListTools" in line:
            print(f"LINE {i} len={len(line)}")
            # extract around stream_graph
            idx = line.find("stream_graph")
            print(line[max(0, idx - 100) : idx + 200][:400])
            print("---")
        continue
    print(f"LINE {i} len={len(line)}")
    idx = line.find("stream_graph")
    print(line[max(0, idx - 80) : idx + 160][:300])
    print("---")
    if i > 5000:
        break
