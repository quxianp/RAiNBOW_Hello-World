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

BLOCK_TEMPLATE = f"""{START}

## {PARTY} The show

<div align="center">

<table>
<tr>
<td width="50%" valign="top">

<img src="assets/rainbow-bar-github.png" alt="The GitHub language bar: all 631 languages, each named with its real share">

<br><sub><b>All 631 languages.</b><br>Drawn from <code>GET /repos/&#8230;/languages</code>{DASH}the breakdown GitHub itself serves.</sub>

</td>
<td width="50%" valign="top">

<img src="assets/rainbow-bar-local.png" alt="The hue sweep: 694 Linguist colours ordered by hue">

<br><sub><b>The hue sweep.</b><br>694 Linguist colours, ordered by hue.</sub>

</td>
</tr>
</table>

</div>

<div align="center">

<img src="assets/hello-world.gif" width="820" alt="run.sh: the animated show, ending on a true-colour Hello World!">

<br><sub>{CLAPPER} <a href="assets/hello-world.mp4">Download the MP4</a> {DASH} <code>run.sh</code> recorded with VHS in GitHub Actions.</sub>

</div>

> **Why the bar is drawn rather than screenshotted.** GitHub's own legend can
> only name the largest handful of languages and collapses the remaining 600+
> into a single grey <b>Other</b> row, so C and C++ never appear by name on the
> site no matter how this repository is built. The bar itself does contain them
> {DASH} 631 hair-thin segments {DASH} but the legend will not say so, which is why both
> images above are generated from the JSON GitHub itself serves.

{END}"""

PATTERN = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--check",
        action="store_true",
        help="exit 1 instead of writing when the block needs changing",
    )
    args = ap.parse_args()

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

    README.write_text(
        text[: match.start()] + desired + text[match.end():],
        encoding="utf-8", newline="")
    print(f"updated asset block in {README}")
    return 0


if __name__ == "__main__":
    sys.exit(main())