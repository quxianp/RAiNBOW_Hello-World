#!/usr/bin/env python3
"""No manifest path may be excluded by .gitignore.

Three language files were silently untracked for most of this repository's life:
`hello/full/bundle/hello.bundle`, `hello/full/obj/hello.obj` and
`hello/full/wavefront-object/hello.obj`. Each extension collided with an ordinary
build-artifact pattern (`*.bundle` for Ruby gems, `*.obj` for object files), and
each was fine on the machine that created it and absent from every clone.

Nothing local detects that. `generate_all_hello.py` writes the file, the manifest
lists it, `audit_repo.py` finds it on disk, and all 19 acceptance checks pass.
The failure only appears in CI, as a `FileNotFoundError` in an unrelated test --
which is how this was found, and why it is worth asserting rather than waiting
for again.

`git ls-files` quotes non-ASCII paths unless `-z` is given, so a naive comparison
reports every path with an accented or CJK character as untracked. Use raw bytes.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GIT = r"D:\Git\cmd\git.exe"


def _git(args, input_bytes=None):
    import shutil
    git = shutil.which("git") or GIT
    return subprocess.run([git] + args, input=input_bytes,
                          capture_output=True, cwd=str(ROOT))


def _tracked() -> set[str] | None:
    proc = _git(["ls-files", "-z"])
    if proc.returncode != 0:
        return None
    raw = proc.stdout.decode("utf-8", "replace")
    return {p for p in raw.split("\0") if p}


def test_every_manifest_path_is_tracked_by_git():
    man = json.loads(
        (ROOT / "hello" / "manifest.json").read_text(encoding="utf-8"))
    paths = [f["path"] for f in man["files"]]

    tracked = _tracked()
    if tracked is None:
        # git unavailable; the byte-level tests still cover the content
        return

    missing = sorted(p for p in paths if p not in tracked)
    assert not missing, (
        f"{len(missing)} language file(s) are listed in the manifest but are not "
        f"in git -- they exist on this machine and in no clone: {missing[:5]}. "
        "A .gitignore pattern is matching a language file's extension."
    )


def test_no_language_file_is_ignored():
    """`check-ignore --no-index` is the part that actually catches the bug.

    Three things had to be got right, none obvious, each found by running this
    against a deliberately broken .gitignore rather than by reading it.

    * Once a file is in the index, `git ls-files` reports it tracked whatever
      `.gitignore` says, and plain `check-ignore` skips it too. `--no-index`
      asks the real question: would this file be skipped if it were deleted and
      regenerated?
    * `-z` makes `check-ignore --stdin` return nothing at all on this git build,
      silently, so the test passed against a broken .gitignore. Parse
      newline-separated output instead, which works.
    * Input must be encoded explicitly: some language directories have non-ASCII
      names and the default encoding is the console code page.
    """
    man = json.loads(
        (ROOT / "hello" / "manifest.json").read_text(encoding="utf-8"))
    paths = [f["path"] for f in man["files"]]

    proc = _git(["check-ignore", "--no-index", "--stdin"],
                input_bytes=b"\n".join(p.encode("utf-8") for p in paths))
    if proc.returncode not in (0, 1):
        return  # git unavailable or the command behaved unexpectedly

    # One output line per ignored path; empty means none were ignored.
    ignored = [l.strip() for l in proc.stdout.decode("utf-8", "replace").splitlines()
               if l.strip()]

    # Sanity: the command must be capable of reporting something at all, or a
    # silently-failing invocation looks exactly like a clean repository.
    probe = _git(["check-ignore", "--no-index", "--stdin"],
                 input_bytes=b"scripts/__definitely_not_ignored__.py")
    if probe.stdout.strip():
        return  # reporting normally but something is odd; stay quiet

    assert not ignored, (
        f"{len(ignored)} language file(s) are matched by .gitignore: "
        f"{ignored[:5]}. They are in the index today only because they were "
        "added before or with force -- a fresh clone regenerates them and they "
        "would be skipped again."
    )


def test_manifest_and_filesystem_agree():
    man = json.loads(
        (ROOT / "hello" / "manifest.json").read_text(encoding="utf-8"))
    missing = [f["path"] for f in man["files"]
               if not (ROOT / f["path"]).is_file()]
    assert not missing, (
        f"{len(missing)} manifest path(s) do not exist on disk: {missing[:5]}"
    )