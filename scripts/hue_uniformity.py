#!/usr/bin/env python3
"""Is the bar actually a rainbow?

The claim this repository makes is that `hello/core/` is ordered by hue, so that
the language bar reads as a spectrum rather than as noise. That is a claim about
a distribution, and distributions are measurable: order the 694 core languages by
their Linguist colour's hue and the gaps between consecutive hues should be small
and even.

They will not be perfectly even. Linguist assigns colours by hand and several are
grey or near-grey, which have no meaningful hue at all. So the question is not
"is every gap identical" but "how bad is the worst one, and are the near-grey
entries the ones causing it".

That is answerable, and the answer is worth having in the repository rather than
in a conversation.

    python scripts/hue_uniformity.py
    python scripts/hue_uniformity.py --verbose
"""

from __future__ import annotations

import argparse
import colorsys
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "hello" / "manifest.json"


def parse_colour(value: str | None):
    """'#ffdab3' -> (h, s, v) in 0..1, or None for greys and for junk."""
    if not value:
        return None
    v = value.strip().lstrip("#")
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    if len(v) != 6:
        return None
    try:
        r, g, b = (int(v[i:i + 2], 16) / 255 for i in (0, 2, 4))
    except ValueError:
        return None
    h, s, val = colorsys.rgb_to_hsv(r, g, b)
    return h, s, val


def is_grey(hsv) -> bool:
    """A colour with no meaningful hue: saturation near zero."""
    return hsv[1] < 0.15


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    core = [f for f in man["files"] if f["path"].startswith("hello/core/")]

    chromatic, achromatic, missing = [], [], []
    for f in core:
        # The manifest spells it `color`, not `colour`. The first version of this
        # read `colour`, found nothing, and reported "0 chromatic of 694" with a
        # perfectly straight face -- which is exactly the failure mode that made
        # the demo gate necessary in the first place.
        raw = f.get("color") or f.get("colour")
        colour = (raw or "").strip() or None
        hsv = parse_colour(colour)
        if hsv is None:
            missing.append((f["language"], colour))
        elif is_grey(hsv):
            achromatic.append((f["language"], colour, round(hsv[0] * 360, 1)))
        else:
            chromatic.append((f["language"], colour, hsv[0] * 360))

    chromatic.sort(key=lambda r: r[2])
    gaps = []
    for i in range(len(chromatic)):
        a = chromatic[i][2]
        b = chromatic[(i + 1) % len(chromatic)][2]
        d = (b - a) % 360
        gaps.append((d, chromatic[i][0], chromatic[(i + 1) % len(chromatic)][0]))

    gaps.sort(reverse=True)
    ideal = 360.0 / max(1, len(chromatic))
    mean = sum(g[0] for g in gaps) / len(gaps) if gaps else 0.0
    worst = gaps[0] if gaps else (0.0, "", "")

    report = {
        "core": len(core),
        "chromatic": len(chromatic),
        "achromatic": len(achromatic),
        "no_colour": len(missing),
        "ideal_gap_deg": round(ideal, 2),
        "mean_gap_deg": round(mean, 2),
        "max_gap_deg": round(worst[0], 2),
        "max_gap_between": [worst[1], worst[2]],
        "top_gaps": [
            {"deg": round(d, 1), "between": [a, b]} for d, a, b in gaps[:8]
        ],
    }

    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    print(f"core languages            : {report['core']}")
    print(f"  with a chromatic colour : {report['chromatic']}")
    print(f"  grey or near-grey       : {report['achromatic']}")
    print(f"  no colour at all        : {report['no_colour']}")
    print()
    print(f"hue gap, ideal for {report['chromatic']} languages : "
          f"{ideal:.2f} deg")
    print(f"mean gap                          : {mean:.2f} deg")
    print(f"largest gap                       : {worst[0]:.2f} deg  "
          f"({worst[1]} -> {worst[2]})")
    print()
    print("largest gaps:")
    for d, a, b in gaps[:8]:
        print(f"  {d:6.1f} deg   {a} -> {b}")

    if args.verbose and achromatic:
        print()
        print("achromatic entries, which have no meaningful hue:")
        for lang, colour, hue in achromatic[:40]:
            print(f"  {hue:6.1f} deg  {colour:<9} {lang}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
