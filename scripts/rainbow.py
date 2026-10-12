#!/usr/bin/env python3
"""24-bit true-colour ANSI rainbow renderer.

Used by run.sh when lolcat is unavailable, and by the VHS recording.  Renders:
  * the repository's own language bar (every Linguist colour, in hue order)
  * ASCII "Hello World!" in per-language colours
  * animated wave / rainbow sweeps

Options:
  --bar                 render the language bar only
  --hello               render the ASCII art only
  --sweep N             animate N sweep frames (default 12)
  --width N             force the art width (default: terminal width)
  --plain               disable colour (for non-tty output)
  --no-animation        skip frames entirely
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import shutil
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config"

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
HOME = "\033[H"
CLEAR = "\033[2J\033[H"
HIDE = "\033[?25l"
SHOW = "\033[?25h"


def truecolor(r: int, g: int, b: int, text: str) -> str:
    return f"\033[38;2;{r};{g};{b}m{text}{RESET}"


def hex_to_rgb(value: str):
    v = (value or "").lstrip("#")
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    try:
        return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:
        return (200, 200, 200)


def hsl_to_rgb(h: float, s: float, ll: float):
    def hue(p, q, t):
        t = t % 1.0
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            return p + (q - p) * (2 / 3 - t) * 6
        return p

    if s == 0:
        v = ll * 255
        return int(v), int(v), int(v)
    q = ll * (1 + s) if ll < 0.5 else ll + s - ll * s
    p = 2 * ll - q
    r = hue(p, q, h + 1 / 3)
    g = hue(p, q, h)
    b = hue(p, q, h - 1 / 3)
    return int(r * 255), int(g * 255), int(b * 255)


def load_bar():
    path = CONFIG / "rainbow_langs.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("languages", [])


# --------------------------------------------------------------------------
# 5x7 block-letter font.
#
# Uppercase only, and every glyph fills all seven rows. The previous revision
# used lowercase glyphs whose bitmap rows were inconsistent -- 'e' and 'o' began
# with two empty rows, 'd' was ".##.#"/"#..##" and 'W' was really an 'M' shape --
# so the rendered word read as scattered confetti instead of "Hello World!".
# Splitting it across two lines also keeps it inside a 1200x800 VHS frame
# instead of wrapping off the right edge.
# --------------------------------------------------------------------------
FONT = {
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#.#", "#..#.", "#...#"],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "!": ["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."],
    " ": [".....", ".....", ".....", ".....", ".....", ".....", "....."],
}

TEXT_LINES = ["HELLO", "WORLD!"]


def ascii_art(scale: int = 2):
    """Two lines of filled block letters, each pixel `scale` wide and tall."""
    rows = []
    for line_no, text in enumerate(TEXT_LINES):
        letters = [FONT.get(c, FONT[" "]) for c in text]
        height = max(len(g) for g in letters)
        line_rows = []
        for y in range(height):
            out = ""
            for g in letters:
                glyph = g[y] if y < len(g) else "....."
                out += "".join(
                    ("\u2588" if ch == "#" else " ") * scale for ch in glyph
                )
                out += " " * scale
            line_rows.append(out.rstrip())
        # stretch vertically too, so the letters are as tall as they are wide
        for row in line_rows:
            for _ in range(scale):
                rows.append(row)
        if line_no != len(TEXT_LINES) - 1:
            rows.append("")
    return rows


# --------------------------------------------------------------------------
def render_bar(width: int, langs, plain: bool):
    if not langs:
        return []
    per = max(1, width // max(1, len(langs)))
    out = []
    for y in range(2):
        row = ""
        for rec in langs:
            r, g, b = rec.get("rgb") or hex_to_rgb(rec.get("color", "888888"))
            row += truecolor(r, g, b, "\u2588" * per) if not plain else "\u2588" * per
        out.append(row + RESET)
    return out


def render_colour_labels(langs, limit: int = 4):
    """A few annotated segments so the terminal output is not just a blob."""
    if not langs:
        return []
    out = []
    step = max(1, len(langs) // limit)
    for rec in langs[::step][:limit]:
        r, g, b = rec.get("rgb") or hex_to_rgb(rec.get("color", "888888"))
        out.append(truecolor(r, g, b, f"  {rec['name'][:28]:<28}") + RESET
                   + DIM + f" #{rec.get('color','?')} hue {rec.get('hue',0):.0f}" + RESET)
    return out


def sweep(frame: int, frames: int, width: int):
    rows = []
    cols = max(24, width)
    phase = frame / max(1, frames)
    for x in range(cols):
        h = (x / cols + phase) % 1.0
        r, g, b = hsl_to_rgb(h, 0.95, 0.55)
        rows.append(truecolor(r, g, b, "\u2588"))
    return ["".join(rows) + RESET]


def draw_fill(langs, width: int, frames: int, plain: bool):
    """The bar filling in, one language at a time, with a bright leading edge."""
    n = len(langs) or 1
    per = max(1, width // n)
    if plain or frames <= 0:
        for row in render_bar(width, langs, True):
            print(row)
        return

    sys.stdout.write(HIDE)
    try:
        for f in range(frames + 1):
            head = int(round(n * f / frames))
            sys.stdout.write(CLEAR)
            sys.stdout.write(
                BOLD + "  RAiNBOW_Hello-World language bar " + RESET + DIM
                + f"({head}/{n} languages on the bar \u00b7 "
                + f"{100.0 / n:.4f}% each)" + RESET + "\n"
            )
            row = ""
            for i, rec in enumerate(langs):
                r, g, b = rec.get("rgb") or hex_to_rgb(rec.get("color", "888888"))
                block = "\u2588" * per
                if i < head:
                    # the newest segment flashes white so the edge is obvious
                    if f < frames and i == head - 1:
                        row += "\033[48;2;255;255;255m" + block + RESET
                    else:
                        row += truecolor(r, g, b, block)
                else:
                    row += "\033[38;2;40;46;54m" + block  # not yet placed
            sys.stdout.write(row + RESET + "\n")
            sys.stdout.flush()
            time.sleep(0.05)
    finally:
        sys.stdout.write(SHOW + CLEAR)
        sys.stdout.flush()


def draw_reveal(rows, langs, frames: int, plain: bool):
    """Reveal the block-letter art left to right, one column per few frames."""
    n = len(langs) or 1
    widest = max((len(r) for r in rows), default=1) or 1

    def paint(cut: int) -> str:
        out = []
        for y, line in enumerate(rows):
            cells = []
            for i, ch in enumerate(line[:cut]):
                if ch == " ":
                    cells.append(" ")
                    continue
                rec = langs[(i + y * 7) % n]
                r, g, b = rec.get("rgb") or hex_to_rgb(rec.get("color", "888888"))
                cells.append(truecolor(r, g, b, ch))
            out.append("".join(cells).rstrip())
        return "\n".join(out)

    if plain or frames <= 0:
        print(paint(widest))
        return

    for f in range(frames + 1):
        cut = int(round(widest * f / frames))
        sys.stdout.write(CLEAR)
        sys.stdout.write(BOLD + "  Hello World!" + RESET + "\n")
        sys.stdout.write(paint(cut) + "\n")
        sys.stdout.flush()
        time.sleep(0.07)


def is_tty() -> bool:
    if os.environ.get("RAINBOW_PLAIN"):
        return False
    return sys.stdout.isatty()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bar", action="store_true")
    ap.add_argument("--hello", action="store_true")
    ap.add_argument("--sweep", type=int, default=12)
    ap.add_argument("--fill-frames", type=int, default=0,
                    help="animate the bar filling in over N frames (--bar)")
    ap.add_argument("--reveal-frames", type=int, default=0,
                    help="reveal the art over N frames (--hello)")
    ap.add_argument("--sweep-only", action="store_true",
                    help="run just the hue sweep, then stop (section divider)")
    ap.add_argument("--width", type=int, default=0)
    ap.add_argument("--plain", action="store_true")
    ap.add_argument("--no-animation", action="store_true")
    ap.add_argument("--scale", type=int, default=2)
    ap.add_argument("--mode", choices=["blocks", "braille", "ascii"], default="blocks")
    args = ap.parse_args()

    langs = load_bar()
    width = args.width or min(shutil.get_terminal_size((100, 24)).columns, 160)
    # Colour survives redirection on purpose: logs/run.log, CI logs and the
    # piped demo all need the true-colour bar. Opt out with --plain or
    # RAINBOW_PLAIN=1. Only cursor tricks stay gated on a real terminal.
    plain = args.plain or os.environ.get("RAINBOW_PLAIN", "0").strip().lower() in (
        "1", "true", "yes",
    )
    tty = is_tty()
    both = not (args.bar or args.hello)

    if plain:
        print(f"rainbow languages in the bar: {len(langs)}")
        print(f"target share per language  : {100.0 / max(1, len(langs)):.4f} %")
        print("Hello World!")
        return 0

    # ---- animated modes -------------------------------------------------
    # run.sh calls this script with --bar and --hello, which sets both=False and
    # therefore skipped every animation the recorded demo relied on: the GIF was
    # a still terminal. These two modes restore real motion.
    animate = not args.no_animation and tty

    # --sweep-only means "draw the sweep and nothing else". It must NOT depend on
    # `both`, which is only true when --bar and --hello were both passed, and it
    # must not be gated behind a later early-return that skips the drawing.
    #
    # Both mistakes were live at once: run.sh calls
    #   rainbow.py --sweep N --sweep-only --width W
    # which sets both=False, so the sweep was skipped, and the --sweep-only branch
    # then returned 0 before drawing anything. The command exited 0 having
    # printed zero bytes, so the "animated hold" at the end of the show produced
    # no output whatsoever. Measured motion coverage found it: the final 8.7 s of
    # a 37.4 s recording was completely frozen.
    if args.sweep_only and args.sweep and animate:
        sys.stdout.write(HIDE)
        try:
            for i in range(args.sweep):
                sys.stdout.write(CLEAR)
                for row in sweep(i, args.sweep, width):
                    sys.stdout.write(row + "\n")
                sys.stdout.flush()
                time.sleep(0.045)
        finally:
            sys.stdout.write(SHOW + CLEAR)
            sys.stdout.flush()
        return 0

    if args.sweep_only and args.sweep and not animate:
        # No TTY (or --no-animation): emit a single static sweep so the phase
        # still contributes visible content instead of vanishing silently.
        for row in sweep(0, args.sweep, width):
            sys.stdout.write(row + "\n")
        sys.stdout.flush()
        return 0

    if args.fill_frames and args.bar and animate:
        draw_fill(langs, width, args.fill_frames, plain)
        return 0

    if args.sweep and not args.no_animation and both and tty:
        sys.stdout.write(HIDE)
        try:
            for i in range(args.sweep):
                sys.stdout.write(CLEAR)
                for row in sweep(i, args.sweep, width):
                    sys.stdout.write(row + "\n")
                sys.stdout.flush()
                time.sleep(0.045)
        finally:
            sys.stdout.write(SHOW + CLEAR)
            sys.stdout.flush()

    # A bare hue sweep, used by run.sh as a divider between sections so the
    # recording keeps moving instead of holding on a static prompt.
    if both or args.bar:
        print(BOLD + "  RAiNBOW_Hello-World language bar "
              + RESET + DIM
              + f"({len(langs)} languages, {100.0 / max(1, len(langs)):.4f}% each)"
              + RESET)
        for row in render_bar(width, langs, plain):
            print(row)
        for row in render_colour_labels(langs):
            print(row)
        print()

    if both or args.hello:
        print(BOLD + "  Hello World!" + RESET)
        rows = ascii_art(args.scale)
        if args.reveal_frames and animate:
            draw_reveal(rows, langs, args.reveal_frames, plain)
            return 0
        n = len(langs) or 1
        for y, line in enumerate(rows):
            out = []
            for i, ch in enumerate(line):
                if ch == " ":
                    out.append(" ")
                    continue
                rec = langs[(i + y * 7) % n]
                r, g, b = rec.get("rgb") or hex_to_rgb(rec.get("color", "888888"))
                out.append(truecolor(r, g, b, ch))
            print("".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
