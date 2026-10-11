#!/usr/bin/env python3
"""Check the documentation cross-references resolve.

    python scripts/check_docs_links.py

Extends the README link checker to every markdown file in the repository, which
is where the drift actually accumulates: README.md is checked constantly, and
docs/*.md are checked never.

Caught on its first run by pointing at a file that did not exist yet, so the
check exists because it found a real problem immediately.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent

LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$", re.MULTILINE)

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".tmp"}


def norm_anchor(x: str) -> str:
    x = unquote(x).strip().lower().replace("_", "-")
    x = re.sub(r"[^\w\s-]", "", x, flags=re.UNICODE)
    x = re.sub(r"[\s-]+", "-", x)
    return x.strip("-")


def slugify(h: str) -> str:
    return norm_anchor(h)


def main() -> int:
    docs = [
        p for p in sorted(ROOT.rglob("*.md"))
        if not any(part in SKIP_DIRS for part in p.parts)
        and ".git" not in p.parts
    ]
    if not docs:
        print("no markdown files found", file=sys.stderr)
        return 1

    bad: list[str] = []
    checked = 0

    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        anchors = {slugify(h) for _, h in HEADING_RE.findall(text)}
        for raw in LINK_RE.findall(text):
            target = raw.strip()
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            checked += 1
            path, _, frag = target.partition("#")
            if path:
                # Relative links are resolved against the containing document,
                # not the repository root -- a doc in docs/ linking to
                # ARCHITECTURE.md means docs/ARCHITECTURE.md.
                resolved = (doc.parent / path).resolve()
                if not resolved.exists():
                    bad.append(f"{doc.relative_to(ROOT)} -> {target} "
                               f"(no such file: {resolved})")
                    continue
            if frag and norm_anchor(frag) not in anchors:
                bad.append(f"{doc.relative_to(ROOT)} -> {target} "
                           f"(no such heading in {path or 'this document'})")

    print(f"checked {checked} local links across {len(docs)} markdown files")
    for b in bad:
        print(f"  BROKEN {b}")
    if bad:
        print(f"\n{len(bad)} broken reference(s)")
        return 1
    print("all local references resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())