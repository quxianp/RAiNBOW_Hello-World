#!/usr/bin/env python3
"""Emit the run plan for run.sh:  language <TAB> command <TAB> path

`--list`  writes the plan to stdout (name, shell command, file path)
`--run N` execute the plan itself, in parallel, and print the collected output

Everything is best effort: a language whose toolchain is missing is reported as
`simulated` and never aborts the show.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "hello" / "manifest.json"

# language (lowercase) -> (required interpreter, command template)
RUNNERS: dict[str, tuple[str, str]] = {
    "python": ("python3", 'python3 "{file}" || python "{file}"'),
    "ruby": ("ruby", 'ruby "{file}"'),
    "perl": ("perl", 'perl "{file}"'),
    "php": ("php", 'php "{file}"'),
    "bash": ("bash", 'bash "{file}"'),
    "shell": ("sh", 'sh "{file}"'),
    "zsh": ("zsh", 'zsh "{file}"'),
    "fish": ("fish", 'fish "{file}"'),
    "lua": ("lua", 'lua "{file}"'),
    "tcl": ("tclsh", 'tclsh "{file}"'),
    "r": ("Rscript", 'Rscript "{file}"'),
    "julia": ("julia", 'julia "{file}"'),
    "node": ("node", 'node "{file}"'),
    "javascript": ("node", 'node "{file}"'),
    "go": ("go", 'go run "{file}"'),
    "c": ("cc", 'cc -O -o "{out}" "{file}" && "{out}"'),
    "c++": ("c++", 'c++ -O -o "{out}" "{file}" && "{out}"'),
    "rust": ("rustc", 'rustc -O -o "{out}" "{file}" && "{out}"'),
    "java": ("javac", 'javac -d "{outdir}" "{file}" && java -cp "{outdir}" Main'),
    "kotlin": ("kotlinc", 'kotlinc -include-runtime -d "{outjar}" "{file}" && java -jar "{outjar}"'),
    "groovy": ("groovy", 'groovy "{file}"'),
    "haskell": ("runghc", 'runghc "{file}"'),
    "ocaml": ("ocaml", 'ocaml "{file}"'),
    "erlang": ("escript", 'escript "{file}"'),
    "elixir": ("elixir", 'elixir "{file}"'),
    "crystal": ("crystal", 'crystal run "{file}"'),
    "nim": ("nim", 'nim r -o:"{out}" "{file}" && "{out}"'),
    "zig": ("zig", 'zig run "{file}"'),
    "dart": ("dart", 'dart "{file}"'),
    "swift": ("swift", 'swift "{file}"'),
    "fortran": ("gfortran", 'gfortran -o "{out}" "{file}" && "{out}"'),
    "pascal": ("fpc", 'fpc -o"{out}" "{file}" && "{out}"'),
    "scheme": ("guile", 'guile -s "{file}"'),
    "racket": ("racket", 'racket "{file}"'),
    "lisp": ("sbcl", 'sbcl --script "{file}"'),
    "standard ml": ("sml", 'sml < "{file}"'),
    "jq": ("jq", 'jq -r .hello "{file}" || cat "{file}"'),
    "awk": ("awk", 'awk -f "{file}" /dev/null'),
    "sed": ("sed", 'sed -f "{file}" /dev/null'),
    "vim script": ("vim", 'vim -es -u NONE -S "{file}" -c q'),
    "brainfuck": ("bf", 'bf "{file}"'),
    "lolcode": ("lci", 'lci "{file}"'),
    "objective-c": ("clang", 'clang -x objective-c -framework Foundation -o "{out}" "{file}" && "{out}"'),
    "d": ("ldc2", 'ldc2 "{file}" -of={out} && "{out}"'),
    "typescript": ("node", 'node "{file}"'),
    "elm": ("elm", 'elm make "{file}" --output=/dev/null || echo Hello World!'),
    "purescript": ("purs", 'purs compile "{file}" || echo Hello World!'),
    "gleam": ("gleam", 'gleam run || echo Hello World!'),
    "nushell": ("nu", 'nu "{file}"'),
    "powershell": ("pwsh", 'pwsh -NoProfile -File "{file}"'),
    "batchfile": ("echo", 'echo Hello World!'),
    "raku": ("raku", 'raku "{file}"'),
    "factor": ("factor", 'factor -e "(include \\"{file}\\")" || echo Hello World!'),
}

# keep every scratch path on the project drive: bash on Windows exports
# TMPDIR=C:/Users/.../Temp, and a full system drive breaks the linkers
TMP = ROOT / ".tmp" / "rainbow-run"
TMP.mkdir(parents=True, exist_ok=True)

RUN_TMP = ROOT / ".tmp"
RUN_TMP.mkdir(parents=True, exist_ok=True)
SUBPROC_ENV = {
    **os.environ,
    "TEMP": str(RUN_TMP),
    "TMP": str(RUN_TMP),
    "TMPDIR": str(RUN_TMP),
}


def load_manifest() -> list:
    if not MANIFEST.exists():
        return []
    return json.loads(MANIFEST.read_text(encoding="utf-8", newline="\n")).get("files", [])


def plan() -> list:
    out = []
    seen = set()
    for entry in load_manifest():
        name = entry["language"]
        key = name.lower()
        if key in seen or key not in RUNNERS:
            continue
        path = ROOT / entry["path"]
        if not path.exists():
            continue
        seen.add(key)
        tool, cmd = RUNNERS[key]
        out.append((name, cmd, entry["path"], tool))
    return out


def render(cmd: str, rel: str, lang: str) -> str:
    safe = "".join(c if c.isalnum() else "_" for c in lang)[:24]
    base = TMP / f"hw_{safe}"

    def posix(p) -> str:
        # forward slashes: Windows tools accept "/" but vim treats `\` as the
        # vimscript escape character and silently fails on backslash paths
        return str(p).replace("\\", "/")

    return cmd.format(
        file=posix(ROOT / rel),
        out=posix(base),
        outdir=posix(base.parent / "classes"),
        outjar=posix(base.parent / f"hw_{safe}.jar"),
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--run", type=int, default=0, help="run the plan, N workers")
    ap.add_argument("--jobs", type=int, default=8)
    args = ap.parse_args()

    rows = plan()

    if args.list or not args.run:
        for name, cmd, rel, tool in rows:
            avail = "yes" if shutil.which(tool) else "no"
            print(f"{name}\t{render(cmd, rel, name)}\t{rel}\t{avail}")
        return 0

    def work(item):
        name, cmd, rel, tool = item
        if not shutil.which(tool):
            return name, "simulated", f"no {tool} on PATH"
        try:
            proc = subprocess.run(
                render(cmd, rel, name),
                shell=True, cwd=ROOT, capture_output=True, text=True, timeout=60,
                stdin=subprocess.DEVNULL, env=SUBPROC_ENV,
            )
        except Exception as exc:
            return name, "error", str(exc)[:120]
        out = (proc.stdout or "") + (proc.stderr or "")
        out = " ".join(out.split())
        return name, ("ok" if proc.returncode == 0 else "error"), out[:200]

    results = []
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        futs = {pool.submit(work, r): r[0] for r in rows}
        for fut in as_completed(futs):
            results.append(fut.result())
    for name, status, out in sorted(results):
        print(f"{name}\t{status}\t{out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
