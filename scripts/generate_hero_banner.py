#!/usr/bin/env python3
"""Generate the README hero banner.

    python scripts/generate_hero_banner.py
    python scripts/generate_hero_banner.py --width 1600

Writes assets/hero-banner.png: a horizontal hue sweep with the project name in
outline, plus live counts read from the repository itself rather than hard-coded,
so the banner cannot drift away from the facts it advertises.

Pure Pillow, no external fonts beyond the ones shipped with matplotlib, and it
degrades to a plain gradient if no usable font is found.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "hero-banner.png"
CORE_LIST = ROOT / "config" / "core-langs.txt"
MANIFEST = ROOT / "hello" / "manifest.json"
BAR_CFG = ROOT / "config" / "rainbow_langs.json"

LOG = logging.getLogger("hero")


def facts() -> dict[str, int]:
    out = {"core": 0, "full": 0, "files": 0, "segments": 0}
    if MANIFEST.is_file():
        import json
        m = json.loads(MANIFEST.read_text(encoding="utf-8"))
        out["core"] = int(m.get("core_languages", 0))
        out["full"] = int(m.get("full_languages", 0))
        out["files"] = int(m.get("total_files", 0))
    if CORE_LIST.is_file():
        out["core"] = out["core"] or sum(
            1 for l in CORE_LIST.read_text(encoding="utf-8").splitlines() if l.strip()
        )
    if BAR_CFG.is_file():
        import json
        cfg = json.loads(BAR_CFG.read_text(encoding="utf-8"))
        out["segments"] = int(cfg.get("core_count", 0))

    # GitHub's own breakdown is the ground truth for how many segments are
    # actually drawn; logs/linguist_audit.json is produced by CI from
    # github-linguist itself. Prefer it, fall back to the config figure.
    audit = ROOT / "logs" / "linguist_audit.json"
    if audit.is_file():
        import json
        try:
            a = json.loads(audit.read_text(encoding="utf-8"))
            if a.get("aggregate_language_count"):
                out["segments"] = int(a["aggregate_language_count"])
        except Exception:
            pass
    return out


def font(size: int):
    from matplotlib import font_manager
    for name in ("DejaVu Sans", "DejaVu Sans Bold", "Arial", "Helvetica"):
        try:
            path = font_manager.findfont(name, fallback_to_default=False)
        except Exception:
            continue
        from PIL import ImageFont
        return ImageFont.truetype(path, size)
    from PIL import ImageFont
    return ImageFont.load_default()


def hsl_to_rgb(h: float, s: float, l: float):
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

    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q
    return (int(hue(p, q, h + 1 / 3) * 255),
            int(hue(p, q, h) * 255),
            int(hue(p, q, h - 1 / 3) * 255))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--width", type=int, default=1600)
    ap.add_argument("--height", type=int, default=420)
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s",
                        stream=sys.stdout)

    try:
        from PIL import Image, ImageDraw, ImageFilter
    except ImportError:
        LOG.error("Pillow is required (pip install pillow)")
        return 1

    w, h = args.width, args.height
    img = Image.new("RGB", (w, h), (13, 17, 23))
    px = img.load()

    # horizontal hue sweep with a gentle vertical shading
    for x in range(w):
        base = (x / w) * 360.0
        for y in range(h):
            shade = 0.62 - 0.22 * (y / h)
            px[x, y] = hsl_to_rgb(base, 0.78, max(0.10, shade))

    # soften the bands so it reads as a gradient rather than a spectrum chart
    img = img.filter(ImageFilter.GaussianBlur(radius=9))

    draw = ImageDraw.Draw(img)
    f_title = font(int(h * 0.19))
    f_sub = font(int(h * 0.058))

    f = facts()
    title = "RAiNBOW_Hello-World"
    bbox = draw.textbbox((0, 0), title, font=f_title)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx, ty = (w - tw) // 2, int(h * 0.24)

    # dark plate + outlined text keeps the name legible over any hue
    draw.rectangle([tx - 26, ty - 16, tx + tw + 26, ty + th + 16],
                   fill=(10, 12, 18))
    draw.text((tx - 1, ty - 1), title, font=f_title, fill=(0, 0, 0))
    draw.text((tx, ty), title, font=f_title, fill=(255, 255, 255))

    # Two centred lines: one line overflowed the canvas at 1600 px.
    # "segments" is what GitHub actually draws (631), not the 694 core files --
    # conflating the two is exactly the confusion the README exists to correct.
    lines = [
        f"Hello World in {f['files']:,} files   \u00b7   {f['core']} languages on the bar",
        f"{f['segments']} colour segments GitHub renders   \u00b7   "
        f"{f['full']:,} full-layer languages   \u00b7   one rainbow",
    ]
    for i, sub in enumerate(lines):
        sb = draw.textbbox((0, 0), sub, font=f_sub)
        draw.text(((w - (sb[2] - sb[0])) // 2, ty + th + 30 + i * int(h * 0.075)),
                  sub, font=f_sub, fill=(236, 242, 248))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    LOG.info("wrote %s (%d bytes, %dx%d) with facts %s", out, out.stat().st_size, w, h, f)
    return 0


if __name__ == "__main__":
    sys.exit(main())