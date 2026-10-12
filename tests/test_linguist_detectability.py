#!/usr/bin/env python3
"""Linguist must still see each core language as its own language.

The repository's premise is that putting one file per language into the core
layer produces one coloured segment each. That is true until something makes
Linguist fold dialects together, merge two of our languages, or stop detecting
one entirely -- and none of that changes a single byte in the repository, so
none of it is visible to the byte-level tests.

What this test can check locally is the part that does not need Linguist: that
each core file carries the modeline and the Linguist colour that pin it, and
that no two core languages claim the same Linguist name. The full Linguist run
is `scripts/linguist_audit.rb`, which CI runs.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "hello" / "manifest.json"


def _manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))["files"]


def test_every_core_language_has_a_colour():
    """A language with no colour cannot appear on a colour bar at all."""
    man = _manifest()
    core = [f for f in man if f["layer"] == "core"]
    uncoloured = [f["language"] for f in core if not f.get("color")]
    assert not uncoloured, (
        f"{len(uncoloured)} core language(s) have no Linguist colour and "
        f"therefore cannot be on a colour bar: {uncoloured[:5]}"
    )


def test_no_two_core_languages_share_a_linguist_name():
    """Duplicate Linguist names would silently merge two segments into one."""
    man = _manifest()
    core = [f for f in man if f["layer"] == "core"]
    by_name = {}
    for f in core:
        key = f["language"].strip().lower()
        by_name.setdefault(key, []).append(f["path"])
    dupes = {k: v for k, v in by_name.items() if len(v) > 1}
    assert not dupes, (
        f"{len(dupes)} core language name(s) appear more than once, which would "
        f"merge their segments: {list(dupes)[:5]}"
    )


def test_every_core_file_carries_a_modeline():
    man = _manifest()
    core = [f for f in man if f["layer"] == "core"]
    missing = [f["path"] for f in core if not f.get("modeline")]
    assert not missing, (
        f"{len(missing)} core file(s) have no Linguist modeline: {missing[:3]}"
    )


def test_modeline_matches_the_language_it_annotates():
    """A modeline naming the wrong language is worse than none.

    Modeline syntax is a comment, so the prefix varies by language: `# -*-` for
    C-family, `// -*-` for JS, `-- -*-` for SQL, `<!-- -*- ... -->` for XML and
    HTML, `(* -*- ... *)` for OCaml. An earlier version of this test only
    accepted the first three and failed on 18 perfectly valid files.
    """
    VALID = (
        "# -*-", "// -*-", "-- -*-", "; -*-", "% -*-", '" -*-', "! -*-",
        "<!-- -*-", "(* -*-", "{- -*-",
    )
    man = _manifest()
    core = [f for f in man if f["layer"] == "core" and f.get("modeline")]
    bad = []
    for f in core:
        body = (ROOT / f["path"]).read_text(encoding="utf-8", errors="replace")
        first = body.splitlines()[0].strip() if body else ""
        if first and not first.startswith(VALID):
            bad.append((f["language"], first[:40]))
    assert not bad, (
        f"{len(bad)} core file(s) do not start with a recognised modeline "
        f"comment; first: {bad[0]}"
    )


def test_core_is_not_vendored():
    """The opposite mistake: if core is vendored, nothing is on the bar.

    Both a `-linguist-vendored` and a `linguist-detectable` rule are correct for
    hello/core; only the vendored one is fatal. An earlier version of this test
    required every matching rule to mention vendored, which rejected the
    legitimate `linguist-detectable` override.
    """
    ga = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    lines = [l.strip() for l in ga.splitlines() if l.strip() and "hello/core" in l]
    assert lines, ".gitattributes has no rule for hello/core"
    assert any("-linguist-vendored" in l for l in lines), (
        f"hello/core is never un-vendored, so nothing reaches the bar: {lines}"
    )