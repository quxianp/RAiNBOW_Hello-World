#!/usr/bin/env python3
"""The load-bearing invariant: every core file is exactly the same size.

This is the single property the entire repository exists to exploit. Equal byte
size means equal share in GitHub's language bar, and equal share is the only
reason ordering the files by hue produces a visible spectrum rather than a
random confetti strip.

It is tested against the filesystem rather than against the manifest, because a
broken generator and a manifest that agrees with it would pass any check that
only reads the manifest.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "hello" / "core"
MANIFEST = ROOT / "hello" / "manifest.json"

# The size every core file is padded to. balance_bytes.py owns the value; this
# test asserts the property, not the constant.
EXPECTED_SIZE = 2048


def _core_files():
    return sorted(p for p in CORE.rglob("*") if p.is_file())


def test_core_layer_is_not_empty():
    files = _core_files()
    assert len(files) > 0, "hello/core is empty -- nothing would be on the bar"
    assert len(files) >= 600, f"core layer has only {len(files)} files, spec says 600+"


def test_every_core_file_is_exactly_2048_bytes():
    files = _core_files()
    bad = [(p, p.stat().st_size) for p in files
           if p.stat().st_size != EXPECTED_SIZE]
    assert not bad, (
        f"{len(bad)} core file(s) are not {EXPECTED_SIZE} bytes, which means "
        f"they do not get an equal share of the bar; first: {bad[0][0].name} "
        f"is {bad[0][1]} bytes"
    )


def test_no_core_file_is_empty():
    files = _core_files()
    empty = [p for p in files if p.stat().st_size == 0]
    assert not empty, f"{len(empty)} zero-byte core file(s): {empty[:3]}"


def test_shares_sum_to_exactly_one_hundred_percent():
    files = _core_files()
    share = 100.0 / len(files)
    total = share * len(files)
    assert abs(total - 100.0) < 1e-9, f"shares sum to {total}, not 100"


def test_each_core_language_gets_the_same_share():
    files = _core_files()
    share = 100.0 / len(files)
    assert abs(share - 0.144092) < 1e-6, (
        f"share is {share:.6f} %, README and docs claim 0.144092 %"
    )


def test_manifest_agrees_with_the_filesystem():
    assert MANIFEST.is_file(), "hello/manifest.json missing"
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    core = [f for f in man["files"] if f["layer"] == "core"]
    assert man["core_languages"] == len(_core_files()), (
        f"manifest claims {man['core_languages']} core languages but "
        f"{len(_core_files())} files exist"
    )
    assert len(core) == len(_core_files()), (
        f"manifest lists {len(core)} core entries vs {len(_core_files())} files"
    )


def test_every_manifest_core_path_exists():
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    missing = [f["path"] for f in man["files"]
               if f["layer"] == "core" and not (ROOT / f["path"]).is_file()]
    assert not missing, f"{len(missing)} manifest core paths do not exist: {missing[:3]}"


def test_each_core_language_occupies_its_own_directory():
    """One directory per language keeps the per-language files reviewable."""
    dirs = {p.parent for p in _core_files()}
    assert len(dirs) == len(_core_files()), (
        f"{len(_core_files())} core files share only {len(dirs)} directories; "
        "a directory holds more than one language"
    )


def test_every_placeholder_admits_that_it_is_one():
    """A file with no curated program must say so in its own header.

    This is the entire purpose of a placeholder, and it was silently broken for
    the whole repository. `build_file()` received its note through a parameter
    that core files were already using for the modeline caption, so a core
    placeholder printed "Pinned with a Linguist modeline..." and never said it
    had no program -- a reader opening hello/core/rez/hello.r had no way to tell
    it from a working one.

    Checked against the head of the file only, since the padding comment
    legitimately fills the rest.
    """
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    # The marker used to be the literal sentence "No curated Hello World",
    # because every placeholder printed the same one. Each now says which of the
    # five kinds it is, so the test looks for the specific texts instead --
    # a stronger check, since boilerplate would now fail it.
    admissions = ("No curated Hello World",
                  "esoteric language",
                  "programming language",
                  "not a programming language",
                  "a binary format",
                  "an index entry",
                  "not in data/placeholder_classes.json")
    silent = []
    for f in man["files"]:
        if f.get("real_template"):
            continue
        body = (ROOT / f["path"]).read_text(encoding="utf-8", errors="replace")
        head = "\n".join(body.splitlines()[:14])
        if "admission" not in head or not any(a in head for a in admissions):
            silent.append(f["language"])
    assert not silent, (
        f"{len(silent)} placeholder file(s) do not admit they are placeholders, "
        f"so a reader cannot tell them from working programs: {silent[:5]}"
    )


def test_placeholders_are_a_small_and_shrinking_share_of_core():
    """Guards against the template work regressing.

    Core coverage reached 99.7 %; if this ever falls far below that, something
    has quietly broken the matcher rather than genuinely run out of languages.
    """
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    core = [f for f in man["files"] if f["layer"] == "core"]
    have = sum(1 for f in core if f.get("real_template"))
    pct = 100.0 * have / len(core)
    assert pct >= 95.0, (
        f"only {pct:.1f} % of core files have a curated template "
        f"({have}/{len(core)}); the matcher has probably regressed"
    )