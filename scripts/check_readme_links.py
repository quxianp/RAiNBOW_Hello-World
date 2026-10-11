#!/usr/bin/env python3
"""Check that every link and image in README.md resolves.

    python scripts/check_readme_links.py
    python scripts/check_readme_links.py --check

Two classes of problem, both of which have actually happened here:

  * a local path that does not exist -- an asset renamed or deleted while the
    README kept pointing at it, which on GitHub renders as a broken image;
  * an in-page anchor (``#section``) with no matching heading, which silently
    scrolls nowhere.

External https links are listed but not fetched, because a network call in the
acceptance job makes the gate flaky for no gain: the repository's own links are
the ones that rot.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"

LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$", re.MULTILINE)


def slugify(heading: str) -> str:
    """Approximate GitHub's anchor generation.

    Emoji are stripped, so "## <clapper> The show" becomes "-the-show" -- the
    space that followed the emoji survives as a leading hyphen. Callers compare
    with surrounding hyphens ignored, because the exact behaviour has changed
    between GitHub renderers and a false "missing anchor" is worse than a
    permissive match.
    """
    s = heading.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"\s+", "-", s.strip())
    return s


def same_anchor(a: str, b: str) -> bool:
    """Compare two anchors after normalising both sides identically.

    Both sides must go through the same reduction, or the comparison is
    meaningless: percent-encoded emoji survive on the link side but are already
    stripped from the heading side, and a leading ``U+FE0F`` variation selector
    is a decoration, not a word. Reducing only one side made the checker report
    eight phantom failures and hide the two real ones.
    """
    def norm(x: str) -> str:
        x = x.strip().lower().replace("_", "-")
        x = re.sub(r"[^\w\s-]", "", x, flags=re.UNICODE)
        x = re.sub(r"[\s-]+", "-", x)
        return x.strip("-")

    return norm(a) == norm(b)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="unused; kept for symmetry")
    args = ap.parse_args()

    if not README.is_file():
        print(f"error: {README} missing", file=sys.stderr)
        return 1
    text = README.read_text(encoding="utf-8")

    anchors = {slugify(h) for _, h in HEADING_RE.findall(text)}
    missing_files: list[str] = []
    missing_anchors: list[str] = []
    external: list[str] = []
    checked = 0

    for raw in LINK_RE.findall(text):
        target = raw.strip()
        if not target:
            continue
        checked += 1
        if target.startswith(("http://", "https://", "mailto:")):
            external.append(target)
            continue
        path, _, frag = target.partition("#")
        if path:
            if not (ROOT / path).exists():
                missing_files.append(target)
        if frag:
            # TOC entries percent-encode the emoji: #%EF%B8%8F-running-it
            from urllib.parse import unquote
            frag = unquote(frag)
            if not any(same_anchor(frag, a) for a in anchors):
                missing_anchors.append(target)

    print(f"checked {checked} links in {README.name}")
    print(f"  external (not fetched) : {len(external)}")
    print(f"  missing files         : {len(missing_files)}")
    print(f"  missing anchors       : {len(missing_anchors)}")

    for m in missing_files:
        print(f"  MISSING FILE   {m}")
    for m in missing_anchors:
        print(f"  MISSING ANCHOR {m}")

    # A missing asset is a broken image on the page; a missing anchor is only a
    # dead link. Both are worth failing on, but say which is which.
    return 1 if (missing_files or missing_anchors) else 0


if __name__ == "__main__":
    sys.exit(main())