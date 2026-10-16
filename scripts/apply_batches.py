#!/usr/bin/env python3
"""Apply several template batches, one commit each.

`scripts/add_templates.py` handles one batch and does the work. This handles the
loop around it: read a batch, apply it, commit it with its own message, move to
the next. A day of template work is thirty or forty batches, and doing that by
hand is a lot of ceremony per batch for no benefit -- each one still gets its own
commit, with its own message, and its own diff.

A batch is a Python file defining `NEW`, because these programs are full of
quotes, backslashes and newlines and hand-escaping them into JSON is a reliable
way to produce a file that will not parse. The driver converts each dict to JSON
itself.

    python scripts/apply_batches.py 03 04 05     # .tmp/batchNN.{py,msg}
    python scripts/apply_batches.py --list
    python scripts/apply_batches.py --dry-run 03

Layout expected, relative to .tmp/:

    batchNN.py    NEW = {"Fortran 77": "...", ...}
    batchNN.msg   the commit message

`--dry-run` validates every batch and reports what each would add, without
writing a file or creating a commit.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PY = sys.executable
GIT = None
BATCH_DIR = ROOT / ".tmp"

IDENTITY = [
    "-c", "user.name=quxianp",
    "-c", "user.email=quxianp@users.noreply.github.com",
]


def git_path() -> str:
    import shutil
    return shutil.which("git") or r"D:\Git\cmd\git.exe"


def sh(*args, timeout=3600):
    return subprocess.run([git_path(), *args], cwd=str(ROOT),
                          capture_output=True, text=True, timeout=timeout)


def convert(src: pathlib.Path, dest: pathlib.Path) -> tuple[bool, str]:
    """Run a batch module and write its NEW dict as JSON."""
    code = (
        "import importlib.util,json,sys;"
        "s=importlib.util.spec_from_file_location('b',sys.argv[1]);"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        "open(sys.argv[2],'w',encoding='utf-8',newline='\\n')"
        ".write(json.dumps(m.NEW,ensure_ascii=False,indent=1))"
    )
    proc = subprocess.run([PY, "-c", code, str(src), str(dest)],
                          capture_output=True, text=True, timeout=300)
    return proc.returncode == 0, (proc.stderr or "").strip()


def discover() -> list[str]:
    return sorted(p.stem for p in BATCH_DIR.glob("batch*.py")
                  if (BATCH_DIR / f"{p.stem}.msg").exists())


def apply_one(name: str, dry_run: bool) -> str:
    src = BATCH_DIR / f"{name}.py"
    js = BATCH_DIR / f"{name}.json"
    msg = BATCH_DIR / f"{name}.msg"

    if not src.exists():
        return f"{name}: no batch source"
    if not msg.exists():
        return f"{name}: no commit message"

    ok, err = convert(src, js)
    if not ok:
        return f"{name}: could not convert: {err.splitlines()[-1] if err else '?'}"

    flags = ["--from", str(js), "--dry-run" if dry_run else ""]
    cmd = [PY, str(ROOT / "scripts" / "add_templates.py"),
           "--from", str(js)]
    if dry_run:
        cmd.append("--dry-run")
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                          timeout=3600)
    out = (proc.stdout + proc.stderr).strip().splitlines()
    summary = [l.strip() for l in out if l.strip().startswith(
        ("accepted", "duplicates", "rejected"))]
    header = f"{name}: " + ", ".join(summary)
    if dry_run:
        return header
    if proc.returncode != 0:
        tail = [l for l in out if l.strip()][-1:]
        return f"{header} -> FAILED: {tail[0] if tail else ''}"

    sh("add", "-A", "scripts", "hello", "logs")
    staged = sh("diff", "--cached", "--name-only").stdout.split()
    if not staged:
        return f"{name}: nothing staged, skipping"

    proc = sh(*IDENTITY, "commit", "-F", str(msg))
    if proc.returncode != 0:
        return f"{name}: commit failed: {proc.stdout.strip()[-120:]}"
    files = len(sh("show", "--name-only", "--format=", "HEAD").stdout.split())
    return f"{name}: committed {files} file(s)"


def main() -> int:
    global GIT
    GIT = git_path()

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="*", help="batch stems, e.g. 03 04 05")
    ap.add_argument("--list", action="store_true", help="list discoverable batches")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.list:
        names = discover()
        if not names:
            print(f"no batches found in {BATCH_DIR}")
            return 0
        for n in names:
            print(f"  {n}")
        return 0

    names = args.names or discover()
    if not names:
        print(f"no batches in {BATCH_DIR}", file=sys.stderr)
        return 1

    results = []
    for name in names:
        results.append(apply_one(name, args.dry_run))
        print(results[-1], flush=True)

    if not args.dry_run:
        failures = [r for r in results if "FAIL" in r or "failed" in r]
        print(f"\n{len(results) - len(failures)}/{len(results)} batches committed")
        return 1 if failures else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
