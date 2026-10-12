#!/usr/bin/env python3
"""Languages whose extension is ambiguous must not be guessed.

`Rez` is a script language for Apple's resource compiler. Its extension is `.r`,
which Linguist also assigns to R. So `HELLO["rez"]` is either an R script
(`cat("Hello World!")`) or a Rez resource script, and the file itself carries no
further evidence: same extension, different language.

The tie was broken wrongly once -- the R script went in, and `check_templates.py`
caught it on the next run, which is how the entry ended up removed rather than
fixed. Re-adding it will fail the same way.

This test records the decision so the next attempt reads it rather than
rediscovering it.
"""

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Extension -> languages Linguist assigns it to. When there is more than one,
# a template keyed on the extension alone is a guess.
AMBIGUOUS = {".r": {"r", "rez"}}


def _load():
    spec = importlib.util.spec_from_file_location(
        "gen_hello", ROOT / "scripts" / "generate_all_hello.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gen_hello"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_rez_has_no_template_and_that_is_deliberate():
    mod = _load()
    assert "rez" not in mod.HELLO, (
        "Rez has a template again. `.r` is shared with R, and the previous "
        "attempt put `cat(\"Hello World!\")` -- an R script -- into a file "
        "labelled Rez. Either find a genuinely Rez-specific answer or leave the "
        "honest placeholder."
    )


def test_rez_file_says_it_has_no_template():
    man = json.loads(
        (ROOT / "hello" / "manifest.json").read_text(encoding="utf-8"))
    entry = next(f for f in man["files"] if f["language"] == "Rez")
    assert not entry.get("real_template"), (
        "the manifest claims Rez has a curated template; see "
        "test_rez_has_no_template_and_that_is_deliberate"
    )
    body = (ROOT / entry["path"]).read_text(encoding="utf-8", errors="replace")
    assert "admission" in body and "No curated Hello World" in body, (
        "the Rez placeholder does not say it is a placeholder; a reader "
        "opening the file should not think it is a working program"
    )


def test_no_core_language_inherits_only_on_an_ambiguous_extension():
    """Guards the general rule, not just the one instance.

    Two languages sharing an extension is normal and fine -- Rez and R both use
    `.r`, and both ship a file. What is not fine is deriving one's program from
    the other, which is what the extension-based heuristic did.

    So the assertion is about templates, not about which languages exist: on an
    ambiguous extension, a language may claim a curated template only if that
    template is keyed on the language's own name.
    """
    mod = _load()
    man = json.loads(
        (ROOT / "hello" / "manifest.json").read_text(encoding="utf-8"))
    core = [f for f in man["files"] if f["layer"] == "core"]

    for ext, langs in AMBIGUOUS.items():
        using = [f for f in core if (f.get("extension") or "") == ext]
        if len(using) < 2:
            continue
        for f in using:
            key = f["language"].lower().strip()
            if key not in langs:
                continue  # this language is not part of the ambiguity
            if key in mod.HELLO:
                # It has a template keyed on its own name, which is the
                # correct outcome -- R's cat() is an R script because the key
                # is "r", not because the extension is ".r".
                assert mod.HELLO[key] != mod.HELLO.get(
                    sorted(langs - {key})[0], None), (
                    f"{f['language']} shares a template with the other {ext} "
                    "language; they must have distinct programs"
                )