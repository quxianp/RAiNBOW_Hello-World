#!/usr/bin/env python3
"""Every placeholder's admission must match what it actually is.

`scripts/classify_placeholders.py` sorts the 6 000-odd program-less files into
five kinds, and `generate_all_hello.py` prints one of five sentences. Before this,
all of them printed the same sentence, and the two lists could disagree silently:
a file could claim to be an esoteric language while the classifier had decided it
was a binary format, and nothing would notice.

So this checks the join. For every file without a program:

  * the classifier's kind must have an admission text that appears in the file;
  * a file whose kind is `program` must *not* carry the esoteric sentence, even
    though both begin "no program here" -- otherwise the distinction the whole
    change was about would erode back into boilerplate;
  * the kind recorded in the file must match the kind in the JSON.

Skipped if the classification file is missing, which is the state of a partial
checkout.
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
CLASSES = ROOT / "data" / "placeholder_classes.json"
MANIFEST = ROOT / "hello" / "manifest.json"

# Kept in step with ADMISSION_KIND_TEXT in generate_all_hello.py. That duplication
# is deliberate and is what this test is for: it is a second opinion, not a
# re-export, and if the two ever diverge one of them is wrong.
EXPECTED_TEXT = {
    "esolang": "esoteric language",
    "program": "programming language",
    "document": "not a programming language",
    "binary": "a binary format",
    "unknown": "an index entry",
}

KINDS = set(EXPECTED_TEXT)


def _load():
    if not CLASSES.exists() or not MANIFEST.exists():
        return None, None
    classes = json.loads(CLASSES.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return classes, manifest


def test_every_placeholder_states_its_own_kind():
    classes, manifest = _load()
    if classes is None:
        return

    by_path = {f["path"]: f for f in classes["files"]}
    problems = []

    for f in manifest["files"]:
        if f.get("real_template"):
            continue
        rec = by_path.get(f["path"])
        if rec is None:
            problems.append(f"{f['path']}: not in placeholder_classes.json")
            continue

        head = "\n".join(
            (ROOT / f["path"]).read_text(encoding="utf-8", errors="replace")
            .splitlines()[:14])

        kind = rec.get("kind")
        expected = EXPECTED_TEXT.get(kind)
        if expected is None:
            problems.append(f"{f['path']}: unknown kind {kind!r}")
            continue
        if expected not in head:
            problems.append(
                f"{f['path']}: kind={kind} should say {expected!r}")
        # The file names its kind in the brackets; that must be the real one.
        if f"[kind={kind} " not in head and f"[kind={kind}]" not in head:
            problems.append(f"{f['path']}: does not name kind={kind}")

    assert not problems, (
        f"{len(problems)} placeholder(s) disagree with the classifier:\n  "
        + "\n  ".join(problems[:8]))


def test_a_program_kind_never_claims_to_be_an_esolang():
    """The distinction the whole change rests on.

    Both sentences start "no program here", so a generator regression would be
    easy to miss. It is the one thing here worth checking twice.
    """
    classes, manifest = _load()
    if classes is None:
        return

    by_path = {f["path"]: f for f in classes["files"]}
    wrong = []
    for f in manifest["files"]:
        if f.get("real_template"):
            continue
        rec = by_path.get(f["path"])
        if not rec or rec.get("kind") != "program":
            continue
        head = "\n".join(
            (ROOT / f["path"]).read_text(encoding="utf-8", errors="replace")
            .splitlines()[:14])
        if EXPECTED_TEXT["esolang"] in head:
            wrong.append(f["language"])

    assert not wrong, (
        f"{len(wrong)} real programming language(s) are being described as "
        f"esoteric: {wrong[:5]}")


def test_every_kind_in_the_classifier_has_a_sentence():
    classes, _ = _load()
    if classes is None:
        return
    kinds = set(classes.get("counts", {}))
    missing = kinds - KINDS
    assert not missing, (
        f"the classifier reports kind(s) {sorted(missing)} that the generator "
        f"has no admission sentence for; such a file would print the generic "
        f"fallback instead of saying what it is")


def test_the_classification_covers_every_program_less_file():
    classes, manifest = _load()
    if classes is None:
        return
    classified = {f["path"] for f in classes["files"]}
    unclassified = [
        f["path"] for f in manifest["files"]
        if not f.get("real_template") and f["path"] not in classified
    ]
    assert not unclassified, (
        f"{len(unclassified)} placeholder(s) are missing from "
        f"data/placeholder_classes.json: {unclassified[:5]}. Re-run "
        f"scripts/classify_placeholders.py.")
