#!/usr/bin/env python3
"""Find every figure quoted in the documentation that no longer matches.

Typed figures were the single most common defect in this repository's history.
Not wrong arithmetic -- wrong *stale* arithmetic. A commit message says "94
tests" when there are 95, a README says "1,739 programs" when there are 1,752,
and the number is true for exactly as long as nobody adds anything. E32 is the
entry in the ledger.

`scripts/coverage_figure.py` exists so that no figure is ever typed by hand.
That only helps the code; the prose is full of them, and prose does not run.

So this reads every markdown file, finds the phrases that make a claim about
this repository, resolves the claim against the thing that measures it, and
reports the ones that disagree. It is a report rather than a gate by default,
because "1,600 curated templates" is a deliberate round number and is not wrong
-- but `--strict` turns the disagreements into a non-zero exit for the files
that claim exactness.

The claims it understands:

    N tests                  the number tests/ defines
    N programs               scripts/coverage_figure.py
    N files                  the manifest
    N languages              scripts/language_table.py
    N%core / 99.7 %          the core share
    N commits                git

    python scripts/check_doc_figures.py
    python scripts/check_doc_figures.py --strict
    python scripts/check_doc_figures.py --verbose
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "hello" / "manifest.json"

_TRUTH: dict | None = None

# Fenced code blocks are quoted output, not claims; tables are tables; block
# quotes are quotations. None of them is what this tool is for.
FENCE = re.compile(r"^```.*?^```", re.S | re.M)
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
SKIP_LINE = re.compile(r"^\s*(?:\||>|#|`|[-*]\s|\d+\.\s)")

# README writes a thin space between thousands, so the digit pattern has to
# accept U+202F and U+00A0 as well as an ordinary space and a comma.
DIGITS = r"(\d[\d \u00a0\u202f,]*\d|\d)"


def _n(text: str) -> int:
    for ch in ("\u00a0", "\u202f", ",", " "):
        text = text.replace(ch, "")
    return int(text)


def _load(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def truth() -> dict:
    """Every claimable quantity, measured.

    Memoised. `truth()` reads the whole manifest through language_table.py,
    which parses 7 326 files, and two tests calling it turned a five-minute
    suite into a six-minute one. The quantities do not change while a process
    is running, so caching them is not a compromise.
    """
    global _TRUTH
    if _TRUTH is not None:
        return _TRUTH
    out: dict[str, int] = {}

    n = 0
    for t in sorted((ROOT / "tests").glob("test_*.py")):
        # a `def test_` is one test; the count is by definition, not by running
        # the suite, so it cannot be wrong about how many there are
        n += sum(1 for line in t.read_text(encoding="utf-8").splitlines()
                 if re.match(r"\s*def test_\w+\s*\(", line))
    out["tests"] = n

    cov = _load(ROOT / "scripts" / "coverage_figure.py", "coverage_figure")
    fig = cov.figures()
    for key in ("files", "core", "full", "curated", "programs", "inherit",
                "core_with_program", "full_with_program"):
        out[key] = fig[key]
    out["core_pct"] = round(fig["core_pct"])
    # A round number is a legitimate thing to write; this is what one rounds to.
    out["curated_hundred"] = round(fig["curated"], -2)
    out["core_hundred"] = round(fig["core"], -2)

    tbl = _load(ROOT / "scripts" / "language_table.py", "language_table")
    text = tbl.build()
    m = re.search(r"\*\*total\*\*\s*\|\s*(\d[\d,]*)", text)
    if m:
        out["languages"] = _n(m.group(1))

    # The encoder's settings, read out of the script rather than remembered.
    # record_demo.sh mentions max_colors twice -- once as a size to compare
    # against and once as the value passed to ffmpeg -- so the last occurrence
    # is the one that is actually used, and taking the first reported 96
    # colours for a file that encodes 128.
    rec = (ROOT / "scripts" / "record_demo.sh").read_text(encoding="utf-8")
    fps = re.findall(r"fps=(\d+)", rec)
    if fps:
        out["fps"] = int(fps[-1])
    cols = re.findall(r"max_colors=(\d+)", rec)
    if cols:
        out["max_colors"] = int(cols[-1])

    # Two claims are deliberately not resolved. "631 segments" is what Linguist
    # reports for this repository and lives in docs/WHY-631-NOT-694.md; it needs
    # the linguist gem and a clone, and hardcoding it here would make the check
    # agree with itself forever. The acceptance count is validate_delivery.py's
    # output, which would mean running it. Both are skipped rather than guessed --
    # a checker that agrees with itself is worse than one that says nothing.
    _TRUTH = out
    return out


# Each entry is (claim, pattern). The phrase matters as much as the noun: "694
# files in the core layer" is a claim about the core and "7 326 files" is a
# claim about the repository, and both are written the same way otherwise.
CLAIMS = [
    ("tests", re.compile(DIGITS + r"\s+tests?\b", re.I)),
    ("programs", re.compile(DIGITS + r"\s+(?:real\s+|curated\s+)?programs?\b", re.I)),
    ("commits", re.compile(DIGITS + r"\s+commits?\b", re.I)),
    ("placeholders", re.compile(DIGITS + r"\s+placeholders?\b", re.I)),
    ("core", re.compile(DIGITS + r"\s+core files?\b", re.I)),
    ("full", re.compile(DIGITS + r"\s+full files?\b", re.I)),
    ("core", re.compile(DIGITS + r"\s+core languages?\b", re.I)),
    ("languages", re.compile(DIGITS + r"\s+languages?\b", re.I)),
    ("curated", re.compile(DIGITS + r"\s+curated\b", re.I)),
    ("acceptance", re.compile(DIGITS + r"/\d+\s+acceptance", re.I)),
    ("fps", re.compile(DIGITS + r"\s*fps\b", re.I)),
    ("max_colors", re.compile(DIGITS + r"\s+colours?\b", re.I)),
    ("core_with_program", re.compile(DIGITS + r"\s+core files? now carry", re.I)),
    ("core_pct", re.compile(DIGITS + r"\s*%\s*of the core", re.I)),
]

# Claims the tool knows the shape of but cannot resolve. Listed so that a
# reader can see they were skipped on purpose rather than overlooked.
UNRESOLVED = ("segments", "acceptance")

# A round number is a deliberate approximation, not a stale figure: "about
# 1 600 curated templates" is true in the sense the sentence means.
EXACT_WORDS = re.compile(r"\b(?:about|around|roughly|nearly|over|under|at least|"
                         r"more than|fewer than|some|n\+|~|≈|exactly)\b", re.I)


def scan(path: pathlib.Path, known: dict) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    text = HTML_COMMENT.sub(" ", text)
    text = FENCE.sub(" ", text)

    try:
        rel = path.relative_to(ROOT).as_posix()
    except ValueError:
        # a probe file outside the repository: report it by name rather than
        # refusing to scan it, which is what makes it testable at all
        rel = path.name
    found = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if SKIP_LINE.match(line):
            continue
        for key, pattern in CLAIMS:
            for m in pattern.finditer(line):
                try:
                    said = _n(m.group(1))
                except ValueError:
                    continue
                actual = known.get(key)
                if actual is None:
                    continue
                context = line[max(0, m.start() - 45):m.end() + 25]
                found.append({
                    "file": rel, "line": lineno, "claim": key,
                    "said": said, "actual": actual,
                    "exact": said == actual,
                    "approximate": bool(EXACT_WORDS.search(context)),
                    "text": context.strip(),
                })
    return found


def git_commits() -> int | None:
    try:
        out = subprocess.run(["git", "-C", str(ROOT), "rev-list", "--count", "HEAD"],
                             capture_output=True, text=True, timeout=60)
        return int(out.stdout.strip()) if out.returncode == 0 else None
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero on any exact claim that disagrees")
    ap.add_argument("--include-changelog", action="store_true",
                    help="also check CHANGELOG.md, which records old figures")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    if not MANIFEST.exists():
        print("no manifest; run scripts/generate_all_hello.py first", file=sys.stderr)
        return 1

    known = truth()
    ncommits = git_commits()
    if ncommits is not None:
        known["commits"] = ncommits

    print("measured: " + ", ".join(f"{k}={v}" for k, v in sorted(known.items())))
    print()

    rows = []
    # A changelog records what was true, so its old figures are correct in
    # context. Checking them would report every entry ever written as stale,
    # which is the same as reporting none.
    files = ([p for p in sorted(ROOT.glob("*.md")) if p.name != "CHANGELOG.md"]
             + sorted((ROOT / "docs").rglob("*.md")))
    if args.include_changelog:
        files.append(ROOT / "CHANGELOG.md")
    for md in files:
        if md.exists():
            rows.extend(scan(md, known))

    stale = [r for r in rows if not r["exact"] and not r["approximate"]]
    if args.verbose:
        for r in rows:
            mark = "ok " if r["exact"] else ("~  " if r["approximate"] else "STALE")
            print(f"  {mark} {r['file']}:{r['line']:<4} {r['claim']:<10} "
                  f"said {r['said']}, is {r['actual']}   {r['text'][:60]}")
    else:
        for r in stale:
            print(f"  STALE {r['file']}:{r['line']:<4} {r['claim']:<10} "
                  f"said {r['said']}, is {r['actual']}")
            print(f"        {r['text'][:78]}")

    checked = len(rows)
    approx = sum(1 for r in rows if r["approximate"] and not r["exact"])
    print(f"\n{checked} figure(s) in the documentation, "
          f"{approx} approximate, {len(stale)} stale")
    if UNRESOLVED:
        print("not machine-checked: " + ", ".join(UNRESOLVED))
    if stale and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())