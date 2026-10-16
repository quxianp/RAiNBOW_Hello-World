#!/usr/bin/env python3
"""The generated artefacts must be current.

Two files in this repository are generated and committed: `data/LANGUAGES.md`,
the index of all 7 326 files, and `data/placeholder_classes.json`, the
classification that decides what each program-less file says.

Both were stale within an hour of being written, for the same reason: they are
produced by running something, and running something is easy to forget when the
thing that changed was a different script. The classification went stale because
a template batch landed; the index would have gone stale for the same reason.

They are checked rather than regenerated, so CI fails on drift instead of
silently fixing it. A generated file that nobody regenerates is worse than none:
it describes a repository that no longer exists, with the authority of something
current.

Skipped when the inputs are missing.
"""

import importlib.util
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _run(name: str, path: pathlib.Path, *args: str) -> subprocess.CompletedProcess:
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return subprocess.run([sys.executable, str(path), "--check", *args],
                          capture_output=True, text=True, cwd=str(ROOT))


def test_language_index_is_current():
    tool = ROOT / "scripts" / "language_table.py"
    if not tool.exists() or not (ROOT / "hello" / "manifest.json").exists():
        return
    proc = _run("language_table", tool)
    assert proc.returncode == 0, (
        f"data/LANGUAGES.md is stale:\n{proc.stdout}{proc.stderr}\n"
        f"run: python scripts/language_table.py")


def test_placeholder_classification_is_current():
    tool = ROOT / "scripts" / "classify_placeholders.py"
    if not tool.exists() or not (ROOT / "hello" / "manifest.json").exists():
        return
    proc = _run("classify_placeholders", tool)
    assert proc.returncode == 0, (
        f"data/placeholder_classes.json is stale:\n{proc.stdout}{proc.stderr}\n"
        f"run: python scripts/classify_placeholders.py")
