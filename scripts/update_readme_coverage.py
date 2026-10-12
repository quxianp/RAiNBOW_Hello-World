#!/usr/bin/env python3
"""Rewrite the coverage figure in README.md from the manifest.

    python scripts/update_readme_coverage.py
    python scripts/update_readme_coverage.py --check

The percentage of core files carrying a real Hello World has moved nine times
this week, and each time the README needed editing by hand -- which is how it was
stale on three separate occasions.

Doing it by hand also cost a corrupted README. A one-character change made with
PowerShell's `Set-Content -Encoding UTF8` round-trips the file through the console
code page and destroys every emoji in it. This script writes bytes directly and
refuses to write at all if the result contains U+FFFD, so the number and the
file's integrity are updated by the same code path.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
MANIFEST = ROOT / "hello" / "manifest.json"

# Matches the sentence carrying the figure.
PATTERN = re.compile(r"\*\*\d+\.\d+ %\*\* of core")

FLAG = "--check"


def coverage() -> tuple[float, int, int]:
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    core = [f for f in man["files"] if f["layer"] == "core"]
    have = sum(1 for f in core if f.get("real_template"))
    return (100.0 * have / len(core) if core else 0.0), have, len(core)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(FLAG, action="store_true",
                    help="exit 1 instead of writing when it is out of date")
    args = ap.parse_args()

    if not MANIFEST.is_file():
        print(f"error: {MANIFEST} missing -- run generate_all_hello.py first",
              file=sys.stderr)
        return 1

    pct, have, total = coverage()
    text = README.read_text(encoding="utf-8")

    if "\ufffd" in text:
        print("error: README already contains U+FFFD; refusing to touch it",
              file=sys.stderr)
        return 1

    match = PATTERN.search(text)
    if not match:
        print("error: no coverage figure found in README.md", file=sys.stderr)
        return 1

    desired = f"**{pct:.1f} %** of core"
    if match.group(0) == desired:
        print(f"coverage already up to date ({pct:.1f} %, {have}/{total} core)")
        return 0

    if args.check:
        print(f"README says {match.group(0)}, actual is {desired} "
              f"({have}/{total} core files)", file=sys.stderr)
        return 1

    updated = PATTERN.sub(desired, text, count=1)
    if "\ufffd" in updated:
        print("error: refusing to write a file containing U+FFFD",
              file=sys.stderr)
        return 1

    README.write_text(updated, encoding="utf-8", newline="\n")
    print(f"updated coverage: {match.group(0)} -> {desired} "
          f"({have}/{total} core files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())