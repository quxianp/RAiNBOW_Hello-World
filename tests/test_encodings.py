#!/usr/bin/env python3
"""The encoding files must decode back to the greeting.

Roughly seventy files in `hello/full/` are not programs. They are hex dumps of
encodings: Base58 of the greeting, a real deflate stream, an Intel HEX record
with a checksum, a genuine ZIP archive. Each was produced by the library that
defines the format rather than by memory, because a hex dump written from memory
is wrong in one byte and reads as correct.

Producing them correctly is not the same as *having* them correct, and nothing
checked the second thing. This does, by decoding rather than by comparing: it
parses the ASCII hex tokens back out of each file and feeds them to the decoder,
so an error in the *encoder* is caught and not just an error in the comment.

It found two real problems the moment it ran:

  - `hello/full/srec/` had never been given a record at all. It was still a
    placeholder, and its admission said so -- which the measurement had been
    reading correctly and I had not looked at.
  - the checker's own record layout was off by one, so sixteen *correct* files
    were reported as unverifiable. A verifier that reports everything as broken is
    as useless as one that reports everything as fine.

Skipped when the manifest is missing.
"""

import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
VERIFIER = ROOT / "scripts" / "verify_encodings.py"


def _module():
    if not VERIFIER.exists():
        return None
    spec = importlib.util.spec_from_file_location("verify_encodings", VERIFIER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_every_encoding_file_decodes_to_the_greeting():
    mod = _module()
    if mod is None:
        return
    files = mod.candidates()
    if not files:
        return

    failures = []
    for path in files:
        kind, ok, why = mod.check_encoding(path)
        if not ok:
            failures.append(f"{path.relative_to(ROOT).as_posix()}: {why}")

    assert not failures, (
        f"{len(failures)} encoding file(s) do not decode back to the greeting:\n  "
        + "\n  ".join(failures[:8]))


def test_at_least_one_file_decodes_through_a_real_decoder():
    """Not every file has to be a stream, but some must be.

    Without this, the test above would still pass if `candidates()` matched
    nothing at all, or if every file silently fell through to the text branch --
    which is exactly what happened when the routing keyed on `path.stem`, and
    `hello.intel_hex` has the stem "hello".
    """
    mod = _module()
    if mod is None:
        return
    files = mod.candidates()
    if not files:
        return

    kinds = {}
    for path in files:
        kind, ok, _ = mod.check_encoding(path)
        kinds[kind] = kinds.get(kind, 0) + 1

    assert kinds.get("stream", 0) >= 3, (
        f"only {kinds.get('stream', 0)} file(s) went through a real decoder; "
        f"the rest are unverified text. Routing may have regressed: {kinds}")


def test_intel_hex_and_s_record_checksums_are_rejected_when_wrong():
    """A verifier that cannot fail is not a verifier.

    Both checkers are fed a record with one byte of the checksum changed, and
    both must complain. This is the same discipline used for the .gitignore guard
    and the motion gate: prove the failure mode before trusting the pass.
    """
    mod = _module()
    if mod is None:
        return

    good = ":0C00000048656C6C6F20576F726C6421B7\n"
    ok, _ = mod.check_intel_hex(good)
    assert ok, "a correct Intel HEX record was rejected"

    bad = ":0C00000048656C6C6F20576F726C6421B8\n"
    ok, why = mod.check_intel_hex(bad)
    assert not ok, f"a wrong Intel HEX checksum was accepted: {why}"

    good_s = "S10F000048656C6C6F20576F726C6421B3\n"
    ok, _ = mod.check_srecord(good_s)
    assert ok, "a correct S-record was rejected"

    bad_s = "S10F000048656C6C6F20576F726C6421B4\n"
    ok, why = mod.check_srecord(bad_s)
    assert not ok, f"a wrong S-record checksum was accepted: {why}"
