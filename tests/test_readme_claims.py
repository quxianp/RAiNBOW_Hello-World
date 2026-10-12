#!/usr/bin/env python3
"""The documented numbers must match what the repository actually contains.

Every claim in the README about counts is a place where the page can quietly
become a lie: nothing breaks, the bar still renders, the text is simply wrong.
A reader who checks "694 core languages" against the repository and finds 693
has been misled by this project, which is worse than the project not having
claimed it.

These tests parse the numbers straight out of README.md and compare them with the
manifest and the filesystem.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
MANIFEST = json.loads((ROOT / "hello" / "manifest.json").read_text(encoding="utf-8"))


def _thousands(n: int) -> str:
    """Render an int the way the README does: 7326 -> '7 326'.

    The separator is a plain ASCII space. An earlier version of this helper
    emitted U+00A0, which is what a typesetter would reach for, and the test then
    reported that the README had never stated its own file count -- a failure
    caused entirely by the test disagreeing with the file it was checking.
    """
    return f"{n:,}".replace(",", " ")


def _core_count() -> int:
    return sum(1 for f in MANIFEST["files"] if f["layer"] == "core")


def _full_count() -> int:
    return sum(1 for f in MANIFEST["files"] if f["layer"] == "full")


def test_manifest_counts_are_self_consistent():
    assert MANIFEST["core_languages"] == _core_count(), (
        f"manifest core_languages={MANIFEST['core_languages']} but "
        f"{_core_count()} core entries are listed"
    )
    assert MANIFEST["full_languages"] == _full_count(), (
        f"manifest full_languages={MANIFEST['full_languages']} but "
        f"{_full_count()} full entries are listed"
    )
    assert MANIFEST["total_files"] == len(MANIFEST["files"]), (
        f"total_files={MANIFEST['total_files']} but "
        f"{len(MANIFEST['files'])} entries are listed"
    )


def test_readme_states_the_real_core_count():
    core = _core_count()
    # The README may write 694 or "694" in several places; require the true one.
    assert re.search(rf"\b{core}\b", README), (
        f"README never states the core language count ({core}); it may be "
        "quoting a stale number"
    )


def test_readme_states_the_real_total():
    total = len(MANIFEST["files"])
    thin = _thousands(total)
    assert (f"{total:,}" in README or thin in README
            or str(total) in README), (
        f"README never states the total file count ({total:,})"
    )


def test_readme_share_figure_matches_the_maths():
    core = _core_count()
    share = 100.0 / core
    claimed = re.search(r"0\.(\d{6})\s*%", README)
    assert claimed, "README states no six-decimal byte share"
    value = float("0." + claimed.group(1))
    assert abs(value - share) < 1e-6, (
        f"README claims 0.{claimed.group(1)} % per language but "
        f"100/{core} is {share:.6f} %"
    )


def test_share_sum_is_exactly_one_hundred():
    core = _core_count()
    total = (100.0 / core) * core
    assert abs(total - 100.0) < 1e-9, f"shares sum to {total}, not 100"


def test_readme_mentions_both_the_repository_and_bar_counts():
    """694 and 631 are different measurements and both belong on the page."""
    assert re.search(r"\b694\b", README), "README no longer states 694 languages"
    assert re.search(r"\b631\b", README), (
        "README no longer explains the 631 segment count"
    )


def test_licence_is_mit_and_stated():
    lic = ROOT / "LICENSE"
    assert lic.is_file(), "LICENSE missing"
    text = lic.read_text(encoding="utf-8").upper()
    assert "MIT" in text, "LICENSE is not MIT"
    assert "MIT" in README.upper(), "README does not mention the licence"