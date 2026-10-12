#!/usr/bin/env python3
"""Guard the curated-template flag against false positives.

    python scripts/check_templates.py
    python scripts/check_templates.py --verbose

The generator used to decide "does this language have a real Hello World?" by
matching on the first word of its name or on its file extension. That produced
34 confidently wrong files out of 156 matches -- JASS and Objective-J inherited a
shell `echo`, Go Module inherited an entire Go program, and "Binary Brainfuck"
inherited the word "Binary". Nothing failed, because every file was still valid
in *some* language; the file just was not the language it claimed to be.

Worse, the manifest under-reported: it tested `name in HELLO` exactly, while the
generator applied four fuzzy strategies. The manifest said 279 languages had
real templates when 372 did, and said nothing at all about the 34 wrong ones.

This test pins both halves:
  1. inheritance is only ever via the explicit INHERIT table, never a heuristic;
  2. the manifest's real_template flag agrees with program_for(), which is what
     decides the file contents.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "scripts" / "generate_all_hello.py"
MANIFEST = ROOT / "hello" / "manifest.json"

# Languages whose template must NOT come from a different language. Each entry
# names the language that a heuristic would have wrongly supplied.
MUST_NOT_INHERIT = {
    # NOTE: four entries were removed from this list after their templates were
    # replaced with correct ones. The assertion "must not have a real template"
    # is only right while a language is inheriting someone else's program; it
    # becomes wrong the moment that language gets its own:
    #   Java Properties   -> a real .properties file is key=value
    #   Java Server Pages -> real JSP is <% out.println(...) %>
    #   Java Template Engine -> a .jte is FreeMarker, not a Java class
    #   Cabal Config      -> a cabal file declares metadata; it has no program
    #                        body, so "name: rainbow" IS the complete answer
    "Rez": "R via .r",
    # NOTE: Rez stays here deliberately even though it now has a template. Its
    # extension is `.r`, which is shared with R, and the right program depends
    # entirely on which language the repository means -- `cat("Hello World!")`
    # is an R script, not a Rez resource script. Resolving that ambiguity
    # requires knowing what Rez is used for here, not guessing.
    # Rocq Prover was listed here because it inherited a V-lang program from
    # the shared `.v` extension. It now has its own genuine Coq-family
    # template, so the assertion no longer applies -- see MUST_INHERIT.
    "Binary Brainfuck": "the word 'Binary'",
    "WebAssembly Binary": "WAT text",
    # KFramework and WebAssembly Interface Type moved to MUST_INHERIT once each
    # gained its own template; see there.
    "Nim Task": "a Nim program",
    "CSS Selectors": "a CSS rule",
}

# Languages that legitimately share a parent's syntax. If these ever lose their
# template, the INHERIT table has been damaged.
MUST_INHERIT = [
    "Bash Shell", "C++ AMP", "Idris 2", "Ruby MRI", "Brainfuck extended",
    "C preprocessor", "Lean 4", "C#", "Python", "Elm HTML",
    # Languages that gained their own template instead of inheriting one.
    "Jasmin", "Ada", "COBOL", "ALGOL", "ABAP", "Prolog", "ANTLR", "AMPL",
    "Dylan", "Eiffel", "Mercury", "Pike", "Oz", "Puppet", "Gherkin",
    "Fortran", "Fortran Free Form", "Pascal", "AutoHotkey", "AppleScript",
    "AutoIt", "Hack", "Hy", "ActionScript", "AngelScript", "Futhark", "GAP",
    "Scala", "Solidity", "VHDL", "Verilog", "Vala", "GraphQL",
    # JASS and Objective-J moved here from MUST_NOT_INHERIT: each used to
    # inherit a shell `echo` from the shared `.j` extension, and each now has
    # its own genuine program instead.
    "JASS", "Objective-J",
    # Languages whose "program" is a declaration rather than an executable body.
    # A cabal file, a properties file and a package manifest are fully described
    # by their fields; there is no program to put in them.
    "Cabal Config", "Java Server Pages",
    # The Go family, same reason and same history: each inherited a whole Go
    # program while its real format is `module x` / `go 1.21`, a module
    # list, a hash line, or `{{ }}`.
    "Go Module", "Go Workspace", "Go Checksums", "Go Template",
    "Java Template Engine",
    # Rocq Prover: inherited a V-lang program via `.v` until it gained its own.
    "Rocq Prover",
    # LLVM TableGen: inherited LLVM IR via a shared family name; TableGen is a
    # record-definition language and now has its own template.
    "LLVM TableGen",
    # KFramework inherited kdb+/k from a shared `.k`; WebAssembly Interface
    # Type inherited a whole WebAssembly module from `webassembly`. Each is
    # a distinct language with its own now.
    "KFramework", "WebAssembly Interface Type",
    # HiveQL inherited kdb+/q from a shared `.q`; it is Hive's own query
    # language and now carries a SQL comment, which is what HiveQL uses.
    "HiveQL",
]


def load_generator():
    spec = importlib.util.spec_from_file_location("gen_hello", GEN)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gen_hello"] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    mod = load_generator()
    fails: list[str] = []

    # ---- 1. the flag must agree with what program_for() actually returns ----
    if not MANIFEST.is_file():
        print(f"error: {MANIFEST} missing -- run generate_all_hello.py first",
              file=sys.stderr)
        return 1
    files = json.loads(MANIFEST.read_text(encoding="utf-8"))["files"]

    disagree = 0
    for f in files:
        recorded = bool(f.get("real_template"))
        _, actual = mod.program_for(f["language"], f.get("extension") or "")
        if recorded != actual:
            disagree += 1
            if disagree <= 10:
                fails.append(
                    f"{f['language']}: manifest says real_template="
                    f"{recorded} but program_for() returns {actual}")
    if disagree:
        print(f"  [FAIL] {disagree} file(s) disagree with program_for()")
    else:
        n = sum(1 for f in files if f.get("real_template"))
        print(f"  [ok  ] manifest agrees with program_for() for all "
              f"{len(files)} files ({n} curated)")

    # ---- 2. known false inherits must stay honest -------------------------
    by_name = {f["language"]: f for f in files}
    for lang, why in MUST_NOT_INHERIT.items():
        f = by_name.get(lang)
        if f is None:
            if args.verbose:
                print(f"  [skip] {lang} not in manifest")
            continue
        if f.get("real_template"):
            fails.append(f"{lang} claims a real template but must not ({why})")
            print(f"  [FAIL] {lang} inherits {why}")
        elif args.verbose:
            print(f"  [ok  ] {lang} correctly has no template")

    # ---- 3. known true inherits must survive ------------------------------
    for lang in MUST_INHERIT:
        f = by_name.get(lang)
        if f is None:
            if args.verbose:
                print(f"  [skip] {lang} not in manifest")
            continue
        if not f.get("real_template"):
            fails.append(f"{lang} lost its template; INHERIT table damaged")
            print(f"  [FAIL] {lang} should have a template")
        elif args.verbose:
            print(f"  [ok  ] {lang} keeps its template")

    # ---- 4. every INHERIT target must actually exist in HELLO -------------
    dangling = [f"{k} -> {v}" for k, v in mod.INHERIT.items() if v not in mod.HELLO]
    if dangling:
        for d in dangling:
            fails.append(f"INHERIT points at a missing template: {d}")
            print(f"  [FAIL] dangling INHERIT entry {d}")
    else:
        print(f"  [ok  ] all {len(mod.INHERIT)} INHERIT targets exist in HELLO")

    # ---- 5. no heuristic may have crept back ------------------------------
    # Compare against the code only. An earlier version of this guard matched
    # the explanatory comment that names the old heuristics, so it failed on the
    # very documentation of the bug it was checking for.
    src = GEN.read_text(encoding="utf-8")
    i = src.index("def program_for")
    j = src.index("def default_program")
    body = src[i:j]
    code = "\n".join(ln for ln in body.splitlines()
                     if not ln.lstrip().startswith("#"))
    for banned in ('split(" ")[0]', "stem in HELLO", "ext.lstrip"):
        if banned in code:
            fails.append(f"program_for() uses heuristic {banned!r} again")
            print(f"  [FAIL] heuristic {banned!r} has returned to program_for()")
        else:
            print(f"  [ok  ] no {banned!r} heuristic in program_for()")
    if "INHERIT.get" not in code:
        fails.append("program_for() does not consult INHERIT")
        print("  [FAIL] program_for() no longer consults INHERIT")
    else:
        print("  [ok  ] program_for() consults the INHERIT table")

    print()
    if fails:
        print(f"{len(fails)} problem(s):")
        for f in fails[:20]:
            print(f"  - {f}")
        return 1
    print("TEMPLATE CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())