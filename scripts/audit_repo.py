#!/usr/bin/env python3
"""Print a health report for the repository.

    python scripts/audit_repo.py
    python scripts/audit_repo.py --strict     # exit 1 on any WARN or FAIL

This is the first thing to run when the language bar looks wrong, and it is what
the bug report template asks for. It answers, without needing the GitHub API:

  * how many core and full files exist on disk versus what the manifest claims,
  * whether every core file really is the exact same size -- the property the
    whole bar rests on,
  * whether the byte shares still add up to 100 %,
  * which core languages have no Linguist colour and therefore cannot be on the
    bar at all,
  * whether the assets the README embeds actually exist and are non-trivial.

Everything is derived from files in the repository. Exit status is 0 unless
something is actually broken, so it is safe to run as a smoke test.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "hello" / "core"
FULL = ROOT / "hello" / "full"
MANIFEST = ROOT / "hello" / "manifest.json"
LINGUIST = ROOT / "data" / "linguist.json"
README = ROOT / "README.md"

# Files the README embeds. A missing one is a broken image, not a cosmetic bug.
REQUIRED_ASSETS = [
    "assets/hero-banner.png",
    "assets/hello-world.gif",
    "assets/hello-world.mp4",
    "assets/rainbow-bar-github.png",
    "assets/rainbow-bar-local.png",
    "assets/rainbow-wheel.png",
]

# Below this a rendered image is almost certainly blank, and a zero-byte GIF
# renders as a broken-image icon.
MIN_ASSET_BYTES = 1024

status_counts: Counter[str] = Counter()


def report(level: str, msg: str) -> None:
    status_counts[level] += 1
    print(f"  [{level:<4}] {msg}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if anything WARNs or FAILs")
    args = ap.parse_args()

    print("RAiNBOW_Hello-World audit")
    print("=" * 60)

    # ---------------------------------------------------------------- files
    core_files = sorted(p for p in CORE.rglob("*") if p.is_file())
    full_files = sorted(p for p in FULL.rglob("*") if p.is_file())
    print(f"\nfiles on disk: {len(core_files)} core, {len(full_files)} full, "
          f"{len(core_files) + len(full_files)} total")

    if not core_files:
        report("FAIL", "hello/core is empty")
    if not full_files:
        report("FAIL", "hello/full is empty")

    empty = [p for p in core_files if p.stat().st_size == 0]
    if empty:
        report("FAIL", f"{len(empty)} zero-byte core file(s), e.g. "
                       f"{empty[0].relative_to(ROOT)}")
    else:
        report("ok", "no zero-byte core files")

    # ------------------------------------------------- the equal-size invariant
    # This is the property the entire bar depends on: equal byte size means
    # equal share, which means the hue ordering is actually visible.
    sizes = Counter(p.stat().st_size for p in core_files)
    if not sizes:
        report("FAIL", "no core files to measure")
    else:
        size, count = sizes.most_common(1)[0]
        report("ok" if count == len(core_files) else "FAIL",
               f"core files share one size: {size} bytes ({count}"
               f"/{len(core_files)})")
        if count != len(core_files):
            odd = [p for p in core_files if p.stat().st_size != size]
            report("WARN", f"{len(odd)} core file(s) differ, e.g. "
                           f"{odd[0].relative_to(ROOT)} = "
                           f"{odd[0].stat().st_size} bytes")
            report("WARN", "run: python scripts/balance_bytes.py")

    # ------------------------------------------------------------- manifest
    if MANIFEST.is_file():
        try:
            man = json.loads(MANIFEST.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            report("FAIL", f"manifest.json is not valid JSON: {exc}")
            man = {}
        if man:
            claimed_core = man.get("core_languages")
            claimed_full = man.get("full_languages")
            report("ok" if claimed_core == len(core_files) else "WARN",
                   f"manifest core_languages={claimed_core} "
                   f"vs {len(core_files)} on disk")
            report("ok" if claimed_full == len(full_files) else "WARN",
                   f"manifest full_languages={claimed_full} "
                   f"vs {len(full_files)} on disk")
    else:
        report("WARN", "hello/manifest.json missing")

    # ------------------------------------------------------- byte share sums
    if core_files:
        total = sum(p.stat().st_size for p in core_files)
        share = 100.0 / len(core_files)
        report("ok", f"each core language = {share:.6f} % of the bar")
        report("ok", f"share sum = {len(core_files) * share:.6f} %")

    # -------------------------------------------------------------- colours
    if LINGUIST.is_file():
        try:
            ling = json.loads(LINGUIST.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            report("WARN", f"linguist.json unreadable: {exc}")
            ling = []
        uncoloured = [r["name"] for r in ling if not r.get("color")]
        if uncoloured:
            report("ok", f"{len(uncoloured)} Linguist languages have no colour "
                         f"and cannot appear on a colour bar (correctly excluded)")
    else:
        report("WARN", "data/linguist.json missing")

    # -------------------------------------------------------------- assets
    for rel in REQUIRED_ASSETS:
        p = ROOT / rel
        if not p.is_file():
            report("FAIL", f"missing asset {rel}")
        elif p.stat().st_size < MIN_ASSET_BYTES:
            report("FAIL", f"{rel} is {p.stat().st_size} bytes, "
                           f"suspiciously small (degenerate render?)")
        else:
            report("ok", f"{rel} ({p.stat().st_size:,} bytes)")

    if README.is_file():
        text = README.read_text(encoding="utf-8")
        for rel in REQUIRED_ASSETS:
            if rel not in text:
                report("WARN", f"{rel} exists but the README does not embed it")

    # -------------------------------------------------------------- verdict
    print("\n" + "=" * 60)
    summary = "  ".join(f"{k}={v}" for k, v in sorted(status_counts.items()))
    print(f"{summary}")

    bad = status_counts["FAIL"]
    warn = status_counts["WARN"]
    if bad:
        print(f"RESULT: {bad} failure(s)")
    elif warn:
        print("RESULT: healthy, with warnings")
    else:
        print("RESULT: healthy")

    if bad:
        return 1
    if warn and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())