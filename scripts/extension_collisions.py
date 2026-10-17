#!/usr/bin/env python3
"""How many of this repository's files depend on an extension nobody owns?

`hello/manifest.json` records one extension per language. That is a lossy
summary of what GitHub Linguist actually does, and it loses information in a way
that is invisible until something depends on it.

Linguist resolves a file by filename first, then by path pattern, then by
extension -- and where several languages claim one extension, the winner is
decided by Linguist's heuristics, not by us. So for every such extension the
manifest holds two claims and Linguist will honour one of them. `Rez` is the
example that surfaced this: Linguist gives both R and Rez the extension `.r`,
our manifest therefore has `hello/core/rez/hello.r` and `hello/core/r/hello.r`
side by side, and both of those files are R as far as the language bar is
concerned.

That is not automatically wrong. A hundred of these are Linguist being
deliberately vague -- `.pl` is Perl, Prolog and Pl all at once, and Linguist
picks by looking at what is in the file. But it does mean a *count* derived
from the manifest can disagree with the bar GitHub shows, and the size of that
disagreement is worth measuring rather than assuming.

So this reports, per colliding extension:

  * which languages claim it, and how many files each contributes;
  * how many of those files are in the core layer, where they are counted;
  * how many bytes they carry, which is what the rainbow bar is balanced by.

It does not guess which language Linguist would pick. That question needs
Linguist, `scripts/linguist_audit.rb`, and a clone -- and a tool that answered
it by reading the manifest would be answering a different question with a
straight face, which is the failure mode this repository has hit four times
today.

    python scripts/extension_collisions.py
    python scripts/extension_collisions.py --short
    python scripts/extension_collisions.py --json
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "hello" / "manifest.json"


def load() -> list[dict]:
    if not MANIFEST.exists():
        print("no manifest; run scripts/generate_all_hello.py first",
              file=sys.stderr)
        raise SystemExit(1)
    return json.loads(MANIFEST.read_text(encoding="utf-8"))["files"]


def byte_totals() -> dict[str, int]:
    """On-disk size per file, measured rather than taken from the manifest.

    The manifest records the byte *share* a language was given -- the field is
    `share`, not `bytes`, and summing it would answer a different question.
    What this tool wants is how many bytes are actually at stake, so it stats
    the files. A file that is missing counts as zero rather than raising,
    because a collision audit is the wrong place to discover a checkout that is
    not clean.
    """
    out: dict[str, int] = {}
    for f in load():
        p = ROOT / f["path"]
        try:
            out[f["path"]] = p.stat().st_size
        except OSError:
            out[f["path"]] = 0
    return out


def collides() -> list[dict]:
    """Every extension more than one language claims, largest first."""
    by_ext: dict[str, list[dict]] = collections.defaultdict(list)
    for f in load():
        by_ext[f.get("extension") or ""].append(f)

    sizes = byte_totals()
    out = []
    for ext, files in by_ext.items():
        langs = sorted({f["language"] for f in files})
        if len(langs) < 2:
            continue
        core = [f for f in files if f["path"].startswith("hello/core/")]
        out.append({
            "extension": ext,
            "languages": langs,
            "files": len(files),
            "core_files": len(core),
            "bytes": sum(sizes[f["path"]] for f in files),
        })
    out.sort(key=lambda d: (-d["files"], d["extension"]))
    return out


def figures() -> dict:
    """The whole result as numbers, for anything that wants to quote one."""
    rows = collides()
    files = load()
    touched = sum(r["files"] for r in rows)
    return {
        "files": len(files),
        "extensions": len({f.get("extension") or "" for f in files}),
        "colliding_extensions": len(rows),
        "colliding_files": touched,
        "colliding_pct": round(100.0 * touched / len(files), 1) if files else 0.0,
        "colliding_core_files": sum(r["core_files"] for r in rows),
        "colliding_bytes": sum(r["bytes"] for r in rows),
        "largest": rows[0] if rows else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--short", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--top", type=int, default=40)
    args = ap.parse_args()

    rows = collides()
    f = figures()

    if args.json:
        print(json.dumps({**f, "rows": rows}, ensure_ascii=False, indent=2))
        return 0

    if args.short:
        print(f"{f['colliding_extensions']} of {f['extensions']} extensions "
              f"are claimed by more than one language, covering "
              f"{f['colliding_files']} of {f['files']} files "
              f"({f['colliding_pct']} %), "
              f"{f['colliding_core_files']} of them in the core layer")
        return 0

    print(f"{f['colliding_extensions']} colliding extension(s), "
          f"{f['colliding_files']} file(s), {f['colliding_pct']} % of the "
          f"repository, {f['colliding_bytes']} bytes\n")
    print(f"  {'extension':<26} {'files':>5} {'core':>5}  languages")
    for r in rows[:args.top]:
        langs = ", ".join(r["languages"])
        if len(langs) > 58:
            langs = langs[:55] + "..."
        print(f"  {r['extension']:<26} {r['files']:>5} {r['core_files']:>5}  "
              f"{langs}")
    if len(rows) > args.top:
        print(f"  ... and {len(rows) - args.top} more")
    print("\nLinguist decides which language wins; this only counts how much is "
          "at stake.")
    return 0


if __name__ == "__main__":
    sys.exit(main())