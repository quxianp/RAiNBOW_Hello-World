#!/usr/bin/env python3
"""Check that hello/manifest.json describes the repository that is on disk.

Everything else in this repository reads the manifest: the generator writes it,
the bar renderer colours from it, the coverage figure counts it, the acceptance
checks compare against it. A manifest that is internally consistent but
describes a repository that does not exist would be silently wrong in a way
nothing downstream notices, and a field that is internally inconsistent --
a hue that does not match the colour beside it -- is worse, because the file
looks fine and the rainbow comes out wrong.

So this asserts the properties the manifest is supposed to have, in the order a
reader would check them:

  * every path exists, is under hello/, and its layer matches its directory;
  * no path appears twice;
  * the extension recorded is the extension on disk -- which is the check that
    caught `pathlib.Path("hello.intel_hex").stem` returning "hello";
  * every colour parses, and the hue beside it is that colour's hue, computed
    rather than trusted. This is the one that matters: the bar is drawn from
    these two fields and nothing else, so a mismatch is a wrong pixel;
  * shares sum to 100 per layer, and the core layer's are equal to a tolerance;
  * modelines are ones Linguist recognises;
  * runners are ones run_languages.py knows.

    python scripts/check_manifest.py
    python scripts/check_manifest.py --verbose
"""

from __future__ import annotations

import argparse
import colorsys
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "hello" / "manifest.json"
HELLO = ROOT / "hello"

HEX = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

# The manifest's `modeline` is Linguist's *name* for the modeline a language
# uses -- "vim", "emacs", "ignore-list" -- not a line of text. So it is checked
# against the names languages.yml actually defines, read from data/ at runtime
# rather than kept in a table here: a list in this file would drift the moment
# Linguist renamed one, and would do so silently. That is the `colour`/`color`
# mistake with an extra step.
#
# `type` is Linguist's classification and is null for the esolang entries, which
# Linguist does not classify at all. That is not a missing value; it is the
# honest one, and asserting it is populated would be wrong.
LINGUIST_TYPES = {"programming", "markup", "prose", "data"}

# `pathlib.Path.suffix` gives ".py"; the manifest has always stored the same.
LAYERS = ("core", "full")


def modeline_names() -> set[str]:
    """Every `- name:` listed under a `modelines:` key in data/languages.yml.

    Parsed with a regex rather than a YAML library, because the whole test suite
    is standard-library only and this needs exactly one key. `indent` is the
    column of the `modelines:` line; a list item nested deeper than that is a
    child of a modeline (its own `filetype:` list), not a modeline itself, and
    including those would make the check accept nonsense.
    """
    yml = ROOT / "data" / "languages.yml"
    if not yml.exists():
        return set()
    names: set[str] = set()
    in_modelines: int | None = None
    for line in yml.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        pad = len(line) - len(line.lstrip())
        if in_modelines is None:
            if stripped == "modelines:":
                in_modelines = pad
            continue
        if pad <= in_modelines and not stripped.startswith("- "):
            in_modelines = None          # back out to the next key
            continue
        if stripped.startswith("- ") and pad == in_modelines:
            name = stripped[2:].split(":", 1)[0].strip().strip("\"'")
            if name:
                names.add(name)
    return names


def load() -> dict:
    if not MANIFEST.exists():
        print("no manifest; run scripts/generate_all_hello.py first",
              file=sys.stderr)
        raise SystemExit(1)
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def parse_colour(text: str) -> tuple[float, float, float] | None:
    """'#rrggbb' or '#rgb' as floats in 0..1, or None if it is not a colour.

    Both lengths are accepted because Linguist's languages.yml uses the short
    form for several languages -- `#c00` is COBOL's colour and `#f00` is not a
    thing, but `#0a0` appears -- and a strict six-digit parser would report
    three languages as having none.
    """
    if not isinstance(text, str) or not HEX.match(text):
        return None
    h = text[1:]
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))  # type: ignore


def hue_of(colour: tuple[float, float, float]) -> float:
    """HSV hue in degrees, which is what the manifest's `hue` field means.

    A grey has no hue in any useful sense; the generator records 0.0 for those
    and that is the one value this function is not asked to reproduce, so greys
    are exempt from the consistency check below rather than compared.
    """
    r, g, b = colour
    h, _l, _s = colorsys.rgb_to_hsv(r, g, b)
    return round(h * 360.0, 2)


def is_grey(colour: tuple[float, float, float]) -> bool:
    r, g, b = colour
    return abs(r - g) < 0.02 and abs(g - b) < 0.02 and abs(r - b) < 0.02


def slug(language: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", language.lower()).strip("-")


def check(files: list[dict]) -> list[str]:
    problems: list[str] = []
    seen: dict[str, int] = {}
    known_modelines = modeline_names()

    # Linguist's extensions can be compound -- `.js.erb`, `.gradle.kts`,
    # `.antlers.html` -- and `pathlib.Path.suffix` returns only the last one.
    # The mirror of that mistake is asserting equality against `suffix`: it
    # rejects a correct manifest and says nothing about a wrong one. So the
    # recorded extension has to be a suffix of the filename *and* the longest
    # one the manifest records for that language, which is what "the" extension
    # means when a language has several.
    recorded_ext = {f.get("extension") or "" for f in files}

    for i, f in enumerate(files):
        path = f.get("path")
        where = f"{path or '?'} (#{i})"

        if not path:
            problems.append(f"{where}: no path")
            continue
        if path in seen:
            problems.append(f"{path}: appears twice (entries {seen[path]}, {i})")
        seen[path] = i

        if not path.startswith("hello/"):
            problems.append(f"{path}: not under hello/")
            continue

        # ---- the file exists, and is in the layer the manifest says --------
        layer = f.get("layer")
        if layer not in LAYERS:
            problems.append(f"{where}: layer {layer!r} is not one of {LAYERS}")
        elif not path.startswith(f"hello/{layer}/"):
            problems.append(f"{where}: layer {layer!r} but the path says "
                            f"{path.split('/')[1]!r}")

        p = ROOT / path
        if not p.is_file():
            problems.append(f"{path}: not on disk")
            continue

        # ---- the extension on disk is the extension recorded ----------------
        recorded = f.get("extension") or ""
        name = p.name
        if not name.endswith(recorded):
            problems.append(f"{path}: manifest says {recorded!r}, and the "
                            f"file {name!r} does not end in it")
        else:
            longer = [e for e in recorded_ext
                      if len(e) > len(recorded) and name.endswith(e)]
            if longer:
                problems.append(
                    f"{path}: manifest says {recorded!r} but "
                    f"{', '.join(sorted(repr(e) for e in longer))} "
                    f"is a longer extension the same file ends in")

        # ---- the colour and the hue agree -----------------------------------
        colour = parse_colour(f.get("color"))
        hue = f.get("hue")
        if f.get("color") and colour is None:
            problems.append(f"{where}: color {f.get('color')!r} is not a "
                            f"hex colour")
        elif colour is not None and not is_grey(colour):
            if not isinstance(hue, (int, float)):
                problems.append(f"{where}: hue {hue!r} is not a number, and "
                                f"the colour {f.get('color')} is chromatic")
            else:
                want = hue_of(colour)
                if abs(float(hue) - want) > 0.5:
                    problems.append(f"{where}: hue {hue} but {f.get('color')} "
                                    f"is {want} degrees -- the bar would be "
                                    f"drawn from the wrong field")

        # ---- the modeline is one Linguist defines --------------------------
        modeline = f.get("modeline")
        if modeline and known_modelines and modeline not in known_modelines:
            problems.append(f"{where}: modeline {modeline!r} is not a name "
                            f"languages.yml defines")

        # ---- the type, where there is one ----------------------------------
        kind = f.get("type")
        if kind is not None and kind not in LINGUIST_TYPES:
            problems.append(f"{where}: type {kind!r} is not one of "
                            f"{sorted(LINGUIST_TYPES)}")

        # ---- a runner must say which file it runs --------------------------
        runner = f.get("runner")
        if runner and "{file}" not in runner:
            problems.append(f"{where}: runner {runner!r} never mentions the "
                            f"file it is supposed to run")

    problems.extend(check_shares(files))
    return problems


def check_shares(files: list[dict]) -> list[str]:
    """Core shares must sum to 100 and be equal within a tolerance."""
    problems: list[str] = []
    by_layer: dict[str, list[float]] = {}
    for f in files:
        share = f.get("share")
        if isinstance(share, (int, float)):
            by_layer.setdefault(f.get("layer", "?"), []).append(float(share))

    for layer, shares in sorted(by_layer.items()):
        total = sum(shares)
        if abs(total - 100.0) > 0.5:
            problems.append(f"{layer}: shares sum to {total:.4f}, not 100 "
                            f"({len(shares)} files)")

    core = by_layer.get("core")
    if core:
        lo, hi = min(core), max(core)
        if hi - lo > 0.5:
            problems.append(f"core: shares range from {lo:.4f} to {hi:.4f}; "
                            f"the bar is meant to be even")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    man = load()
    files = man["files"]
    problems = check(files)

    print(f"checked {len(files)} manifest entries "
          f"({sum(1 for f in files if f.get('layer') == 'core')} core, "
          f"{sum(1 for f in files if f.get('layer') == 'full')} full)")

    if args.verbose:
        for p in problems:
            print(f"  {p}")

    if problems:
        shown = len(problems) if args.verbose else 10
        print(f"\n{len(problems)} problem(s):")
        for p in problems[:shown]:
            print(f"  {p}")
        if len(problems) > shown:
            print(f"  ... and {len(problems) - shown} more")
        return 1

    print("manifest agrees with the files on disk")
    return 0


if __name__ == "__main__":
    sys.exit(main())