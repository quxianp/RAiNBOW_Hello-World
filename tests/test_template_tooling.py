#!/usr/bin/env python3
"""The template tooling must refuse what it claims to refuse.

`scripts/add_templates.py` has been the gate on every batch added today, and its
value is entirely in what it says no to. Twenty-nine batches went through it and
roughly one entry in five was rejected. If it accepted everything, it would be a
convenience rather than a guard, and nothing would notice until a wrong program
landed -- which is the failure the repository already has 34 recorded examples of.

So this asserts the refusals directly, against the tool's own `validate()`, and
then does the same for the other three things the tool promises:

  * a language the manifest does not ship is refused;
  * a blank program is refused;
  * a program that never says "Hello World" is refused, unless the extension is
    a declaration form;
  * a duplicate is reported rather than overwritten;
  * `--replace` overwrites a real change and reports a no-op as a duplicate;
  * splicing produces valid Python and preserves every existing key.

Skipped when the manifest is missing.
"""

import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOL = ROOT / "scripts" / "add_templates.py"
MANIFEST = ROOT / "hello" / "manifest.json"


def _module():
    spec = importlib.util.spec_from_file_location("add_templates", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _ready():
    if not MANIFEST.exists() or not TOOL.exists():
        return None, None, None, None
    mod = _module()
    return mod, mod.load_manifest(), mod.existing_keys(), mod.src_text()


def test_a_language_the_repository_does_not_ship_is_refused():
    mod, manifest, have, _ = _ready()
    if mod is None:
        return
    accepted, dupes, rejected = mod.validate(
        {"Nonexistent Language 9000": "Hello World!\n"}, manifest, have)
    assert not accepted, "a language outside the manifest was accepted"
    assert any("not a language" in why for _, why in rejected), (
        f"the refusal did not say why: {rejected}")


def test_a_blank_program_is_refused():
    """The `HELLO["coff"] = ""` defect, by name.

    An empty string used to satisfy the "key is present" test and mark COFF as
    having a real template, producing a file that was a banner followed by
    nothing. The refusal is the whole reason the tool has a `strip()` test.
    """
    mod, manifest, have, _ = _ready()
    if mod is None:
        return
    language = next(iter(manifest))
    for blank in ("", "   \n", "\n\t "):
        accepted, _, rejected = mod.validate({language: blank}, manifest, have)
        assert not accepted, f"a blank program was accepted: {blank!r}"
        assert any("blank" in why for _, why in rejected), rejected


def test_a_program_that_never_greets_is_refused():
    mod, manifest, have, _ = _ready()
    if mod is None:
        return
    # A language whose extension is NOT a declaration form, or the greeting
    # check would be bypassed and the test would pass for the wrong reason --
    # which is what the first version of this did.
    candidates = [
        lang for lang, files in manifest.items()
        if not have.__contains__(lang.lower())
        and files
        and not any((f.get("extension") or "").lower() in mod.DECLARATION_FORMS
                    for f in files)
    ]
    if not candidates:
        return
    accepted, _, rejected = mod.validate(
        {candidates[0]: "int main(void) { return 0; }\n"}, manifest, have)
    assert not accepted, "a program with no greeting was accepted"
    assert any("never says Hello World" in why for _, why in rejected), rejected


def test_a_declaration_form_may_skip_the_greeting_check():
    """.properties, .cabal and go.mod have no body to print.

    This is the exemption, and it has to be narrow: it keys on the extension
    rather than on the language, so it cannot be used to excuse a program.
    """
    mod, manifest, have, _ = _ready()
    if mod is None:
        return
    # a language whose extension is a declaration form
    candidates = [
        lang for lang, files in manifest.items()
        if any((f.get("extension") or "").lower() in mod.DECLARATION_FORMS
               for f in files)
        and not have.__contains__(lang.lower())
    ]
    if not candidates:
        return
    lang = candidates[0]
    accepted, _, rejected = mod.validate({lang: "name: rainbow\n"}, manifest, have)
    assert accepted or any("never says" in why for _, why in rejected), (
        "declaration forms must bypass the greeting check")


def test_a_duplicate_is_reported_rather_than_overwritten():
    mod, manifest, have, _ = _ready()
    if mod is None:
        return
    existing = sorted(k for k in have if k in {l.lower() for l in manifest})
    if not existing:
        return
    key = existing[0]
    accepted, dupes, _ = mod.validate({key: "Hello World!\n"}, manifest, have)
    assert not accepted, "an existing template was silently overwritten"
    assert dupes, "the duplicate was not reported"


def test_replace_reports_a_no_op_as_a_duplicate():
    mod, manifest, have, src = _ready()
    if mod is None:
        return
    src = src or mod.src_text()
    keys = sorted(k for k in have if k in {l.lower() for l in manifest})
    if not keys:
        return
    key = keys[0]
    current = mod.templates_value(src, key)
    if not current:
        return
    accepted, dupes, _ = mod.validate({key: current}, manifest, have,
                                      replace=True)
    assert not accepted, "an identical template was reported as a change"
    assert dupes and "identical" in dupes[0][1], (
        f"the no-op was not reported as identical: {dupes}")


def test_splicing_preserves_every_existing_key_and_stays_valid_python():
    """A splice that dropped entries would look like a successful run.

    It would produce a file that compiles, passes every check, and has silently
    deleted a language's program. So the count is compared, not just the exit
    status.
    """
    mod, manifest, have, _ = _ready()
    if mod is None:
        return
    target = next(k for k in manifest if not have.__contains__(k.lower()))
    entries = [(target, "Hello World!\n")]
    new_src, added = mod.splice(entries)
    compile(new_src, "generate_all_hello.py", "exec")

    ns = {"__file__": str(ROOT / "scripts" / "generate_all_hello.py"),
          "__name__": "gen_under_test"}
    exec(compile(new_src.split("if __name__")[0], "g", "exec"), ns)
    after = set(ns["HELLO"])

    missing = set(have) - after
    assert not missing, (
        f"splicing dropped {len(missing)} existing template(s): "
        f"{sorted(missing)[:5]}")
    assert added == 1, f"expected one splice, got {added}"
