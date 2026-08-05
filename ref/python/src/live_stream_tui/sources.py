"""Stream sources: demo, pipe stdin, grok subprocess."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterator, List, Optional


DEMO_MARKDOWN = """# Live stream demo

Streaming markdown with **bold**, *italic*, and `code`.

Hermes-style: tokens flood in; the TUI paints at a fixed cadence and
**never thrash-reparses** the whole document.

## List

- item one
- item two
- item three
- nested idea with a longer line that wraps under stress

## Code

```python
def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

# stream-friendly: fence stays open until the closer lands
print(fib(12))
```

## Table

| plane | speed | role |
|------:|------:|------|
| 0 | slow | long range |
| 7 | fast | local |
| 3 | mid | burst |

## Math-ish (literal)

`score(m,n) = q · R(n-m) k`

## More prose for stress

The frame budget is sacred. If the model dumps 200 tokens in a blink,
we coalesce: one append, not 200 full markdown rebuilds. Completed
blocks freeze; only the open line re-parses. That is how the status
sparkline stays flat instead of looking like a seismograph of shame.

Done.
"""

# Heavier demo for visual stress (CLI --stress).
STRESS_MARKDOWN = (
    DEMO_MARKDOWN
    + "\n\n## Stress block\n\n"
    + "\n\n".join(
        f"Paragraph {i}: " + ("lorem ipsum dolor sit amet " * 8)
        for i in range(1, 40)
    )
    + "\n\n```rust\n"
    + "\n".join(f"// line {i}: fn stress_{i}() {{ let x = {i}; }}" for i in range(80))
    + "\n```\n\n# Fin\n"
)


def demo_chunks(
    delay: float = 0.03,
    *,
    markdown: Optional[str] = None,
    stress: bool = False,
) -> Iterator[str]:
    """Yield NDJSON text events in small chunks."""
    text = markdown if markdown is not None else (STRESS_MARKDOWN if stress else DEMO_MARKDOWN)
    i = 0
    while i < len(text):
        n = 1 if text[i] in "\n`#" else min(4, len(text) - i)
        chunk = text[i : i + n]
        i += n
        yield json.dumps({"type": "text", "data": chunk}) + "\n"
        if delay > 0:
            time.sleep(delay)
    yield json.dumps({"type": "end", "stopReason": "EndTurn"}) + "\n"


def flood_chunks(
    *,
    total_chars: int = 8000,
    chunk_size: int = 1,
    delay: float = 0.0,
) -> Iterator[str]:
    """Max-rate flood to prove coalesce (no frame thrash)."""
    remaining = total_chars
    n = 0
    while remaining > 0:
        take = min(chunk_size, remaining)
        # Mix newlines so markdown forms real blocks under flood.
        if n > 0 and n % 40 == 0:
            data = "\n\n"
        elif n > 0 and n % 12 == 0:
            data = " **x** "
        else:
            data = "x" * take
        remaining -= take
        n += 1
        yield json.dumps({"type": "text", "data": data}) + "\n"
        if delay > 0:
            time.sleep(delay)
    yield json.dumps({"type": "end", "stopReason": "EndTurn"}) + "\n"


def stdin_lines() -> Iterator[str]:
    for line in sys.stdin:
        yield line


def find_grok() -> Optional[str]:
    w = shutil.which("grok")
    if w:
        return w
    cand = Path.home() / ".grok" / "bin" / "grok.exe"
    if cand.is_file():
        return str(cand)
    cand2 = Path.home() / ".grok" / "bin" / "grok"
    if cand2.is_file():
        return str(cand2)
    return None


def grok_stream(
    prompt: str,
    *,
    model: Optional[str] = None,
    cwd: Optional[str] = None,
    extra_args: Optional[List[str]] = None,
) -> Iterator[str]:
    """Spawn `grok -p ... --output-format streaming-json` and yield NDJSON lines."""
    exe = find_grok()
    if not exe:
        raise FileNotFoundError("grok not on PATH (install Grok CLI or add ~/.grok/bin)")
    cmd = [exe, "-p", prompt, "--output-format", "streaming-json"]
    if model:
        cmd.extend(["-m", model])
    if extra_args:
        cmd.extend(extra_args)
    env = os.environ.copy()
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=cwd or os.getcwd(),
        env=env,
    )
    assert proc.stdout is not None
    try:
        for line in proc.stdout:
            yield line
    finally:
        try:
            proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
        if proc.returncode not in (0, None) and proc.stderr:
            err = proc.stderr.read()
            if err.strip():
                yield json.dumps({"type": "error", "message": err.strip()[:2000]}) + "\n"
