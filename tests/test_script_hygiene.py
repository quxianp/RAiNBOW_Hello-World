#!/usr/bin/env python3
"""Every script must be runnable, documented, and honest about its own help.

Small defects of this kind accumulate silently. A script whose `python -m
py_compile` passes can still have a usage example that names a flag it does not
have, a missing docstring, or a `--help` that exits non-zero.
"""

import ast
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = sorted((ROOT / "scripts").glob("*.py"))

# Scripts that are libraries or one-shot diagnostics rather than CLI tools.
NO_CLI = {"run_tests.py"}   # has argparse, tested directly


def _scripts():
    return SCRIPTS


def test_there_are_scripts_to_check():
    assert len(SCRIPTS) >= 15, (
        f"only found {len(SCRIPTS)} scripts in scripts/ -- the glob may be wrong"
    )


def test_every_script_compiles():
    bad = []
    for p in SCRIPTS:
        try:
            compile(p.read_text(encoding="utf-8"), str(p), "exec")
        except Exception as exc:  # noqa: BLE001
            bad.append(f"{p.name}: {exc}")
    assert not bad, f"scripts that do not compile: {bad}"


def test_every_script_has_a_docstring():
    """A script with no docstring gives a reader nothing about what it is for."""
    missing = []
    for p in SCRIPTS:
        tree = ast.parse(p.read_text(encoding="utf-8"))
        if not ast.get_docstring(tree):
            missing.append(p.name)
    assert not missing, f"scripts with no module docstring: {missing}"


def test_docstring_examples_name_flags_that_exist():
    """A usage example that names a non-existent flag is worse than none.

    The docstrings are the first thing anyone reads about these scripts, and a
    command in one that fails teaches the reader to distrust the whole file.
    """
    problems = []
    for p in SCRIPTS:
        text = p.read_text(encoding="utf-8")
        doc = ast.get_docstring(ast.parse(text)) or ""
        examples = re.findall(r"python scripts/" + re.escape(p.name) + r"[^\n]*",
                              doc)
        for ex in examples:
            for flag in re.findall(r"(?<![\w-])--[a-z][a-z0-9-]+", ex):
                if flag not in text:
                    problems.append(f"{p.name}: docstring shows {flag} "
                                    "but the script never defines it")
    assert not problems, "\n".join(problems)


def test_help_exits_zero():
    """--help that returns non-zero breaks every wrapper around it."""
    bad = []
    for p in SCRIPTS:
        if p.name in NO_CLI:
            continue
        text = p.read_text(encoding="utf-8")
        if "argparse" not in text:
            continue
        try:
            proc = subprocess.run(
                [sys.executable, str(p), "--help"],
                capture_output=True, timeout=60, cwd=str(ROOT))
        except Exception as exc:  # noqa: BLE001
            bad.append(f"{p.name}: {exc}")
            continue
        if proc.returncode != 0:
            bad.append(f"{p.name} --help exited {proc.returncode}")
    assert not bad, f"scripts whose --help fails: {bad}"


def test_no_script_hardcodes_an_absolute_windows_path():
    """A machine-specific path breaks CI, which runs on Linux."""
    bad = []
    for p in SCRIPTS:
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"[A-Za-z]:\\\\", line):
                bad.append(f"{p.name}:{i}")
    assert not bad, f"hardcoded Windows paths in: {bad}"


def _write_text_calls(src: str):
    """Yield (line_number, call_text) for each write_text(...) call.

    Matched with balanced parens rather than a regex. A non-greedy regex stops
    at the first closing paren followed by a newline, which for a multi-line
    call containing nested calls lands in the middle of the arguments. That is
    how this test first reported a false positive on a call that already had
    newline="\n" further down.
    """
    for m in re.finditer(r"\.write_text\(", src):
        i = m.end()
        depth = 1
        while i < len(src) and depth:
            if src[i] == "(":
                depth += 1
            elif src[i] == ")":
                depth -= 1
            i += 1
        yield src[:m.start()].count("\n") + 1, src[m.end():i]


def test_scripts_write_json_with_explicit_newlines():
    """`* -text` means nothing normalises line endings on the way in.

    Without newline="\n", a Windows run commits CRLF into generated JSON and
    rewrites the entire file -- the 81 290-line manifest churn was exactly this.
    """
    bad = []
    for p in SCRIPTS:
        src = p.read_text(encoding="utf-8")
        for line, call in _write_text_calls(src):
            if "json.dumps" in call and "newline" not in call:
                bad.append(f"{p.name}:{line}")
    assert not bad, (
        f"write_text calls emitting JSON without newline= at: {bad}"
    )


def test_no_curated_template_is_empty():
    """A key in HELLO is not the same as a program in HELLO.

    `HELLO["coff"] = ""` satisfied the "is this language known?" test, so COFF
    was marked as having a curated template and generated as a banner followed
    by nothing -- a file claiming to be a Hello World program and containing
    none. `program_for()` now requires the value to be non-blank, and this
    asserts it directly so an empty entry cannot be reintroduced.
    """
    import importlib.util

    gen = ROOT / "scripts" / "generate_all_hello.py"
    spec = importlib.util.spec_from_file_location("gen_hello", gen)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gen_hello"] = mod
    spec.loader.exec_module(mod)

    # Whitespace is the legitimate exception: its program is spaces and tabs,
    # so it strips to nothing while being completely correct. Excluding it by
    # name, with the reason, rather than by "strip() and hope" -- otherwise the
    # next language with an invisible program would be added to the exclusion
    # list by whoever got there first.
    INVISIBLE = {"whitespace"}
    empty = [k for k, v in mod.HELLO.items()
             if not v.strip() and k not in INVISIBLE]
    assert not empty, (
        f"HELLO has {len(empty)} empty entries, which mark a language as having "
        f"a curated template while generating nothing: {empty[:5]}"
    )

    # And the manifest must not claim one either.
    import json
    man = json.loads(
        (ROOT / "hello" / "manifest.json").read_text(encoding="utf-8"))
    bad = [f["language"] for f in man["files"]
           if f.get("real_template")
           and f["language"].lower() not in INVISIBLE
           and not mod.program_for(
               f["language"], f.get("extension") or "")[0].strip()]
    assert not bad, f"languages claiming a template that is blank: {bad}"

