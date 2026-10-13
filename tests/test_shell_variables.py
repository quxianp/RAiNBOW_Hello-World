#!/usr/bin/env python3
"""No variable may be read by run.sh before it is assigned.

`run.sh` runs under `set -u`, which makes reading an unassigned variable a fatal
error that kills the show. One did:

    if [ "$FAST" = "1" ]; then        # line 279, never assigned anywhere

That line sits behind `[ -t 1 ]`, so it only runs when stdout is a terminal --
which is what VHS gives the recorded demo and what no local test gives, because
every local invocation pipes its output. The result was a published GIF whose
last 22 seconds were a still frame, with this in the middle of it:

    run.sh: line 279: FAST: unbound variable

The only reason it was ever found is that somebody looked at a frame of the
recording instead of at a file size. Nothing else could see it: every local run
took the other branch, the script exited with an error rather than a hang, and
`bash -n` only parses.

So this test reads the script rather than running it. It finds every `$NAME` and
`${NAME...}` the file mentions and asserts each one is assigned somewhere in the
same file. That is a static answer to a runtime-only failure, which is the only
kind available for a branch that requires a terminal.

Known shell-provided names are excluded; see SHELL_VARS.
"""

import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUN_SH = ROOT / "run.sh"

# Assigned by bash itself, or by the shell that invoked us. Reading these is safe.
SHELL_VARS = {
    # bash special parameters
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "@", "*", "#", "?", "-",
    "$", "!", "_", "0",
    # bash builtin variables
    "SECONDS", "RANDOM", "LINENO", "PWD", "OLDPWD", "PPID", "UID", "EUID",
    "GROUPS", "HOSTNAME", "HOSTTYPE", "MACHTYPE", "OSTYPE", "SHELL", "SHLVL",
    "BASHPID", "BASH", "BASH_VERSION", "BASH_VERSINFO", "RANDOM",
    # environment this repository relies on
    "HOME", "PATH", "USER", "LOGNAME", "TERM", "COLORTERM", "FORCE_COLOR",
    "NO_COLOR", "CI", "GITHUB_ACTIONS", "GITHUB_REF_NAME", "GITHUB_TOKEN",
    "PYTHON", "PY", "MOTION", "FORCE_HOLD", "RUN_LOG",
}

# Variables run.sh assigns implicitly as loop targets or via `read`.
IMPLICIT = re.compile(
    r"^\s*(?:for|select)\s+([A-Za-z_][A-Za-z0-9_]*)"
    r"|\bread\s+(?:-[a-zA-Z]+\s+)*(-?[A-Za-z_][A-Za-z0-9_]*)",
    re.M)

# Assignment forms: NAME=, NAME+=, "NAME"=, ${NAME}=, NAME[...] =, export NAME=,
# readonly NAME=, declare NAME=, local NAME=, typeset NAME=, and for-loop targets.
ASSIGN = re.compile(
    r"(?:^|[\s;&|(){])"
    r"(?:export\s+|readonly\s+|declare\s+|typeset\s+|local\s+)?"
    r"([A-Za-z_][A-Za-z0-9_]*)\s*(?:\[[^\]]*\])?\+?=",
    re.M)

READ = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)[#%:\-}]|\$([A-Za-z_][A-Za-z0-9_]*)")


def _strip_comments(src: str) -> str:
    """Drop `#` comments, quote-aware.

    Comments mention variable names in prose -- including the ones being fixed,
    which is how this file came to name `$HUE` after the offending line was
    deleted -- and a comment cannot execute, so it must not count as a read.

    The scanner tracks quoting rather than using a regex, because run.sh contains
    `printf '%s' '#'` and `${#msg}`, and both look like a comment to a regex.
    """
    out = []
    quote = None
    i = 0
    n = len(src)
    while i < n:
        ch = src[i]
        if quote is None:
            if ch in "'\"":
                quote = ch
                out.append(ch)
                i += 1
            elif ch == "#" and (i == 0 or src[i - 1] in " \t\n;&|("):
                while i < n and src[i] != "\n":
                    i += 1
            else:
                out.append(ch)
                i += 1
        else:
            out.append(ch)
            i += 1
            # a backslash escapes the next character inside double quotes only
            if quote == '"' and ch == "\\" and i < n:
                out.append(src[i])
                i += 1
            elif ch == quote:
                quote = None
    return "".join(out)


def _source() -> str:
    return RUN_SH.read_text(encoding="utf-8")


def _referenced(src: str) -> set:
    found = set()
    for braced, bare in READ.findall(src):
        found.add(braced or bare)
    return found


def _assigned(src: str) -> set:
    found = set(ASSIGN.findall(src))
    for a, b in IMPLICIT.findall(src):
        found.add(a or b)
    return found


def test_run_sh_declares_every_variable_it_reads():
    src = _strip_comments(_source())
    unassigned = sorted(_referenced(src) - _assigned(src) - SHELL_VARS)
    assert not unassigned, (
        f"run.sh reads {len(unassigned)} variable(s) it never assigns: "
        f"{unassigned}. It runs under `set -u`, so each of these kills the show "
        f"the first time that line executes. If the line is behind a terminal "
        f"check it will only ever fail in the recorded demo."
    )


def test_run_sh_is_syntactically_valid():
    bash = shutil.which("bash") or r"D:\Git\bin\bash.exe"
    if not Path(bash).exists():
        return
    proc = subprocess.run([bash, "-n", str(RUN_SH)],
                          capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, f"bash -n failed:\n{proc.stderr}"


def test_fast_is_actually_assigned():
    """The specific regression, kept so it cannot come back quietly.

    `--fast` is a documented mode. It has to both assign `FAST` and use it, or
    the flag either does nothing or kills the script.
    """
    src = _source()
    assert re.search(r"(?:^|[\s;&|(){])FAST\s*=", src, re.M), (
        "run.sh never assigns FAST; every reference to it is fatal under `set -u`")
    assert re.search(r"--fast\).*FAST=1", src), (
        "the --fast flag does not set FAST=1, so the mode it selects is dead code")
    assert re.search(r'"\$FAST"', src), (
        "run.sh assigns FAST but never reads it")


def test_uses_set_u_consistently():
    """`set -u` is the setting that turns this class into a fatal error.

    If it is ever removed the test above stops describing reality, so it says so
    rather than quietly becoming a weaker check.
    """
    src = _source()
    assert re.search(r"^set -[a-z]*u", src, re.M), (
        "run.sh no longer sets -u; test_run_sh_declares_every_variable_it_reads "
        "is now checking something that cannot fail the show")
