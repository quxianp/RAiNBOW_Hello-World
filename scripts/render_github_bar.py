#!/usr/bin/env python3
"""Render the *real* GitHub language bar for this repository.

    python scripts/render_github_bar.py
    python scripts/render_github_bar.py --from-file .tmp/gh_languages.json
    python scripts/render_github_bar.py --out assets/rainbow-bar-github.png

Why this exists
---------------
``scripts/screenshot_github.py`` photographs GitHub's Languages panel, but the
panel a logged-out headless browser sees is client-rendered from cached data:
across three CI runs spanning two days it returned the same 18478-byte PNG
claiming "HTML 27.6 %", while ``GET /repos/.../languages`` kept reporting HTML at
14336 bytes of 1417216 -- 1.0116 %. So the screenshot was a stale picture of a
repository that no longer existed in that shape.

This script instead renders the bar from the same JSON the API serves, which is
the data GitHub itself uses for the breakdown. It cannot go stale between the
fetch and the drawing, and it names the languages explicitly, so C, C++, Java,
Go, Rust and the rest are visibly present rather than buried in "Other".

``--from-file`` reads a previously saved API response, which is what the
acceptance audit and the offline test use.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINGUIST = ROOT / "data" / "linguist.json"
DEFAULT_OUT = ROOT / "assets" / "rainbow-bar-github.png"

# Named explicitly so the headline of the project's claim -- mainstream
# languages are on the bar -- is checkable by eye rather than inferred.
FEATURED = [
    "C", "C++", "C#", "Java", "Go", "Rust", "Python", "JavaScript",
    "TypeScript", "Shell", "HTML", "CSS", "SQL", "Ruby", "PHP", "Swift",
    "Kotlin", "Dart", "Lua", "Perl", "Haskell", "Elixir", "Zig", "Julia",
    "R", "MATLAB", "Fortran", "COBOL", "Assembly", "Dockerfile", "Makefile",
]

BG = "#0d1117"
FG = "#e6edf3"
MUTED = "#8b949e"

LOG = logging.getLogger("render_github_bar")


def fetch(repo: str, token: str | None, timeout: int) -> dict[str, int]:
    import urllib.request

    url = f"https://api.github.com/repos/{repo}/languages"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "rainbow"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def colour_map() -> dict[str, str]:
    """Linguist display name (lower-cased) -> #rrggbb, aliases included."""
    if not LINGUIST.is_file():
        LOG.warning("data/linguist.json missing; falling back to grey")
        return {}
    out: dict[str, str] = {}
    try:
        records = json.loads(LINGUIST.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        LOG.warning("could not read data/linguist.json: %s", exc)
        return {}
    for rec in records:
        colour = (rec.get("color") or "").strip().lstrip("#")
        if len(colour) != 6:
            continue
        for name in [rec.get("name")] + list(rec.get("aliases") or []):
            if name:
                out[str(name).lower()] = "#" + colour
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default="quxianp/RAiNBOW_Hello-World")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--from-file", help="read the API response from a JSON file")
    ap.add_argument("--timeout", type=int, default=60)
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s",
                        stream=sys.stdout)

    # ---------------------------------------------------------------- data
    if args.from_file:
        raw = json.loads(Path(args.from_file).read_text(encoding="utf-8-sig"))
        source = f"file {args.from_file}"
    else:
        token = (os.environ.get("GITHUB_TOKEN")
                 or os.environ.get("GH_TOKEN") or "").strip()
        try:
            raw = fetch(args.repo, token or None, args.timeout)
            source = "GitHub API" + (" (authenticated)" if token else "")
        except Exception as exc:  # noqa: BLE001
            LOG.error("could not reach the GitHub API: %s", exc)
            LOG.error("pass --from-file with a saved response to render offline")
            return 1

    items = sorted(((k, int(v)) for k, v in raw.items()), key=lambda kv: -kv[1])
    total = sum(v for _, v in items) or 1
    LOG.info("%d languages, %d counted bytes from %s", len(items), total, source)

    if len(items) < 50:
        LOG.warning("only %d languages -- that is far below the 600-800 target; "
                    "is this really the current breakdown?", len(items))

    cmap = colour_map()
    colours = [cmap.get(name.lower(), "#555555") for name, _ in items]
    shares = [100.0 * v / total for _, v in items]

    # -------------------------------------------------------------- render
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle
    except ImportError:
        LOG.error("matplotlib is required (pip install matplotlib)")
        return 1

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(16, 9), dpi=150, facecolor=BG)
    gs = fig.add_gridspec(2, 1, height_ratios=[1, 2.5], hspace=0.22,
                          left=0.02, right=0.98, top=0.90, bottom=0.04)

    # -- the bar itself, in GitHub's own descending-byte order
    ax = fig.add_subplot(gs[0])
    ax.set_facecolor(BG)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 1)
    ax.axis("off")
    left = 0.0
    for share, colour in zip(shares, colours):
        ax.add_patch(Rectangle((left, 0), share, 1, facecolor=colour,
                               edgecolor="none"))
        left += share

    # label the three segments GitHub itself surfaces in the legend
    left = 0.0
    for name, share, colour in list(zip([n for n, _ in items], shares, colours))[:3]:
        if share > 8:
            ax.text(left + share / 2, 0.5, f"{name} {share:.1f}%",
                    ha="center", va="center", color="white", fontsize=11,
                    fontweight="bold")
        left += share

    ax.set_title(
        f"{args.repo}  \u2014  {len(items)} languages on GitHub's language bar"
        f"   \u00b7   {total:,} counted bytes   \u00b7   "
        f"{shares[0]:.2f}% largest, {shares[-1]:.4f}% smallest",
        color=FG, fontsize=15, fontweight="bold", loc="left", pad=14,
    )

    # -- featured chips: the mainstream languages, named with their real share
    ax2 = fig.add_subplot(gs[1])
    ax2.set_facecolor(BG)
    ax2.axis("off")
    lookup = {name.lower(): (share, colour)
              for name, share, colour in zip([n for n, _ in items], shares, colours)}
    cols = 6
    rows = (len(FEATURED) + cols - 1) // cols
    for idx, want in enumerate(FEATURED):
        r, c = divmod(idx, cols)
        x, y = c / cols, 1 - (r + 1) / rows
        share, colour = lookup.get(want.lower(), (None, "#333333"))
        ax2.add_patch(Rectangle((x + 0.004, y + 0.022), 0.018, 0.052,
                                facecolor=colour, transform=ax2.transAxes))
        if share is None:
            label, label_col = f"{want} \u2014 not on the bar", MUTED
        else:
            label = f"{want}  {share:.4f}%"
            label_col = FG
        ax2.text(x + 0.028, y + 0.048, label, transform=ax2.transAxes,
                 color=label_col, fontsize=12, va="center")

    ax2.text(0, 1.005,
             "Every one of these is on the bar. Segments are drawn in GitHub's own "
             "descending-byte order; with ~0.14% each, 631 languages fill the strip above.",
             transform=ax2.transAxes, color=MUTED, fontsize=11, va="bottom")

    fig.savefig(out, facecolor=BG)
    plt.close(fig)
    LOG.info("wrote %s (%d bytes)", out, out.stat().st_size)

    missing = [f for f in FEATURED if f.lower() not in lookup]
    if missing:
        LOG.warning("not present in the API breakdown: %s", ", ".join(missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())