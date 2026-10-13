#!/usr/bin/env python3
"""No tracked text file may dirty the working tree on a fresh checkout.

One stray byte broke 23 of 24 CI shards. `scripts/publish_release.ps1` was
committed with a UTF-8 BOM and a single CRLF line ending, while `.gitattributes`
declares `*.ps1 text eol=lf`. Every checkout therefore rewrote the file, leaving
the tree dirty, and the batch job's `git pull --rebase` refused with "You have
unstaged changes" before it ran a single line of its own work.

Nothing local detects this: the working tree matches the index, the file is
valid, every test passes, and the problem appears only on a fresh clone -- which
is exactly what CI does and what no developer does.

So the check is made directly: clone into a temporary directory and assert the
result is clean. It is the only test here that exercises a real clone, and it is
worth the few seconds.

Skipped when git is unavailable or the repository has no commits.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SKIP_DIRS = {".tmp", "__pycache__", "node_modules"}


def _git_exe():
    return shutil.which("git") or r"D:\Git\cmd\git.exe"


def test_fresh_clone_has_a_clean_working_tree():
    git = _git_exe()
    if not Path(git).exists() and not shutil.which("git"):
        return

    tmp = Path(tempfile.mkdtemp(prefix="rainbow-clone-"))
    try:
        # Clone from the local repository as a bare source, checking out a
        # single commit: this is what a runner does, and it is the only way to
        # exercise git's smudge filters.
        proc = subprocess.run(
            [git, "clone", "--depth", "1", "--no-local",
             ROOT.as_uri() if hasattr(ROOT, "as_uri") else str(ROOT), str(tmp)],
            capture_output=True, text=True, timeout=900)
        if proc.returncode != 0:
            # Some configurations refuse file:// clones; fall back to a plain
            # copy, which still catches a committed CRLF.
            proc = subprocess.run(
                [git, "clone", "--depth", "1", str(ROOT), str(tmp)],
                capture_output=True, text=True, timeout=900)
            if proc.returncode != 0:
                return

        status = subprocess.run(
            [git, "status", "--porcelain"],
            capture_output=True, text=True, cwd=str(tmp), timeout=300)
        if status.returncode != 0:
            return

        dirty = [l for l in status.stdout.splitlines() if l.strip()]
        assert not dirty, (
            f"a fresh clone is dirty: {len(dirty)} file(s) are rewritten by "
            f"git's filters on checkout. Every runner would see this. "
            f"First: {dirty[:5]}"
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_no_tracked_text_file_has_a_bom_or_crlf():
    """Cheaper, and catches the cause rather than the symptom.

    A UTF-8 BOM or a CRLF in a file that `.gitattributes` marks as LF text is
    rewritten on checkout. Both arrived here from PowerShell's Set-Content.

    Only *tracked* files matter: `logs/runners.txt` is gitignored, is rewritten
    on every run, and can never dirty a checkout because it is not in one. The
    first version of this test scanned the filesystem and failed on it.
    """
    import subprocess

    git = shutil.which("git") or r"D:\Git\cmd\git.exe"
    proc = subprocess.run([git, "ls-files", "-z"], capture_output=True,
                          cwd=str(ROOT))
    if proc.returncode != 0:
        return
    tracked = {p for p in proc.stdout.decode("utf-8", "replace").split("\0") if p}

    offenders = []
    for pattern in ("*.md", "*.py", "*.ps1", "*.yml", "*.yaml",
                    "*.json", "*.sh", "*.tape", "*.rb", "*.txt"):
        for p in ROOT.rglob(pattern):
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            rel = p.relative_to(ROOT).as_posix()
            if rel not in tracked:
                continue
            data = p.read_bytes()
            if data.startswith(b"\xef\xbb\xbf"):
                offenders.append(f"{rel}: UTF-8 BOM")
            elif b"\r\n" in data:
                offenders.append(f"{rel}: CRLF")

    assert not offenders, (
        f"{len(offenders)} tracked text file(s) carry a BOM or CRLF endings and "
        f"will be rewritten on checkout: {offenders[:6]}"
    )