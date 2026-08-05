"""Hermes-style palette: truecolor on a transparent terminal background.

Intentionally no solid screen fills so Windows Terminal (or any terminal
wallpaper / opacity) shows through. Lines and labels carry the color.
"""

from __future__ import annotations

# After curve: flat 60 fps incremental path (sky / cyan)
AFTER = "#38bdf8"
AFTER_DIM = "#0ea5e9"
AFTER_TIP = "bold #38bdf8"

# Before curve: O(n) re-parse decay (hot pink)
BEFORE = "#ec4899"
BEFORE_DIM = "#db2777"
BEFORE_TIP = "bold #ec4899"

# Soft fill between the two series (gap / wasted re-parse)
FILL = "#f9a8d4"
FILL_DIM = "dim #f472b6"

# Chrome on transparent glass
TITLE = "bold #f8fafc"
SUBTITLE = "dim #94a3b8"
AXIS = "dim #64748b"
GRID = "dim #475569"
CURSOR = "dim #94a3b8"
STATUS_OK = "#86efac"
STATUS_STREAM = "#38bdf8"
STATUS_MUTED = "#94a3b8"
ACCENT = "#a78bfa"

# Shared CSS: fully transparent surfaces so the host terminal paints the bg.
TRANSPARENT_CSS = """
Screen {
    background: transparent;
    color: #e2e8f0;
}
Header {
    background: transparent;
    color: #f8fafc;
    text-style: bold;
    dock: top;
    height: 1;
}
Footer {
    background: transparent;
    color: #94a3b8;
    dock: bottom;
}
Footer > .footer--highlight {
    background: transparent;
    color: #38bdf8;
}
Footer > .footer--key {
    background: transparent;
    color: #ec4899;
    text-style: bold;
}
"""
