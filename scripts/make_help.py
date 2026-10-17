#!/usr/bin/env python3
"""Print the targets in a Makefile, with their `## help` comments.

A Makefile that documents itself is the only documentation a new contributor
is guaranteed to find, because `make help` is the first thing anybody tries.
The usual recipe is a `grep -E '^[a-z-]+:.*?## '` piped into `awk`, which has
two problems on the machine this repository is developed on: grep and awk are
not on PATH, and a plain `@echo` per line comes back wrapped in literal double
quotes when make hands the recipe to a shell that is not Bash.

Neither is a good reason for `make help` not to work, so this reads the
Makefile and prints the target list itself -- same job, standard library only,
and identical output on every platform.

    python scripts/make_help.py [Makefile]

It also warns about targets whose `##` comment is empty or missing, because a
target listed in `.PHONY` and absent from the help is worse than one that was
never written.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# `target: deps  ## text`. The comment is found by searching the whole line
# rather than by trying to split the line at the first `#`: a recipe line's
# own `#` is not the target's comment, but a target's is always the first one
# in the line, and a line without a `##` simply is not documented.
HELP = re.compile(r"##+\s*(\S.*?)\s*$")
TARGET = re.compile(r"^([A-Za-z0-9_][A-Za-z0-9_.-]*)\s*:(?!=)")

# .PHONY declares which targets exist even when no file of that name does.
PHONY = re.compile(r"^\.PHONY\s*:?=\s*(.*)$")


def targets(text: str) -> list[tuple[str, str]]:
    out = []
    for line in text.splitlines():
        m = TARGET.match(line)
        if not m:
            continue
        # A line inside a recipe may start with a tab; those are never targets.
        if line[0] in "\t ":
            continue
        h = HELP.search(line)
        if h:
            out.append((m.group(1), h.group(1)))
    return out


def declared_phony(text: str) -> list[str]:
    names: list[str] = []
    for m in PHONY.finditer(text):
        names.extend(m.group(1).split())
    return names


def main() -> int:
    path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "Makefile"
    if not path.is_file():
        print(f"no {path}", file=sys.stderr)
        return 1

    text = path.read_text(encoding="utf-8")
    documented = targets(text)
    if not documented:
        print("no documented targets found", file=sys.stderr)
        return 1

    width = max(len(n) for n, _ in documented)
    print(f"RAiNBOW_Hello-World -- {path.name}\n")
    for name, help_text in documented:
        print(f"  {name:<{width}}  {help_text}")

    undocumented = [n for n in declared_phony(text)
                    if n not in {n for n, _ in documented}]
    if undocumented:
        print()
        for n in undocumented:
            print(f"  {n} is in .PHONY but has no ## comment", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())