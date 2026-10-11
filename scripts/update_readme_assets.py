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

CLAPPER = "\u2b07\u2193"          # down arrow
PARTY = "\U0001f3ac"            # clapper board
DASH = "\u2014"                 # em dash
NDASH = "\u2013"                # en dash
DOT = "\u00b7"                  # middle dot

BLOCK_TEMPLATE = f"""{START}

## {PARTY} The show

![all 631 languages, drawn from the GitHub API](assets/rainbow-bar-github.png)

![rainbow bar, hue-ordered](assets/rainbow-bar-local.png)

![demo](assets/hello-world.gif)

[{CLAPPER} Download the MP4](assets/hello-world.mp4)

> **First image** {DASH} drawn from `GET /repos/.../languages`, the exact breakdown
> GitHub uses. The bar, plus **all 631 languages listed by name** with their
> colour and their real share {DASH} C, C++, C#, Java, Go, Rust, Python, TypeScript,
> Fortran, Assembly, Zig down to `xBase` and `Zil`. Nothing is hidden behind an
> "Other" bucket.
>
> **Why that image exists:** GitHub's own legend can only name a handful of
> languages and collapses the remaining 600+ into a single grey **Other** row, so
> C and C++ never appear by name on the site no matter how the repository is
> built. The bar itself does contain them {DASH} it is 631 hair-thin segments {DASH} but
> the legend will not say so.
>
> **Second image** {DASH} the same 694 Linguist colours ordered by hue, generated
> deterministically from `config/rainbow_langs.json`, so it is always current.
>
> **GIF and MP4** {DASH} `run.sh` recorded with VHS in GitHub Actions.

{END}"""

PATTERN = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)


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

    text = README.read_text(encoding="utf-8")
    match = PATTERN.search(text)
    if not match:
        print(f"error: markers {START} / {END} not found in {README}", file=sys.stderr)
        return 1

    desired = BLOCK_TEMPLATE
    if match.group(0) == desired:
        print("README asset block already up to date")
        return 0

    if args.check:
        print("README asset block is out of date", file=sys.stderr)
        return 1

    updated = text[: match.start()] + desired + text[match.end():]
    README.write_text(updated, encoding="utf-8", newline="")
    print(f"updated asset block in {README}")
    return 0


if __name__ == "__main__":
    sys.exit(main())