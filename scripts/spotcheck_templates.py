#!/usr/bin/env python3
"""Turn the ad-hoc spot-check into a documented script.

    python scripts/spotcheck_templates.py
    python scripts/spotcheck_templates.py --full

Reading a sample of the generated files is the only check that a template is the
*right* program for its language. Everything else here establishes that a file
has a template; only looking establishes that the template is correct.

Kept in the repository because it is the check that would have caught a matcher
serving the wrong language -- the failure mode of E25, where every file was valid
in *some* language and nothing but reading would notice it was the wrong one.

Two things it has to get right, both learned the hard way:

  * find the end of the banner by its known final line, not by filtering each
    line by substring. A version that filtered guessed wrong on files whose
    banner used a different comment character, and reported them as containing
    nothing but a banner when they were perfectly fine.
  * special-case Whitespace. Its program genuinely is spaces and tabs, so any
    strip-based check empties it and calls a correct file empty.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "hello" / "manifest.json"
OUT = ROOT / ".tmp" / "spotcheck.txt"

# A spread: mainstream languages, esolangs, hardware description, data formats,
# config, and the ones most likely to have been filled in by mistake.
DEFAULT_SAMPLE = [
    "Ada", "COBOL", "ALGOL", "Prolog", "Forth", "Brainfuck", "Whitespace",
    "LOLCODE", "INTERCAL", "Befunge", "Malbolge", "Factor", "PostScript",
    "J", "APL", "Smalltalk", "Self", "Eiffel", "Haskell", "OCaml",
    "Standard ML", "Erlang", "Elixir", "Clojure", "Racket", "Scheme",
    "Ruby", "Crystal", "Nim", "Zig", "V", "Odin", "Julia", "R", "MATLAB",
    "Pascal", "Modula-2", "Fortran", "SQL", "JSON", "YAML", "Dockerfile",
    "Ansible", "Makefile", "Nix", "PowerShell", "Batchfile", "Assembly",
    "Verilog", "VHDL", "Solidity", "WebAssembly", "LLVM", "Zephir",
    "Elm", "Tcl", "Awk", "Haxe", "PureScript", "Gleam", "Raku",
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--full", action="store_true",
                    help="check every curated template rather than a sample")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    files = man["files"]
    by = {f["language"]: f for f in files}

    if args.full:
        names = [f["language"] for f in files if f.get("real_template")]
    else:
        names = DEFAULT_SAMPLE

    rows = []
    problems = 0
    seen = set()

    for name in names:
        if name in seen:
            continue
        seen.add(name)
        f = by.get(name)
        if not f:
            rows.append(f"??   {name:16} (not in manifest)")
            continue
        if not f.get("real_template"):
            rows.append(f"none {name:16} (no curated template)")
            continue

        path = ROOT / f["path"]
        body = path.read_text(encoding="utf-8", errors="replace")
        lines = body.splitlines()

        cut = 0
        for i, ln in enumerate(lines[:14]):
            if "reference" in ln and ":" in ln:
                cut = i + 1
                break

        # Whitespace's program is invisible by construction.
        if name.lower() == "whitespace":
            raw = path.read_bytes()
            body_bytes = raw[cut:] if cut < len(raw) else raw
            rows.append(
                f"OK   {name:16} invisible program: "
                f"{body_bytes.count(32)} spaces + "
                f"{body_bytes.count(9)} tabs")
            continue

        prog = [l.strip() for l in lines[cut:]
                if l.strip() and "rainbow-pad" not in l]
        if not prog:
            rows.append(f"EMPTY{name:16} <no program after the banner>")
            problems += 1
        else:
            rows.append(f"OK   {name:16} " + " | ".join(prog[:3])[:66])

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(rows), encoding="utf-8", newline="\n")

    print(f"checked {len(seen)} languages -> {out}")
    print(f"empty after banner: {problems}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())