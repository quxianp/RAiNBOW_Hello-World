#!/usr/bin/env python3
"""Animated rainbow intro banner.

    python scripts/brand_frames.py [--frames 18] [--text RAiNBOW_Hello-World]

Prints the brand word one frame at a time with a hue sweep running across the
letters, clearing the screen between frames, then leaves the final frame on
screen.

This exists because run.sh's own intro computed a hue per character and then
threw it away:

    h=$(( ( (frame * 24 + i * 8) % 360 ) ))
    printf '%s' "$(rgb 255 255 255)"   # <- h never used; always white

so the "animated" opening was 8 identical all-white frames. Doing the hue maths
in Python keeps the colour maths honest and keeps run.sh readable, and it runs
the whole animation in one process instead of forking per frame.
"""

from __future__ import annotations

import argparse
import os
import sys
import time

CLEAR = "\033[2J\033[H"
HIDE = "\033[?25l"
SHOW = "\033[?25h"
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


def hsl_to_rgb(h: float, s: float = 0.95, l: float = 0.58):
    """h in degrees -> (r, g, b) ints. Same formula as scripts/rainbow.py."""
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


def frame_line(text: str, frame: int, frames: int, subtitle: str) -> str:
    n = len(text)
    step = 360.0 / max(n, 1)
    out = [BOLD]
    for i, ch in enumerate(text):
        h = frame * (360.0 / max(frames, 1)) + i * step
        r, g, b = hsl_to_rgb(h)
        out.append(f"\033[38;2;{r};{g};{b}m{ch}")
    out.append(RESET + "\n")
    out.append(DIM + subtitle + RESET + "\n")
    return "".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--text", default="RAiNBOW_Hello-World")
    ap.add_argument("--frames", type=int, default=18)
    ap.add_argument("--delay", type=float, default=0.055)
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--plain", action="store_true",
                    help="print a single static line (no cursor tricks)")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if args.plain or not sys.stdout.isatty():
        sys.stdout.write(BOLD + args.text + RESET + "\n")
        if args.subtitle:
            sys.stdout.write(DIM + args.subtitle + RESET + "\n")
        return 0

    sys.stdout.write(HIDE)
    sys.stdout.flush()
    try:
        for f in range(args.frames):
            sys.stdout.write(CLEAR)
            sys.stdout.write(frame_line(args.text, f, args.frames, args.subtitle))
            sys.stdout.flush()
            time.sleep(args.delay)
        # leave the last frame on screen for the roll call
        sys.stdout.write(CLEAR)
        sys.stdout.write(frame_line(args.text, args.frames - 1, args.frames,
                                    args.subtitle))
        sys.stdout.flush()
    finally:
        sys.stdout.write(SHOW)
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())