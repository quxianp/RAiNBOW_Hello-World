#!/usr/bin/env python3
"""Rewrite the asset block in README.md between the RAINBOW_ASSETS markers.

    python scripts/update_readme_assets.py
    python scripts/update_readme_assets.py --check

Called by the ``assets`` workflow job after the GIF/MP4/bar renders exist.
Idempotent: running it twice produces no second diff, so the bot commit only
appears when something actually changed.

``--check`` exits 1 if the block is out of date, which is useful locally.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
START = "<!-- RAINBOW_ASSETS_START -->"
END = "<!-- RAINBOW_ASSETS_END -->"

BLOCK_TEMPLATE = """{start}

## \U0001f3ac The show

![rainbow bar](assets/rainbow-bar-github.png)

![demo](assets/hello-world.gif)

[\u2b07\u2193 Download the MP4](assets/hello-world.mp4)

> The three assets above are produced by `.github/workflows/rainbow.yml` on every
> push to `main`. Until the first successful run, they may not exist yet — see
> [Regenerating the assets](#regenerating-the-assets).

{end}"""

PATTERN = re.compile(
    re.escape(START) + r".*?" + re.escape(END), re.DOTALL
)


def build_block() -> str:
    return BLOCK_TEMPLATE.format(start=START, end=END)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 1 instead of writing when the block needs changing",
    )
    args = parser.parse_args()

    if not README.is_file():
        print(f"error: {README} not found", file=sys.stderr)
        return 1

    text = README.read_text(encoding="utf-8", newline="\n")
    match = PATTERN.search(text)
    if not match:
        print(f"error: markers {START} / {END} not found in {README}", file=sys.stderr)
        return 1

    desired = build_block()
    if match.group(0) == desired:
        print("README asset block already up to date")
        return 0

    if args.check:
        print("README asset block is out of date", file=sys.stderr)
        return 1

    updated = text[: match.start()] + desired + text[match.end() :]
    README.write_text(updated, encoding="utf-8", newline="\n")
    print(f"updated asset block in {README}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
