#!/usr/bin/env python3
"""A rainbow progress bar for the "executing languages" window.

    python scripts/spinner.py --label "executing core languages" --seconds 30

Prints an in-place-updating bar with a travelling hue highlight, so the stretch
of the show where languages are actually being executed has motion on screen
instead of a frozen prompt.

Runs until `--seconds` elapses or it receives SIGTERM/SIGINT, which is how
run.sh stops it, so the bar can wrap a subprocess whose duration is unknown.
Falls back to a single static line when stdout is not a terminal.
"""

from __future__ import annotations

import argparse
import os
import signal
import sys
import time

RESET = "\033[0m"
DIM = "\033[2m"
BOLD = "\033[1m"


def hsl_to_rgb(h: float, s: float = 0.9, l: float = 0.55):
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--label", default="working")
    ap.add_argument("--seconds", type=float, default=30.0)
    ap.add_argument("--width", type=int, default=60)
    ap.add_argument("--fps", type=float, default=12.0)
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    stop = False

    def handle(signum, frame):  # noqa: ARG001
        nonlocal stop
        stop = True

    signal.signal(signal.SIGTERM, handle)
    signal.signal(signal.SIGINT, handle)

    tty = sys.stdout.isatty()
    if not tty:
        sys.stdout.write(f"{DIM}  {args.label} ...{RESET}\n")
        return 0

    deadline = time.time() + args.seconds
    delay = 1.0 / max(args.fps, 1.0)
    cells = [chr(0x2591)] * args.width  # light shade for the empty track

    try:
        sys.stdout.write(HIDE := "\033[?25l")
        sys.stdout.flush()
        while not stop and time.time() < deadline:
            # a rainbow highlight sweeping across the bar, fading behind it
            head = int((time.time() * 26) % (args.width + 12))
            line = []
            for i in range(args.width):
                d = head - i
                if d <= 0:
                    line.append(cells[i])
                elif d < 14:
                    r, g, b = hsl_to_rgb((i / args.width) * 300.0 + time.time() * 120.0)
                    line.append(f"\033[38;2;{r};{g};{b}m\033[48;2;30;36;44m{chr(0x2588)}")
                else:
                    line.append(f"\033[38;2;30;36;44m\033[48;2;18;22;28m{chr(0x2588)}")
            sys.stdout.write("\r  " + BOLD + args.label + RESET + " "
                             + "".join(line) + RESET)
            sys.stdout.flush()
            time.sleep(delay)
    finally:
        sys.stdout.write("\033[?25h")
        sys.stdout.write("\r" + " " * (args.width + len(args.label) + 8) + "\r")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())