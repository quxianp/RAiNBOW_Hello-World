#!/usr/bin/env python3
"""Check that every file's banner says what the manifest says about it.

Each of the 7,326 files opens with a banner: the language name, the colour
Linguist assigned, the hue that colour's HSV hue is, the layer, and an admission
line for the files that have no program. Six fields, in every file, and nothing
checked any of them.

That is the same situation `hello/manifest.json` was in, and it found four
languages carrying a `runner` that never ran them (E34). A banner that says
`colour : #ff0000` beside a manifest entry that says `#00ff00` is not a cosmetic
problem: the banner is what a reader sees when they open the file, and it is the
thing a screenshot of this repository shows.

So this reads every banner and checks it against the manifest and against the
generator:

  * the banner names the language the manifest names;
  * the colour matches, or both say there is none;
  * the hue matches the hue computed from the colour, to 0.1 degree;
  * the layer matches, and the full-layer suffix says why it is not counted;
  * an admission line exists exactly when the file has no program -- no
    admission on a file with a program, and none missing from a file without
    one;
  * the padding marker, where there is padding, is the generator's own;
  * the file ends with a newline.

    python scripts/check_banners.py
    python scripts/check_banners.py --verbose
    python scripts/check_banners.py --language Python
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "hello" / "manifest.json"
CLASSES = ROOT / "data" / "placeholder_classes.json"
BANNER_LINES = 10

# Eleven comment syntaxes are in play -- `#`, `;`, `//`, `%`, `!`, `--`, `*`,
# `REM`, and `/* */` for the block-comment languages. Every pattern below allows
# a marker prefix rather than requiring `#`, because six of those eleven put
# the banner inside a block comment where there is no `#` to anchor to. A
# checker that only understood `#` reported 25,880 problems in a repository
# whose banners are correct.
MARK = r"(?:#|;|//|%|!|--|\*|REM)?\s*"

# `not assigned by Linguist` is three words. `\S+` captured only `not`, which
# made 6,000-odd files whose banner correctly says Linguist has no colour for
# them look like banners claiming a colour called "not". And the `$` needs
# re.M: these patterns are searched against ten lines joined with newlines,
# where `$` without re.M means end-of-string and never matches a line ending.
RE_COLOUR = re.compile(MARK + r"colou?r\s*:\s*(.+?)\s*$", re.M)
RE_HUE = re.compile(MARK + r"hue\s*:\s*([\d.]+)\s*deg")
RE_LAYER = re.compile(MARK + r"layer\s*:\s*(core|full)\b")
RE_ADMISSION = re.compile(MARK + r"admission\s*:\s*(.+)")
RE_TITLE = re.compile(r"^\s*" + MARK + r"(?P<name>.+?)\s+-\s+Hello World!\s+::")
# Three languages use `[` as their comment marker -- INI, gettext catalogues and
# Public Key blocks -- and the generator emits their title as `[Name] Hello
# World!` with no ` - ` separator, because the bracket already carries it.
RE_TITLE_BRACKET = re.compile(r"^\s*(?P<name>.+?)\]\s+Hello World!\s+::")
# Two padding markers exist and only one of them names a language. The other
# (`rainbow-pad equal byte share keeps the language bar an even rainbow`) is
# generic and every core file has it, so matching on the word alone reports
# every core file as having the wrong language in its padding.
RE_PAD_LANG = re.compile(MARK + r"rainbow-pad\s+(?P<lang>.+?)\s+::")

NOT_COLOURED = "not assigned by linguist"


def load() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "gen_hello", ROOT / "scripts" / "generate_all_hello.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gen_hello"] = mod
    spec.loader.exec_module(mod)
    return mod


def banner_of(path: pathlib.Path, comment: tuple) -> list[str]:
    """The file's leading comment block, read as a fixed window.

    Deliberately not "the block up to the first non-comment line". The modeline
    and the banner need not share a marker: Squirrel's `.nut` files open with
    `# -*- mode: squirrel -*-` and the banner below it with `;`, so a scanner
    that stops at the first line that does not begin with the language's own
    comment marker sees one line and reports four problems for a file that is
    correct. The window is fixed and the patterns do the deciding.
    """
    lines: list[str] = []
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if len(lines) >= BANNER_LINES:
                break
            lines.append(line.rstrip("\n"))
    return lines


def has_program_for(entry: dict, gen, kinds: dict) -> bool:
    """Whether this file should have a program, per the generator and the index.

    Deliberately a function of this module rather than inline in `main`, so
    that a test exercising the checker uses the same rule the checker uses. The
    first version of that test passed `True` unconditionally and reported
    fifty false positives on the document-kind files, which have no program and
    correctly carry an admission line.

    `real and kind is None`, not `real or kind == "..."`: a file that
    classify_placeholders.py has classified is a file with no program, by
    definition.
    """
    _program, real = gen.program_for(entry["language"],
                                     entry.get("extension") or "")
    return bool(real) and kinds.get(entry["path"]) is None


def check(entry: dict, path: pathlib.Path, gen, has_program: bool) -> list[str]:
    rel = entry["path"]
    where = rel
    problems: list[str] = []
    try:
        lines = banner_of(path, gen.COMMENT.get(entry.get("extension") or "", gen.C_NONE))
    except OSError as exc:
        return [f"{where}: cannot read ({exc})"]

    if not lines:
        return [f"{where}: empty"]

    # ---- the title names the language -----------------------------------
    # Not necessarily the first line: when a language has a modeline, the
    # generator writes `# -*- mode: python -*-` above the title, because the
    # modeline has to be the first thing in the file for an editor to read it.
    m = None
    for line in lines:
        m = RE_TITLE.match(line) or RE_TITLE_BRACKET.match(line)
        if m:
            break
    if not m:
        problems.append(f"{where}: no banner title in the first "
                        f"{BANNER_LINES} lines: {lines[0][:60]!r}")
    else:
        # The first characters of a file are part of the language, not the name:
        # Vim comments with `"`, XML/HTML with `<!--`, SQL with `--`. Strip them
        # so " Ant Build System" and "<!-- Ant Build System" both compare equal
        # to the language's actual name.
        said = m.group("name").strip().lstrip('"\'`<![').strip()
        # ...and SQL-style markers are two characters, so `-` and `--` both.
        said = said.lstrip("-").strip()
        if said != entry["language"]:
            problems.append(f"{where}: banner says {said!r}, the "
                            f"manifest says {entry['language']!r}")

    text = "\n".join(lines)

    # ---- the colour and the hue agree with the manifest ------------------
    mc = RE_COLOUR.search(text)
    manifest_colour = (entry.get("color") or "").lower() or None
    if mc:
        said = mc.group(1).lower()
        if manifest_colour and said != manifest_colour:
            problems.append(f"{where}: banner colour {said}, manifest "
                            f"{manifest_colour}")
        elif not manifest_colour and said != NOT_COLOURED:
            problems.append(f"{where}: banner colour {said}, but Linguist "
                            f"assigns none")
    else:
        problems.append(f"{where}: no colour in the banner")

    mh = RE_HUE.search(text)
    manifest_hue = entry.get("hue")
    if manifest_hue is None:
        if mh:
            problems.append(f"{where}: a hue in the banner, but the manifest "
                            f"has none")
    elif mh is None:
        problems.append(f"{where}: no hue in the banner, manifest says "
                        f"{manifest_hue}")
    elif abs(float(mh.group(1)) - float(manifest_hue)) > 0.1:
        problems.append(f"{where}: banner hue {mh.group(1)}, manifest "
                        f"{manifest_hue}")

    # ---- the layer -------------------------------------------------------
    ml = RE_LAYER.search(text)
    if not ml:
        problems.append(f"{where}: no layer in the banner")
    elif ml.group(1) != entry.get("layer"):
        problems.append(f"{where}: banner says {ml.group(1)}, manifest says "
                        f"{entry.get('layer')}")

    # ---- an admission line exactly when there is no program --------------
    ma = RE_ADMISSION.search(text)
    if has_program and ma:
        problems.append(f"{where}: has a program and also an admission line")
    elif not has_program and not ma:
        problems.append(f"{where}: has no program and no admission line")

    # ---- the padding marker names the right language --------------------
    for line in lines:
        mp = RE_PAD_LANG.search(line)
        if mp and mp.group("lang") != entry["language"]:
            problems.append(f"{where}: padding marker names "
                            f"{mp.group('lang')!r}, not {entry['language']!r}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--language", help="check one language only")
    ap.add_argument("--limit", type=int, default=12)
    args = ap.parse_args()

    if not MANIFEST.exists():
        print("no manifest; run scripts/generate_all_hello.py first",
              file=sys.stderr)
        return 1

    gen = load_generator()
    files = load()["files"]

    kinds = {}
    if CLASSES.exists():
        kinds = {f["path"]: f.get("kind")
                 for f in json.loads(CLASSES.read_text(encoding="utf-8"))["files"]}

    problems: list[str] = []
    checked = 0
    for entry in files:
        if args.language and entry["language"].lower() != args.language.lower():
            continue
        path = ROOT / entry["path"]
        if not path.is_file():
            continue
        # "has a program" is the generator's own answer, not the banner's: the
        # whole point is to catch a banner that disagrees with it.
        has_program = has_program_for(entry, gen, kinds)
        problems.extend(check(entry, path, gen, has_program))
        checked += 1

    print(f"checked {checked} banner(s)")
    if args.verbose:
        for p in problems:
            print(f"  {p}")

    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in problems[:args.limit]:
            print(f"  {p}")
        if len(problems) > args.limit:
            print(f"  ... and {len(problems) - args.limit} more "
                  f"(use --verbose)")
        return 1

    print("every banner agrees with the manifest and the generator")
    return 0


if __name__ == "__main__":
    sys.exit(main())