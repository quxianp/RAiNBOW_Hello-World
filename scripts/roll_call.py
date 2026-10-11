#!/usr/bin/env python3
"""Animated roll call for the core languages.

    python scripts/roll_call.py --max 12
    python scripts/roll_call.py --max 12 --delay 0.07

Prints `+ <Language>` lines with a rainbow wave travelling through them: the hue
offset shifts every frame, and lines are emitted one at a time so the recording
has real motion instead of 12 lines appearing instantly.

Reads the same list the rest of the show uses (config/core-langs.txt) and falls
back to a plain listing when stdout is not a terminal, so logs and CI output stay
readable.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIST = ROOT / "config" / "core-langs.txt"

RESET = "\033[0m"
DIM = "\033[2m"
BOLD = "\033[1m"


def hsl_to_rgb(h: float, s: float = 0.85, l: float = 0.6):
    h = (h % 360.0) / 360.0

    def hue(p, q, t):
        t %= 1.0
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            return p + (q - p) * (2 / 3 - t) * 6
        return p

    if s == 0:
        v = int(l * 255)
        return v, v, v
    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q
    return (int(hue(p, q, h + 1 / 3) * 255),
            int(hue(p, q, h) * 255),
            int(hue(p, q, h - 1 / 3) * 255))


def names() -> list[str]:
    if LIST.is_file():
        out = [l.strip() for l in LIST.read_text(encoding="utf-8").splitlines()]
        return [n for n in out if n]
    return []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max", type=int, default=12, help="how many to print")
    ap.add_argument("--delay", type=float, default=0.07, help="seconds per line")
    ap.add_argument("--total", type=int, default=0,
                    help="total count, for the '+N more' line (0 = autodetect)")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    all_names = names()
    total = args.total or len(all_names)
    shown = max(0, args.max)
    picked = all_names[:shown]
    tty = sys.stdout.isatty() and os.environ.get("RAINBOW_PLAIN", "0") not in ("1", "true")

    if not tty:
        for name in picked:
            sys.stdout.write(f"    + {name}\n")
        hidden = total - len(picked)
        if hidden > 0:
            sys.stdout.write(f"    ... +{hidden} more core languages\n")
        sys.stdout.flush()
        return 0

    # a rainbow wave rolls through the list; each line is one step of the wave
    for i, name in enumerate(picked):
        base = (i * 22.0) % 360.0
        cells = []
        for j, ch in enumerate(name):
            if ch == " ":
                cells.append(" ")
                continue
            r, g, b = hsl_to_rgb(base + j * 14.0)
            cells.append(f"\033[38;2;{r};{g};{b}m{ch}")
        sys.stdout.write("    + " + "".join(cells) + RESET + "\n")
        sys.stdout.flush()
        time.sleep(args.delay)

    hidden = total - len(picked)
    if hidden > 0:
        sys.stdout.write(f"    {DIM}... +{hidden} more core languages{RESET}\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())