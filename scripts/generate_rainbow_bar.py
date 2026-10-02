#!/usr/bin/env python3
"""Render the project colour wheel as local bar artwork.

Reads config/rainbow_langs.json (every Linguist language with a colour,
sorted by hue) and writes:

  assets/rainbow-bar-local.png   a 2400x120 horizontal gradient bar
  assets/rainbow-bar-local.svg   the same bar as vector art
  assets/rainbow-wheel.png       a small circle filled with language colours

Only pillow is required; everything degrades to SVG if it is absent.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config"
ASSETS = ROOT / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)


def load():
    data = json.loads((CONFIG / "rainbow_langs.json").read_text(encoding="utf-8"))
    return data.get("languages", [])


def hex_to_rgb(value: str):
    v = (value or "").lstrip("#")
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    try:
        return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:
        return (128, 128, 128)


def render_png(langs, path: Path, width=2400, height=160) -> bool:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        print("pillow missing; skipping PNG")
        return False

    img = Image.new("RGB", (width, height), (13, 17, 23))
    draw = ImageDraw.Draw(img)
    if not langs:
        img.save(path)
        return True

    per = max(1, width // len(langs))
    x = 0
    for rec in langs:
        rgb = rec.get("rgb") or hex_to_rgb(rec.get("color", "888888"))
        w = per if x + per * 2 < width else width - x
        draw.rectangle([x, 0, x + w, height - 40], fill=tuple(rgb))
        x += w
        if x >= width:
            break

    # label strip with the 12 named hue buckets
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 14)
    except Exception:
        font = ImageFont.load_default()
    bands = [
        (0, "red"), (60, "yellow"), (120, "green"), (180, "cyan"),
        (240, "blue"), (300, "magenta"),
    ]
    draw.rectangle([0, height - 40, width, height], fill=(13, 17, 23))
    for edge, label in bands:
        x = int(edge / 360 * width)
        draw.text((x + 4, height - 30), label, fill=(220, 220, 220), font=font)
    img.save(path)
    print(f"wrote {path.relative_to(ROOT)} ({path.stat().st_size} B)")
    return True


def render_svg(langs, path: Path, width=2400, height=160) -> None:
    if not langs:
        langs = [{"color": "808080"}]
    per = width / max(1, len(langs))
    rects = []
    for i, rec in enumerate(langs):
        rgb = rec.get("rgb") or hex_to_rgb(rec.get("color", "888888"))
        hexv = "#%02x%02x%02x" % tuple(rgb)
        x = i * per
        rects.append(f'    <rect x="{x:.2f}" y="0" width="{per + 0.5:.2f}" '
                     f'height="{height - 40}" fill="{hexv}"/>')
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
        f'  <rect width="{width}" height="{height}" fill="#0d1117"/>\n'
        + "\n".join(rects)
        + f'\n  <rect x="0" y="{height - 40}" width="{width}" height="40" fill="#0d1117"/>\n'
        f'</svg>\n'
    )
    path.write_text(svg, encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)} ({path.stat().st_size} B)")


def render_wheel(langs, path: Path, size=1200) -> bool:
    try:
        from PIL import Image, ImageDraw
    except Exception:
        return False
    img = Image.new("RGB", (size, size), (13, 17, 23))
    draw = ImageDraw.Draw(img)
    if not langs:
        img.save(path)
        return True
    cx = cy = size / 2
    radius = size * 0.45
    rings = 5
    for ring in range(rings):
        inner = rings - ring - 1
        count = max(12, (ring + 1) * 24)
        for i in range(count):
            start = i / count * 360
            end = (i + 1) / count * 360 + 1.5
            rec = langs[(i + ring * 7) % len(langs)]
            rgb = rec.get("rgb") or hex_to_rgb(rec.get("color", "888888"))
            draw.pieslice(
                [cx - radius * (ring + 1) / rings, cy - radius * (ring + 1) / rings,
                 cx + radius * (ring + 1) / rings, cy + radius * (ring + 1) / rings],
                start=start, end=end, fill=tuple(rgb),
            )
    draw.ellipse([cx - radius / rings / 2, cy - radius / rings / 2,
                  cx + radius / rings / 2, cy + radius / rings / 2], fill=(13, 17, 23))
    img.save(path)
    print(f"wrote {path.relative_to(ROOT)} ({path.stat().st_size} B)")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--width", type=int, default=2400)
    ap.add_argument("--height", type=int, default=160)
    args = ap.parse_args()

    langs = load()
    render_svg(langs, ASSETS / "rainbow-bar-local.svg", args.width, args.height)
    render_png(langs, ASSETS / "rainbow-bar-local.png", args.width, args.height)
    render_wheel(langs, ASSETS / "rainbow-wheel.png", 1200)
    print(f"segments: {len(langs)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
