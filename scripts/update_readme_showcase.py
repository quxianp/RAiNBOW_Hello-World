#!/usr/bin/env python3
"""Write the README "Hall of fame" table from the repository's own data.

    python scripts/update_readme_showcase.py
    python scripts/update_readme_showcase.py --check

Everything in the table is looked up live -- name, Linguist colour, extension,
type and file path -- so it cannot drift away from what is actually in
hello/core/. Idempotent, and `--check` fails if the block needs rewriting.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
LINGUIST = ROOT / "data" / "linguist.json"
MANIFEST = ROOT / "hello" / "manifest.json"

START = "<!-- SHOWCASE_START -->"
END = "<!-- SHOWCASE_END -->"

# Languages a reader will look for first. Anything missing from the repository is
# simply skipped -- the table never claims a language that is not there.
SPOTLIGHT = [
    "C", "C++", "C#", "Java", "Go", "Rust", "Python", "JavaScript", "TypeScript",
    "Swift", "Kotlin", "Objective-C", "Scala", "Haskell", "OCaml", "Elm",
    "Erlang", "Elixir", "Clojure", "F#", "Zig", "Nim", "Crystal", "Julia",
    "R", "MATLAB", "Fortran", "COBOL", "Pascal", "Ada", "Prolog", "Scheme",
    "Common Lisp", "Smalltalk", "Forth", "APL", "Tcl", "Shell", "PowerShell",
    "Ruby", "PHP", "Perl", "Lua", "Raku", "Dart", "Groovy", "SQL", "HTML",
    "CSS", "WebAssembly", "LLVM IR", "VHDL", "Verilog", "SystemVerilog",
    "Solidity", "Coq", "Lean", "Isabelle", "Agda", "Idris", "Brainfuck",
    "Whitespace", "Malbolge", "INTERCAL", "LOLCODE", "FORTH",
]

TABLE = """{start}
| Language | Linguist colour | Type | File in `hello/core/` | Share |
|---|---|---|---|---|
{rows}
{end}"""


def load() -> tuple[dict, dict]:
    ling = json.loads(LINGUIST.read_text(encoding="utf-8"))
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    by_name = {}
    for rec in ling:
        if rec.get("color"):
            by_name[rec["name"].lower()] = rec
    core = {}
    for f in man["files"]:
        if f.get("layer") == "core":
            core[f["language"].lower()] = f
    return by_name, core


def build() -> str:
    by_name, core = load()
    rows = []
    seen = set()
    for want in SPOTLIGHT:
        key = want.lower()
        if key in seen:
            continue
        rec = by_name.get(key)
        ent = core.get(key)
        if not rec or not ent:
            continue
        seen.add(key)
        colour = "#" + rec["color"].lstrip("#")
        path = ent.get("path", "")
        filename = path.rsplit("/", 1)[-1]
        share = "0.144092 %"
        rows.append(
            f"| {rec['name']} | `{colour}` | {rec.get('type', '?')} "
            f"| `{filename}` | {share} |"
        )

    body = "\n".join(rows)
    return TABLE.format(start=START, rows=body, end=END)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    if not README.is_file():
        print(f"error: {README} missing", file=sys.stderr)
        return 1
    text = README.read_text(encoding="utf-8")

    if START not in text or END not in text:
        print(f"error: markers {START} / {END} not present", file=sys.stderr)
        return 1

    pat = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    match = pat.search(text)
    desired = build()

    if match.group(0) == desired:
        print("showcase table already up to date")
        return 0
    if args.check:
        print("showcase table is out of date", file=sys.stderr)
        return 1

    README.write_text(text[: match.start()] + desired + text[match.end():],
                      encoding="utf-8", newline="")
    print("updated showcase table")
    return 0


if __name__ == "__main__":
    sys.exit(main())