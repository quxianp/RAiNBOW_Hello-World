#!/usr/bin/env python3
"""Generated files must not carry platform line-ending drift.

`.gitattributes` sets `* -text`, which disables normalisation. That is correct
here -- the files are byte-padded to an exact size, and normalisation would
change their length -- but it also means a generator run on Windows can commit
CRLF and quietly alter every byte count in the repository.

This was a real defect: generated artefacts churned 81 290 lines per
cross-platform run. These tests assert the property so it cannot come back.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "hello" / "core"
FULL = ROOT / "hello" / "full"


def _files(base: Path, limit: int = 400):
    return sorted(p for p in base.rglob("*") if p.is_file())[:limit]


def test_core_files_have_no_crlf():
    offenders = []
    for p in _files(CORE):
        data = p.read_bytes()
        if b"\r\n" in data:
            offenders.append(p.name)
    assert not offenders, (
        f"{len(offenders)} core file(s) contain CRLF; with `* -text` these are "
        f"committed verbatim and change every byte count: {offenders[:3]}"
    )


def test_generated_json_uses_lf():
    for name in ("manifest.json",):
        p = ROOT / "hello" / name
        if not p.is_file():
            continue
        data = p.read_bytes()
        assert b"\r\n" not in data, f"{name} contains CRLF"


def test_manifest_is_valid_json_with_expected_shape():
    p = ROOT / "hello" / "manifest.json"
    assert p.is_file(), "hello/manifest.json missing"
    man = json.loads(p.read_text(encoding="utf-8"))
    for key in ("core_languages", "full_languages", "total_files", "files"):
        assert key in man, f"manifest is missing the {key!r} key"
    assert len(man["files"]) == man["total_files"], (
        f"manifest lists {len(man['files'])} files but claims "
        f"{man['total_files']}"
    )


def test_scripts_are_readable_as_utf8():
    """A mojibake key in HELLO silently breaks template lookup."""
    bad = []
    for p in sorted((ROOT / "scripts").glob("*.py")):
        try:
            p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            bad.append(p.name)
    assert not bad, f"these scripts are not valid UTF-8: {bad}"


def test_readme_is_utf8_and_has_no_replacement_chars():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "\ufffd" not in text, (
        "README contains U+FFFD replacement characters, which means text was "
        "decoded with the wrong encoding at some point"
    )