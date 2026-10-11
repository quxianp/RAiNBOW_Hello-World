#!/usr/bin/env python3
"""Summarise the language inventory by Linguist type.

    python scripts/language_report.py
    python scripts/language_report.py --top 40
    python scripts/language_report.py --markdown      # paste-ready tables

Answers questions the raw counts in the README do not: what kind of languages
are actually on the bar, which types are over- or under-represented, and how the
core layer compares with the vendored long tail in hello/full/.

Everything comes from hello/manifest.json, which is what the generators wrote,
so the report describes the files that exist rather than an intention.
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "hello" / "manifest.json"


def load() -> list[dict]:
    if not MANIFEST.is_file():
        print(f"error: {MANIFEST} not found", file=sys.stderr)
        raise SystemExit(1)
    return json.loads(MANIFEST.read_text(encoding="utf-8"))["files"]


def pct(part: int, whole: int) -> str:
    return f"{(100.0 * part / whole):5.1f} %" if whole else "  n/a"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--top", type=int, default=15,
                    help="how many languages to list per section")
    ap.add_argument("--markdown", action="store_true",
                    help="emit markdown tables instead of plain text")
    args = ap.parse_args()

    files = load()
    core = [f for f in files if f["layer"] == "core"]
    full = [f for f in files if f["layer"] == "full"]

    by_type_core = collections.Counter(f.get("type") or "unknown" for f in core)
    by_type_full = collections.Counter(f.get("type") or "unknown" for f in full)

    if args.markdown:
        print("### Languages by Linguist type\n")
        print("| Type | Core (`hello/core/`) | Share | Full (`hello/full/`) | Share |")
        print("|---|---:|---:|---:|---:|")
        for t, n in by_type_core.most_common():
            print(f"| {t} | {n:,} | {pct(n, len(core)).strip()} "
                  f"| {by_type_full.get(t, 0):,} "
                  f"| {pct(by_type_full.get(t, 0), len(full)).strip()} |")
    else:
        print("Languages by Linguist type")
        print("=" * 58)
        print(f"{'type':<16}{'core':>8}{'share':>10}{'full':>9}{'share':>10}")
        print("-" * 58)
        for t, n in by_type_core.most_common():
            fn = by_type_full.get(t, 0)
            print(f"{t:<16}{n:>8,}{pct(n, len(core)):>10}"
                  f"{fn:>9,}{pct(fn, len(full)):>10}")
        print("-" * 58)
        print(f"{'total':<16}{len(core):>8,}{'100.0 %':>10}"
              f"{len(full):>9,}{'100.0 %':>10}")

    # Which types are curated rather than placeholder?
    if not args.markdown:
        print()
        real = sum(1 for f in core if f.get("real_template"))
        print(f"core files with a curated template : {real:,} "
              f"({pct(real, len(core)).strip()})")
        runnable = sum(1 for f in core if f.get("runner"))
        print(f"core files with a runner           : {runnable:,} "
              f"({pct(runnable, len(core)).strip()})")

    # The longest names are the ones that make the legend image overflow.
    longest = sorted(core, key=lambda f: len(f["language"]), reverse=True)
    print()
    print(f"longest language names (top {min(args.top, len(longest))}):")
    for f in longest[: args.top]:
        name = f["language"]
        print(f"  {len(name):>3}  {name}  ({f.get('extension')})")

    return 0


if __name__ == "__main__":
    sys.exit(main())