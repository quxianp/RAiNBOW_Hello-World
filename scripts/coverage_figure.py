#!/usr/bin/env python3
"""The coverage figures, measured. Never type these into a commit message.

Every batch message used to end with a line like "Curated coverage 1 670 ->
1 704." Those numbers were written before the batch had been applied, by adding
up the entries offered rather than by counting what landed. They were wrong, and
they were wrong in the most embarrassing direction: they grew faster than the
repository did, because every batch message predicted success and roughly half of
each batch was rejected as a duplicate or as a language this repository does not
ship.

Forty of them were wrong by the time anyone checked. Twenty-nine template batches
in one day produced about four hundred new programs, not the thousand the
messages implied.

So the figure has an owner. This prints it, from the generator's own tables, and
`apply_batches.py` calls it after every batch so the number in a commit message is
the number the repository has.

    python scripts/coverage_figure.py
    python scripts/coverage_figure.py --short      # one line, for a message
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GEN = ROOT / "scripts" / "generate_all_hello.py"
CLASSES = ROOT / "data" / "placeholder_classes.json"


def load_generator():
    spec = importlib.util.spec_from_file_location("gen", GEN)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gen"] = mod
    spec.loader.exec_module(mod)
    return mod


def figures() -> dict:
    gen = load_generator()
    templates = {k: v for k, v in gen.HELLO.items() if v.strip()}
    inherit = dict(getattr(gen, "INHERIT", {}))

    man = json.loads((ROOT / "hello" / "manifest.json").read_text(encoding="utf-8"))
    files = man["files"]

    def has(language: str) -> bool:
        key = (language or "").strip().lower()
        return key in templates or key in inherit

    core = [f for f in files if f["path"].startswith("hello/core/")]
    full = [f for f in files if f["path"].startswith("hello/full/")]
    core_ok = sum(1 for f in core if has(f["language"]))
    full_ok = sum(1 for f in full if has(f["language"]))

    kinds = {}
    if CLASSES.exists():
        data = json.loads(CLASSES.read_text(encoding="utf-8"))
        kinds = dict(data.get("counts", {}))

    return {
        "files": len(files),
        "core": len(core),
        "full": len(full),
        "curated": len(templates),
        "inherit": len(inherit),
        "core_with_program": core_ok,
        "core_pct": 100.0 * core_ok / len(core) if core else 0.0,
        "full_with_program": full_ok,
        "kinds": kinds,
        "programs": len(templates) + len(inherit),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--short", action="store_true",
                    help="one line, suitable for pasting into a commit message")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    f = figures()

    if args.json:
        print(json.dumps(f, indent=2))
        return 0

    if args.short:
        print(f"{f['programs']} programs ({f['core_with_program']}/{f['core']} core, "
              f"{f['core_pct']:.1f} %) in {f['files']} files")
        return 0

    print(f"language files           : {f['files']:,}")
    print(f"  hello/core             : {f['core']:,}")
    print(f"  hello/full             : {f['full']:,}")
    print()
    print(f"curated templates        : {f['curated']:,}")
    print(f"inherit allowlist        : {f['inherit']:,}")
    print(f"programs in total        : {f['programs']:,}")
    print()
    print(f"core coverage            : {f['core_with_program']}/{f['core']} "
          f"({f['core_pct']:.1f} %)")
    print(f"full coverage            : {f['full_with_program']}/{f['full']} "
          f"({100.0 * f['full_with_program'] / f['full']:.1f} %)")
    if f["kinds"]:
        print()
        print("what the program-less files hold instead:")
        for kind, n in sorted(f["kinds"].items(), key=lambda kv: -kv[1]):
            print(f"  {n:6,}  {kind}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
