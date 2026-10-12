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

# Directories that are not part of the repository's own content.
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".tmp", ".venv", "venv"}


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


def test_no_markdown_file_contains_mojibake():
    """Catch a README written through a legacy code page.

    This happened for real: a commit edited README.md with PowerShell's
    `Set-Content -Encoding UTF8`, which round-tripped the file through the
    console's active code page and turned every emoji into CJK-looking mojibake.
    Two headings lost their emoji entirely, which silently broke three
    table-of-contents anchors.

    The signature is specific and reliable: mojibake of a 4-byte UTF-8 sequence
    read as a double-byte code page yields characters in the CJK or Cyrillic
    blocks, which no README in this repository legitimately contains.
    """
    import unicodedata

    bad = []
    for p in sorted(ROOT.rglob("*.md")):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        rel = p.relative_to(ROOT)
        if "\ufffd" in text:
            bad.append(f"{rel} contains U+FFFD")
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for ch in line:
                code = ord(ch)
                if code < 0x250:
                    continue
                name = unicodedata.name(ch, "")
                if any(k in name for k in ("CJK", "HIRAGANA", "KATAKANA",
                                           "HANGUL", "CYRILLIC", "ARABIC",
                                           "HEBREW", "DEVANAGARI")):
                    bad.append(f"{rel}:{i} has {name!r} where ASCII or emoji "
                               f"belongs")
                    break
    assert not bad, "mojibake detected:\n  " + "\n  ".join(bad[:10])


def test_readme_sections_have_emoji_matching_the_contents_strip():
    """The TOC promised nine emoji; eight headings had none.

    Both halves have to agree, so check them against each other rather than
    against a hand-maintained list.
    """
    import re
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    # Match the link cell, not the line: the contents is a four-column table, so
    # one physical line carries four separate entries and counting lines
    # undercounts by a factor of four.
    toc_cells = re.findall(r"([^\|]*\[([^\]]*)\]\(#[^)]+\)[^\|]*)", text)
    headings = re.findall(r"^## (.+)$", text, flags=re.MULTILINE)

    def has_emoji(s: str) -> bool:
        # Emoji and dingbats sit in high Unicode blocks and are not
        # alphanumeric in the "word" sense. An earlier version tested
        # `not c.isalnum()`, which is True for nearly every emoji -- str.isalnum
        # follows the Unicode AL category, and so do symbols -- so the check
        # found zero emoji on a page that is covered in them.
        for c in s:
            cp = ord(c)
            if (0x1F000 <= cp <= 0x1FAFF      # emoji blocks
                    or 0x2600 <= cp <= 0x27BF   # misc symbols + dingbats
                    or cp in (0x203C, 0x2049, 0x2122, 0x2139, 0xFE0F)):
                return True
        return False

    emoji_toc = [t for t, _ in toc_cells if has_emoji(t)]
    assert len(emoji_toc) >= 8, (
        f"only {len(emoji_toc)} of {len(toc_cells)} contents entries carry an "
        "emoji; the page lost its section decoration"
    )
    plain_headings = [h for h in headings if not has_emoji(h)]
    assert len(plain_headings) <= 2, (
        f"{len(plain_headings)} section headings have no emoji while the "
        f"contents strip advertises them: {plain_headings}"
    )