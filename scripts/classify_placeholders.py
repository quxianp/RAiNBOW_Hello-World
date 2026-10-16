#!/usr/bin/env python3
"""Classify every language file that has no program, by what it deserves instead.

The repository has 7 326 language files and roughly 1 070 of them carry a real
Hello World program. It is tempting to read the remaining 6 200 as a backlog of
unfinished work. That reading is wrong, and the data says so.

`data/merged_langs.json` records where every language came from and how Linguist
classifies it. Sorting the placeholder set by that gives four groups that need
four different answers:

  programming        a program is expected. Write one.
  markup/data/config the *document* is the answer. A `.cabal` file has no
                     program; its fields are the content. Saying so is correct,
                     not a shortfall.
  binary             there is no text to print. A `.obj` file is a byte string.
  esoteric           mostly languages whose Hello World is genuinely not written
                     down. Inventing one would be a plausible lie.

This script produces that split, so the next decision is made per group instead
of per file. It writes `data/placeholder_classes.json` and prints a summary.

Run it with --check to assert the classification on disk is current.
"""

from __future__ import annotations

import argparse
import collections
import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "hello" / "manifest.json"
MERGED = ROOT / "data" / "merged_langs.json"
OUT = ROOT / "data" / "placeholder_classes.json"

# What kind of answer each Linguist type can have. The categories are about the
# *file*, not about whether this project managed to fill it in -- which is the
# distinction that made the backlog look like a backlog.
KINDS = {
    "programming": "program",
    "markup": "document",
    "data": "document",
    "prose": "document",
}

# Groups that describe something other than a programming language even when
# Linguist's `type` is absent or wrong. These come from Linguist's own groupings
# and are the reason a plain type lookup is not enough.
NON_PROGRAM_GROUPS = {
    "binary_data": "binary",
    "markup_data": "document",
    "build_config": "document",
    "template": "document",
    "data_science": "document",
    "dsl_query": "program",
    "shell_os": "program",
    "assembly_dialects": "program",
    "ancient": "program",
    "education": "program",
    "chinese": "program",
    "golf": "program",
    "functional": "program",
    "concurrency": "program",
    "logic_constraint": "program",
    "blockchain": "program",
    "quantum": "program",
    "academic": "program",
    "misc": "program",
    "esoteric": "esolang",
}


def load_generator():
    """Import generate_all_hello.py for its template tables.

    It runs a `main()` under `if __name__ == "__main__"`, so importing it is
    safe, but it also expects to be run from the repository root.
    """
    spec = importlib.util.spec_from_file_location(
        "gen", ROOT / "scripts" / "generate_all_hello.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gen"] = mod
    spec.loader.exec_module(mod)
    return mod


def has_program(gen, language: str) -> bool:
    key = (language or "").strip().lower()
    templates = getattr(gen, "HELLO", {})
    if templates.get(key, "").strip():
        return True
    return key in getattr(gen, "INHERIT", {})


def kind_for(entry: dict) -> tuple[str, str]:
    """Return (kind, reason). Reason says which field decided it."""
    ltype = entry.get("type")
    groups = entry.get("groups") or []
    for g in groups:
        if g in NON_PROGRAM_GROUPS:
            return NON_PROGRAM_GROUPS[g], f"group:{g}"
    if ltype in KINDS:
        return KINDS[ltype], f"type:{ltype}"
    if ltype is None and any(s == "esolangs" for s in (entry.get("source") or [])):
        return "esolang", "source:esolangs"
    return "unknown", "unclassified"


def build() -> dict:
    gen = load_generator()
    merged = json.loads(MERGED.read_text(encoding="utf-8"))
    by_name = {e["key"]: e for e in merged}
    by_display = {e["name"]: e for e in merged}

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = []
    counts = collections.Counter()
    reasons = collections.Counter()

    for f in manifest["files"]:
        language = f.get("language") or ""
        if has_program(gen, language):
            continue
        entry = by_name.get(language.lower()) or by_display.get(language)
        if entry is None:
            kind, reason = "unknown", "not-in-merged"
        else:
            kind, reason = kind_for(entry)
        counts[kind] += 1
        reasons[reason] += 1
        rows.append({
            "language": language,
            "path": f["path"],
            "extension": f.get("extension"),
            "kind": kind,
            "reason": reason,
            "groups": entry.get("groups") if entry else [],
            "source": entry.get("source") if entry else [],
        })

    rows.sort(key=lambda r: (r["kind"], r["extension"] or "", r["language"]))
    return {
        "generated_by": "scripts/classify_placeholders.py",
        "total_files": len(manifest["files"]),
        "without_program": len(rows),
        "counts": dict(sorted(counts.items())),
        "reasons": dict(sorted(reasons.items(), key=lambda kv: -kv[1])),
        "files": rows,
    }


def summarise(data: dict) -> None:
    print(f"files in the manifest      : {data['total_files']}")
    print(f"files without a program    : {data['without_program']}")
    print()
    print("by what they deserve instead:")
    for kind, n in sorted(data["counts"].items(), key=lambda kv: -kv[1]):
        print(f"  {n:5}  {kind}")
    print()
    print("decided by:")
    for reason, n in sorted(data["reasons"].items(), key=lambda kv: -kv[1])[:14]:
        print(f"  {n:5}  {reason}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="fail if data/placeholder_classes.json is out of date")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    data = build()
    payload = json.dumps(data, indent=2, sort_keys=False) + "\n"

    if args.check:
        if not OUT.exists():
            print(f"check: {OUT} does not exist; run without --check", file=sys.stderr)
            return 1
        current = OUT.read_text(encoding="utf-8")
        if current != payload:
            print(f"check: {OUT.name} is stale; run without --check to refresh",
                  file=sys.stderr)
            return 1
        if not args.quiet:
            print(f"check: {OUT.name} is current "
                  f"({data['without_program']} files classified)")
        return 0

    OUT.write_text(payload, encoding="utf-8", newline="\n")
    if not args.quiet:
        summarise(data)
        print()
        print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
