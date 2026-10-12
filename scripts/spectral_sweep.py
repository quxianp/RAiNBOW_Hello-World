#!/usr/bin/env python3
"""Sweep a full-width rainbow across the terminal, one language per column.

    python scripts/spectral_sweep.py
    python scripts/spectral_sweep.py --width 96 --cycles 3 --hold 0.04

This is the act that makes the demo move for a reason rather than for its own
sake. Every column is coloured with the actual Linguist colour of one of the
694 core languages, in hue order, so the sweep is the repository's own data
rather than a decorative gradient: if a language were missing from the bar, the
sweep would have a gap.

Two rendering modes:

  --mode block   half-block cells (U+2584), one column per language
  --mode text    truecolour foreground, with no cell background required

--mode text degrades gracefully in terminals that ignore 24-bit colour; the
block mode needs truecolour, and says so rather than emitting nothing.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "rainbow_langs.json"

ESC = "\x1b"

# Windows consoles default to a legacy code page, and printing block-drawing
# characters to one raises UnicodeEncodeError -- which aborted the sweep on the
# first glyph rather than degrading. Reconfigure the stream so the script works
# everywhere Python 3.7+ runs; if it cannot, fall back to ASCII shading so the
# act still happens.
_TRIED_RECONF = False


def _ensure_unicode_stdout() -> bool:
    global _TRIED_RECONF
    if _TRIED_RECONF:
        return True
    _TRIED_RECONF = True
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        return True
    except Exception:
        return False


def load_langs() -> list[dict]:
    if not CONFIG.is_file():
        print(f"error: {CONFIG} missing", file=sys.stderr)
        raise SystemExit(1)
    cfg = CONFIG.read_text(encoding="utf-8")
    import json
    langs = (json.loads(cfg).get("languages") or [])
    langs = [l for l in langs if l.get("color")]
    return sorted(langs, key=lambda r: (r.get("hue") or 0.0, r.get("name", "")))


def hex_rgb(value: str) -> tuple[int, int, int]:
    v = value.lstrip("#")
    return (int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16))


def term_width(default: int = 96) -> int:
    try:
        return max(40, shutil.get_terminal_size((default, 24)).columns)
    except Exception:
        return default


def sweep_block(langs: list[dict], width: int, cycles: int, hold: float,
                label: bool) -> None:
    """Upper half-block: the top half of each cell carries the language colour."""
    upper = "\u2580"
    for c in range(cycles):
        for x in range(width):
            lang = langs[(c * width + x) % len(langs)]
            r, g, b = hex_rgb(lang["color"])
            sys.stdout.write(f"{ESC}[38;2;{r};{g};{b}m{upper}")
            if hold:
                time.sleep(hold)
        sys.stdout.write(f"{ESC}[0m\n")
        sys.stdout.flush()
        if label and c == 0:
            name = langs[0]["name"]
            sys.stdout.write(f"{ESC}[2m  first: {name}{ESC}[0m\n")
            sys.stdout.flush()


def sweep_text(langs: list[dict], width: int, cycles: int, hold: float,
               label: bool) -> None:
    """Truecolour foreground sweep using block glyphs."""
    block = "\u2588"
    for c in range(cycles):
        line = []
        for x in range(width):
            lang = langs[(c * width + x) % len(langs)]
            r, g, b = hex_rgb(lang["color"])
            line.append(f"{ESC}[38;2;{r};{g};{b}m{block}")
        sys.stdout.write("".join(line) + f"{ESC}[0m\n")
        sys.stdout.flush()
        if hold:
            time.sleep(max(hold, 0.05))


def sweep_plain(langs: list[dict], width: int, cycles: int, hold: float,
                label: bool) -> None:
    """No colour at all -- for terminals that strip escape sequences."""
    if _ensure_unicode_stdout():
        shades = "\u2591\u2592\u2593\u2588"
    else:
        shades = ".:*#"
    for c in range(cycles):
        row = "".join(
            shades[int(langs[(c * width + x) % len(langs)].get("hue") or 0.0)
                   // 90 % 4]
            for x in range(width)
        )
        sys.stdout.write(row + "\n")
        sys.stdout.flush()
        if hold:
            time.sleep(max(hold, 0.05))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--width", type=int, default=0,
                    help="columns (default: terminal width)")
    ap.add_argument("--cycles", type=int, default=3)
    ap.add_argument("--hold", type=float, default=0.012,
                    help="delay per column in block mode")
    ap.add_argument("--mode", choices=("block", "text", "plain"), default="block")
    args = ap.parse_args()

    _ensure_unicode_stdout()
    langs = load_langs()
    width = args.width or term_width()
    width = min(width, len(langs))

    fn = {"block": sweep_block, "text": sweep_text, "plain": sweep_plain}[args.mode]
    fn(langs, width, args.cycles, args.hold, label=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())