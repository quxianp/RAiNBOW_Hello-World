#!/usr/bin/env python3
"""Render the *real* GitHub language bar for this repository, with every
language listed.

    python scripts/render_github_bar.py
    python scripts/render_github_bar.py --from-file .tmp/gh_languages.json
    python scripts/render_github_bar.py --out assets/rainbow-bar-github.png
    python scripts/render_github_bar.py --columns 12 --font 8

Why this exists
---------------
``scripts/screenshot_github.py`` photographs GitHub's Languages panel, but the
panel a logged-out headless browser sees is client-rendered from cached data:
across three CI runs spanning two days it returned the same 18478-byte PNG
claiming "HTML 27.6 %", while ``GET /repos/.../languages`` kept reporting HTML at
14336 bytes of 1417216 -- 1.0116 %. So the screenshot was a stale picture of a
repository that no longer existed in that shape.

This script renders from the same JSON the API serves, which is the data GitHub
itself uses for the breakdown, and -- importantly -- prints **every** language in
it, with its colour and its real share. GitHub's own legend can only name the
largest handful and folds the remaining 600+ into one grey "Other" row, so a
reader can never see that C, C++, Java, Go and Rust are all on the bar. Here they
are, all 631 of them, in the same descending-byte order as the strip above.

``--from-file`` reads a previously saved API response; that is what the offline
test and the acceptance audit use.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINGUIST = ROOT / "data" / "linguist.json"
CORE_LIST = ROOT / "config" / "core-langs.txt"
DEFAULT_OUT = ROOT / "assets" / "rainbow-bar-github.png"

BG = "#0d1117"
FG = "#e6edf3"
MUTED = "#8b949e"
UNKNOWN = "#3d444d"

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
        LOG.warning("data/linguist.json missing; unknown languages render grey")
        return {}
    try:
        records = json.loads(LINGUIST.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        LOG.warning("could not read data/linguist.json: %s", exc)
        return {}
    out: dict[str, str] = {}
    for rec in records:
        colour = (rec.get("color") or "").strip().lstrip("#")
        if len(colour) != 6:
            continue
        for name in [rec.get("name")] + list(rec.get("aliases") or []):
            if name:
                out[str(name).lower()] = "#" + colour
    return out


def configured_core_names() -> list[str]:
    if not CORE_LIST.is_file():
        return []
    return [l.strip() for l in CORE_LIST.read_text(encoding="utf-8").splitlines()
            if l.strip()]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default="quxianp/RAiNBOW_Hello-World")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--from-file", help="read the API response from a JSON file")
    ap.add_argument("--columns", type=int, default=10)
    ap.add_argument("--font", type=float, default=7.2)
    ap.add_argument("--width", type=float, default=24.0,
                    help="minimum figure width in inches; it grows if the "
                         "longest language name needs more room")
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
        LOG.warning("only %d languages -- far below the 600-800 target; "
                    "is this really the current breakdown?", len(items))

    cmap = colour_map()
    shares = [100.0 * v / total for _, v in items]
    names = [n for n, _ in items]
    colours = [cmap.get(n.lower(), UNKNOWN) for n in names]

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

    cols = max(1, args.columns)
    rows = math.ceil(len(items) / cols)
    font = args.font

    # Height is driven by the legend: one comfortable line per row. Width is
    # fixed so a column is wide enough for the longest Linguist name plus its
    # percentage without the two colliding.
    bar_h = 2.3
    legend_h = rows * (font / 72.0) * 1.45 + 0.4
    header_h = 1.05
    footer_h = 0.55

    # A column must fit "swatch + longest name + longest percentage". Deriving
    # the figure width from the longest actual name means
    # "Mathematical Programming System" and "Windows Registry Entries" cannot
    # collide with the share printed on their right, at any language count.
    char_w = font * 0.602 / 72.0                 # monospace advance, inches
    longest_name = max(len(n) for n in names)
    pct_w = len(f"{shares[-1]:.4f}%")
    per_col = (0.06 + longest_name * char_w + 0.12 + pct_w * char_w + 0.06)
    width = max(args.width, per_col * cols + 0.3)

    fig = plt.figure(figsize=(width, bar_h + legend_h + header_h + footer_h),
                     dpi=100, facecolor=BG)
    total_h = bar_h + legend_h + header_h + footer_h
    gs = fig.add_gridspec(
        2, 1, height_ratios=[bar_h, legend_h], hspace=0.05,
        left=0.010, right=0.990,
        top=1.0 - header_h / total_h,
        bottom=footer_h / total_h,
    )

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

    # label only the segments wide enough to hold a label
    left = 0.0
    for name, share, colour in zip(names, shares, colours):
        if share >= 3.0:
            ax.text(left + share / 2, 0.5, f"{name} {share:.1f}%",
                    ha="center", va="center", color="#0d1117",
                    fontsize=10, fontweight="bold")
        left += share

    ax.text(0, 1.30, f"{args.repo}", color=FG, fontsize=15, fontweight="bold",
            transform=ax.transAxes)
    ax.text(0, 1.12,
            f"all {len(items)} languages GitHub detects on this repository, "
            f"in its own descending-byte order  \u00b7  {total:,} counted bytes  "
            f"\u00b7  {shares[0]:.4f}% largest, {shares[-1]:.4f}% smallest",
            color=MUTED, fontsize=11, transform=ax.transAxes)
    ax.text(1.0, 1.12,
            "every language is listed below \u2014 GitHub's own legend shows "
            "only the largest few and folds the rest into \"Other\"",
            color=MUTED, fontsize=10, ha="right", transform=ax.transAxes)

    # -- full legend: all languages, same order as the strip above
    ax2 = fig.add_subplot(gs[1])
    ax2.set_facecolor(BG)
    ax2.axis("off")

    col_w = 1.0 / cols
    swatch_w = 0.0060
    for idx, (name, share, colour) in enumerate(zip(names, shares, colours)):
        r, c = divmod(idx, cols)
        x = c * col_w
        y = 1.0 - (r + 1) / rows
        mid = y + 0.5 / rows
        ax2.add_patch(Rectangle((x + 0.0015, mid - 0.20 / rows), swatch_w,
                                0.40 / rows, facecolor=colour,
                                transform=ax2.transAxes, clip_on=False))
        # Name left-aligned, share right-aligned inside the same column, so a
        # long name such as "Mathematical Programming System" can never run
        # into its neighbour's percentage.
        ax2.text(x + 0.0015 + swatch_w * 2.4, mid, name,
                 transform=ax2.transAxes, color=FG, fontsize=font,
                 va="center", ha="left", family="monospace", clip_on=False)
        ax2.text(x + col_w - 0.0035, mid, f"{share:.4f}%",
                 transform=ax2.transAxes, color=MUTED, fontsize=font,
                 va="center", ha="right", family="monospace", clip_on=False)

    configured = configured_core_names()
    footer = (f"{len(items)} languages shown, all of them \u2014 GitHub's own legend "
              f"names only the largest few. hello/core holds {len(configured)} "
              f"configured files of {2048 * len(configured):,} counted bytes; "
              f"Linguist folds some names together (the seven HTML-family files "
              f"become a single HTML segment, and a few names are canonicalised), "
              f"so the segment count is lower than the file count."
              if configured else
              f"{len(items)} languages shown.")
    fig.text(0.010, 0.006, footer, color=MUTED, fontsize=font + 1.6,
             va="bottom", ha="left")

    fig.savefig(out, facecolor=BG)
    plt.close(fig)
    LOG.info("wrote %s (%d bytes, %d rows x %d columns)",
             out, out.stat().st_size, rows, cols)

    unknown = [n for n, col in zip(names, colours) if col == UNKNOWN]
    if unknown:
        LOG.warning("%d languages had no Linguist colour and render grey: %s",
                    len(unknown), ", ".join(unknown[:10]))
    return 0


if __name__ == "__main__":
    sys.exit(main())