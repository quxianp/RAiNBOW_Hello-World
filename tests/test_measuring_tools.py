#!/usr/bin/env python3
"""The measuring tools must measure something.

Four tools were added today whose only purpose is to produce a number:
`coverage_figure.py`, `classify_placeholders.py`, `language_table.py` and
`hue_uniformity.py`. Each is worth having and none of them is worth much if it
silently reports zero, which is exactly what `hue_uniformity.py` did on its first
run -- it read `colour` where the manifest says `color`, found nothing, and
printed "0 chromatic of 694" with a straight face and a zero exit status.

A measurement that reports nothing and exits zero is the most dangerous kind of
broken tool, because it is indistinguishable from a clean result to anything that
looks at the exit code. So each one is asserted to return a non-degenerate
answer, and the sanity checks that would have caught it are written down:

  * the figure must be a plausible number, not zero;
  * the tool must name the field it reads, so a rename in the manifest is a
    visible failure rather than an empty table;
  * the counts must add up to the number of files, because a classifier that
    drops files is worse than one that mislabels them.

Skipped when the manifest is missing.
"""

import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "hello" / "manifest.json"


def _module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _ready():
    return MANIFEST.exists()


def test_coverage_figure_is_not_zero():
    if not _ready():
        return
    mod = _module("coverage_figure", ROOT / "scripts" / "coverage_figure.py")
    f = mod.figures()
    assert f["files"] == 7326, f"the manifest has {f['files']} files, not 7326"
    assert f["core"] == 694, f"the core layer has {f['core']} files, not 694"
    assert f["curated"] > 1000, (
        f"only {f['curated']} curated templates were found; the HELLO table has "
        f"about 1 600. A field rename in the generator would produce this.")
    assert f["programs"] == f["curated"] + f["inherit"], (
        "programs must be curated plus the inherit allowlist")
    assert f["core_pct"] > 90.0, (
        f"core coverage reads {f['core_pct']:.1f} %; it is 99.7 % and has been "
        f"for weeks. A tool reporting 0 % is reading the wrong field.")


def test_classification_accounts_for_every_file():
    if not _ready():
        return
    mod = _module("classify", ROOT / "scripts" / "classify_placeholders.py")
    data = mod.build()
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    total = len(man["files"])
    classified = data["without_program"]

    assert classified + (total - classified) == total, "arithmetic error"
    assert classified < total, (
        "every file is classified as having no program, which means the "
        "template table was read as empty")
    # The five kinds the generator has an admission sentence for, written out
    # here rather than imported. `KINDS` in the classifier maps Linguist's
    # *types* onto these, so importing it would compare the wrong namespace --
    # which is what the first version of this assertion did.
    EXPECTED_KINDS = {"esolang", "program", "document", "binary", "unknown"}

    assert set(data["counts"]) <= EXPECTED_KINDS, (
        f"the classifier produced kinds the generator has no sentence for: "
        f"{set(data['counts']) - EXPECTED_KINDS}")
    assert sum(data["counts"].values()) == classified, (
        "the per-kind counts do not sum to the number of classified files")


def test_classifier_reads_the_field_the_manifest_actually_uses():
    """The `colour`/`color` mistake, named so it cannot recur silently.

    The manifest key is `color`. A tool reading `colour` finds nothing, returns
    an empty result, and exits 0.
    """
    if not _ready():
        return
    mod = _module("classify", ROOT / "scripts" / "classify_placeholders.py")
    data = mod.build()
    kinds = set(data["counts"])
    assert len(kinds) >= 3, (
        f"only {len(kinds)} kind(s) produced: {kinds}. The classifier is "
        f"probably reading a field the manifest does not have.")


def test_hue_uniformity_reads_colour_and_finds_colours():
    if not _ready():
        return
    mod = _module("hue_uniformity", ROOT / "scripts" / "hue_uniformity.py")
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    core = [f for f in man["files"] if f["path"].startswith("hello/core/")]

    chromatic = 0
    for f in core:
        hsv = mod.parse_colour(f.get("color") or f.get("colour"))
        if hsv is not None and not mod.is_grey(hsv):
            chromatic += 1

    assert chromatic > 600, (
        f"only {chromatic} of {len(core)} core languages parsed as chromatic. "
        f"The manifest key is `color`, not `colour`; reading the wrong one "
        f"gives zero and still exits 0.")


def test_language_index_is_grouped_and_complete():
    if not _ready():
        return
    mod = _module("language_table", ROOT / "scripts" / "language_table.py")
    text = mod.build()

    for kind, title in mod.SECTION_TITLES.items():
        assert title.split(" (")[0] in text, f"section missing: {title}"

    rows = [l for l in text.splitlines() if l.startswith("| ") and l.count("|") == 4]
    assert len(rows) > 7000, (
        f"the index lists {len(rows)} rows; there are 7 326 files. A classifier "
        f"that drops files would produce a shorter table and still exit 0.")
    assert "**total**" in text