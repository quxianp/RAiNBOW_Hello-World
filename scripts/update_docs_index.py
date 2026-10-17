#!/usr/bin/env python3
"""Regenerate docs/README.md as an index of every document.

    python scripts/update_docs_index.py
    python scripts/update_docs_index.py --check

    README.md                the project page
    CHANGELOG.md             what changed, and every defect found
    CONTRIBUTING.md          how to work on this, including adding a template
    CODE_OF_CONDUCT.md       expectations for participants
    SECURITY.md              what in this repository is inert data
    docs/ARCHITECTURE.md     how the bar is controlled by byte count
    docs/HOW-FILES-GET-THEIR-CONTENT.md  the five kinds of hello/ file, and how
                                         to add a program to one
    docs/WHY-631-NOT-694.md  why 694 files produce 631 segments
    docs/FAQ.md              the questions that actually get asked
    logs/ERRORS.log          the defect ledger, E1-E29
    logs/DECISIONS.md        decisions and their reasoning

It exists because the deep documents were scattered: linked from the README's
layout table, from CONTRIBUTING, and from each other, with no single place that
lists them. A reader arriving from a search result had no way to know that
docs/WHY-631-NOT-694.md answered their question.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "README.md"

START = "<!-- DOCS_INDEX_START -->"
END = "<!-- DOCS_INDEX_END -->"

# path -> (title, one-line description), in reading order.
DOCS = [
    ("../README.md", "The project page",
     "The rainbow bar, the demo, and how to read everything else."),
    ("ARCHITECTURE.md", "Architecture",
     "The bar is controlled by byte count: equal file size means equal share, "
     "and hue ordering makes that visible. Also the 694-to-631 gap and the "
     "known limits."),
    ("WHY-631-NOT-694.md", "Why 631 segments, not 694",
     "The single most asked question, with the measurements that settle it. "
     "Linguist merges dialects into parents; the 7 HTML-family files become one "
     "`HTML` segment of 7 x 2048 bytes, which is why it reads 1.0116 %."),
    ("HOW-FILES-GET-THEIR-CONTENT.md", "How a file in hello/ gets its content",
     "The five kinds of file in `hello/` and why each needs different content "
     "\u2014 a program, an esoteric admission, an index admission, a document, a "
     "binary header \u2014 plus how to add one, and what \"real\" means here."),
    ("DEMO.md", "The demo",
     "How `assets/hello-world.gif` is recorded, why a gate refuses to publish a "
     "static take, and the three tools to reach for when a recording looks "
     "wrong."),
    ("ENCODINGS.md", "The files that are not programs",
     "The seventy files holding encodings of the greeting rather than a program: "
     "checksummed records, real archives, image formats, and why each is not a "
     "`print`."),
    ("../data/LANGUAGES.md", "Language index",
     "All 7 326 files, grouped by what they contain rather than by directory. "
     "Generated; `scripts/language_table.py --check` fails if it is stale."),
    ("../docs/languages/FORTRAN-AND-COBOL.md", "Fortran and COBOL families",
     "Nine Fortran entries, five of which a single inherited program would get "
     "wrong: fixed form puts the statement number in columns 1-6 and the verb "
     "in column 7, and free form dropped all of it."),
    ("../docs/languages/ASSEMBLY.md", "Assembly families",
     "Eighty-odd entries, each with its own syscall convention -- and that "
     "convention is the program. Plus the object formats, three of which carry "
     "checksums."),
    ("../docs/languages/PROVERS-AND-SOLVERS.md",
     "Provers, model checkers and solvers",
     "Three families that look alike on the language bar and none of which can "
     "print. Coq gets a definition, NuSMV an INVARSPEC, MiniZinc an output "
     "declaration, and CSP a file that says it has neither."),
    ("../docs/languages/SQL-AND-QUERIES.md", "SQL and query languages",
     "Fourteen entries where the keyword is sometimes SELECT, sometimes RETURN "
     "and sometimes PRINT, and two of which cannot print at all."),
    ("../docs/languages/CONFIG-FILES.md", "Build, package and CI configuration",
     "The declaration-form exemption, why it keys on the extension, and why the "
     "guard has to run in both directions."),
    ("../docs/languages/BLOCK-LANGUAGES.md", "Visual and block languages",
     "Seventy entries whose programs are dragged and whose project files are "
     "JSON. Writing Python into a Scratch project passes every check here and "
     "Scratch cannot open it."),
    ("../docs/languages/LISP.md", "The Lisp families",
     "Ten entries whose entire difference is whether the language appends the "
     "newline itself."),
    ("../docs/languages/GOLF.md", "Golf and concatenative languages",
     "Sixty entries whose canonical program is one to fifteen characters, in "
     "three shapes -- and Actually, whose whole program is fifteen + "
     "characters."),
    ("../docs/languages/TERMINALS.md", "Terminal output and control languages",
     "Twenty-odd entries that do not print characters -- they move the cursor "
     "and set attributes. Worked out: the SGR codes are additive bit flags, "
     "38;2;r;g;b is the whole of truecolour, and that is the escape run.sh "
     "draws the rainbow with."),
    ("../docs/languages/SHELLS.md", "The shell family",
     "Fifteen entries, one word 'shell' in most of them, and the distinction "
     "that matters most: a shell script is not a program in the shell. print "
     "is a ksh and zsh builtin and does not exist in bash, so copying one "
     "line between three entries produces one that works and two that fail."),
    ("../docs/languages/MARKUP-AND-DOCUMENTS.md",
     "Markup, prose and documents",
     "Four shapes of document, and the one that is not what it looks like: a "
     "binary format gains a greeting by putting it in the field the format "
     "itself accepts."),
    ("FAQ.md", "Frequently asked questions",
     "Why the bar looks grey, why COBOL is missing, which of 694 and 631 is "
     "right, and whether all the files actually run."),
    ("../CONTRIBUTING.md", "Contributing",
     "How to add a language or a Hello World template, and what CI silently "
     "reverts."),
    ("../CHANGELOG.md", "Changelog",
     "Every notable change and every defect found, with the reason each was "
     "hard to see."),
    ("../SECURITY.md", "Security",
     "What in this repository is inert data rather than code. Most of it."),
    ("../CODE_OF_CONDUCT.md", "Code of conduct",
     "Contributor Covenant 2.1."),
    ("../logs/ERRORS.log", "Defect ledger",
     "Thirty-two defects, each with the symptom, the cause, and why nothing "
     "caught it. The most useful document here."),
    ("../logs/DECISIONS.md", "Decisions",
     "Choices made and the reasoning behind them, including the ones that were "
     "later reversed."),
    ("../logs/AGENT_STATE.md", "Working notes",
     "Current numbers, the commands that matter, and the environment hazards "
     "that have actually cost time."),
]

HEADER = """# Documentation

Every document in this repository, and what it is for. The deep-dive pages
answer questions that the README raises but cannot fit; the ledgers record what
went wrong, which is usually more instructive than what went right.
"""


def build() -> str:
    rows = [f"| Document | What it answers |", "|---|---|"]
    for path, title, desc in DOCS:
        p = ROOT / "docs" / path if not path.startswith("..") else ROOT / path[3:]
        if not p.is_file():
            rows.append(f"| {title} | *(missing: {path})* |")
            continue
        href = path if path.startswith("..") else path
        rows.append(f"| [{title}]({href}) | {desc} |")
    return f"{START}\n" + "\n".join(rows) + f"\n{END}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    existing = OUT.read_text(encoding="utf-8") if OUT.is_file() else ""
    has_markers = START in existing and END in existing

    if not existing:
        # First run: create the file with a heading and the block.
        existing = HEADER + "\n\n"

    desired_block = build()
    m = re.search(re.escape(START) + r".*?" + re.escape(END),
                  existing, re.DOTALL) if has_markers else None
    current = m.group(0) if m else ""

    if current == desired_block and OUT.is_file():
        print("docs index already up to date")
        return 0

    if args.check:
        print("docs index is out of date"
              + ("" if has_markers else " (no markers present)"),
              file=sys.stderr)
        return 1

    if m:
        new = existing[:m.start()] + desired_block + existing[m.end():]
    else:
        new = existing.rstrip() + "\n\n" + desired_block + "\n"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(new, encoding="utf-8", newline="\n")
    print(f"updated {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())