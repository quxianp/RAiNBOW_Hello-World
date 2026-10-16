#!/usr/bin/env python3
"""The bar must actually read as a rainbow.

`hello/core/` is ordered by hue so the language bar is a spectrum rather than
noise. That is a claim about a distribution, and it is the sort of claim that
decays quietly: nothing about adding a language makes the ordering worse, and
nothing would notice if it did.

Measured today over the 655 chromatic entries:

    ideal gap for 655 languages   0.55 deg
    mean gap                      0.55 deg
    largest gap                  9.93 deg   (NCL -> POV-Ray SDL)

The largest gap is allowed to be generous -- Linguist assigns colours by hand, so
clusters are real and nine degrees is a visible but not broken seam. What is not
allowed is a gap wide enough that the bar reads as two rainbows, or a mean that
has drifted away from the ideal by more than a factor of two.
"""

import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "hello" / "manifest.json"
TOOL = ROOT / "scripts" / "hue_uniformity.py"

MAX_WORST_GAP_DEG = 20.0
MAX_MEAN_RATIO = 2.0


def _module():
    spec = importlib.util.spec_from_file_location("hue_uniformity", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_hue_ordering_is_still_a_rainbow():
    mod = _module()
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    core = [f for f in man["files"] if f["path"].startswith("hello/core/")]

    chromatic = []
    for f in core:
        hsv = mod.parse_colour(f.get("color") or f.get("colour"))
        if hsv is not None and not mod.is_grey(hsv):
            chromatic.append(hsv[0] * 360)

    assert len(chromatic) > 600, (
        f"only {len(chromatic)} of {len(core)} core languages have a chromatic "
        f"colour; the rainbow claim cannot be evaluated")

    chromatic.sort()
    gaps = [(chromatic[(i + 1) % len(chromatic)] - chromatic[i]) % 360
            for i in range(len(chromatic))]
    mean = sum(gaps) / len(gaps)
    worst = max(gaps)
    ideal = 360.0 / len(chromatic)

    assert worst <= MAX_WORST_GAP_DEG, (
        f"the largest hue gap is {worst:.1f} deg (limit {MAX_WORST_GAP_DEG}). "
        f"The bar will read as separate bands rather than one spectrum.")
    assert mean <= ideal * MAX_MEAN_RATIO, (
        f"mean hue gap is {mean:.2f} deg against an ideal of {ideal:.2f}; the "
        f"distribution has drifted")


def test_every_core_language_has_a_colour():
    """The modelines do the detecting; the colour does the reading.

    A core entry with no colour still gets a segment, so this would not be caught
    by any bar check -- the segment would just be invisible against the page.
    """
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    core = [f for f in man["files"] if f["path"].startswith("hello/core/")]
    mod = _module()
    uncoloured = [f["language"] for f in core
                  if mod.parse_colour(f.get("color") or f.get("colour")) is None]
    assert not uncoloured, (
        f"{len(uncoloured)} core language(s) have no parseable colour: "
        f"{uncoloured[:5]}")
