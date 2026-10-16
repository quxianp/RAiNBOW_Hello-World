#!/usr/bin/env python3
"""A declaration form must hold a declaration, not a program.

Seven of this repository's language files began as placeholders and were later
given real content, on the grounds that some formats have no program body: a
`.properties` file is key=value, a `.cabal` file declares metadata, a `go.mod`
declares a module. That was the right call and it is now load-bearing for about
two hundred more, so it needs a guard rather than a convention.

The failure mode is quiet. A declaration form given a program does not break
anything: the file still parses, still has the right byte count, still carries
the right Linguist modeline, and still passes all nineteen acceptance checks. It
is simply wrong -- a `go.mod` containing a Go program is a file that every tool
in the Go ecosystem rejects.

So this asserts the shape rather than the content. For every language whose
extension is a declaration form, the file must not look like a program: no
`function main`, no `def main`, no `int main`, no `print(` in a language that
cannot print.

Skipped when the manifest is missing.
"""

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "hello" / "manifest.json"

# Kept in step with DECLARATION_FORMS in scripts/add_templates.py. This is a
# second copy on purpose -- a test that imports the list it is testing cannot fail.
DECLARATION_EXTENSIONS = {
    ".properties", ".cabal", ".mod", ".work", ".sum", ".gohtml", ".dhall",
    ".json", ".json5", ".json6", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".conf", ".editorconfig", ".gitattributes", ".gitignore", ".env",
    ".csv", ".tsv", ".xml", ".plist", ".maven", ".webpack", ".vite",
    ".babel", ".eslint", ".prettier", ".npm", ".yarn", ".pnpm", ".bundler",
    ".homebrew", ".helm", ".libtool", ".automake", ".buildroot", ".buck2",
    ".gitlab_ci", ".gitlab-ci", ".tekton", ".nexus", ".chocolatey",
    ".terraform_cdk", ".aws_cdk", ".rollup", ".nix", ".dockerfile",
    ".podfile", ".gemfile", ".cpanfile", ".composer", ".csproj", ".sln",
    ".gradle", ".bazel", ".buck", ".justfile", ".make", ".mk",
}

# Markers of a program body. None of these should appear in a declaration form.
PROGRAM_MARKERS = [
    re.compile(r"\b(?:function|func|def|proc|sub)\s+main\b"),
    re.compile(r"\bint\s+main\s*\("),
    re.compile(r"\bvoid\s+main\s*\("),
    re.compile(r"^\s*(?:public\s+|private\s+|static\s+)*class\s+\w+"),
    re.compile(r"\bprintln\s*\("),
    re.compile(r"\bconsole\.log\s*\("),
    re.compile(r"^\s*#!/"),
]


def _declaration_languages():
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out = []
    for f in man["files"]:
        ext = (f.get("extension") or "").lower()
        if ext in DECLARATION_EXTENSIONS:
            out.append(f)
    return out


def test_no_declaration_form_contains_a_program_body():
    files = _declaration_languages()
    assert files, (
        "no language in the manifest has a declaration-form extension; the list "
        "in this test and in add_templates.py has drifted out of step with the "
        "repository")

    offenders = []
    for f in files:
        text = (ROOT / f["path"]).read_text(encoding="utf-8", errors="replace")
        for marker in PROGRAM_MARKERS:
            if marker.search(text):
                offenders.append(f"{f['path']}: {marker.pattern}")
                break

    assert not offenders, (
        f"{len(offenders)} declaration-form file(s) contain something that "
        f"looks like a program body: {offenders[:6]}. A .go.mod with a Go "
        f"program in it is a file every Go tool rejects.")


def test_the_two_declaration_lists_agree():
    """One list, in a script and in a test, with nothing checking they match.

    That is the shape of every defect in logs/ERRORS.log. So the lists are
    compared, and the comparison is by extension rather than by trust.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "add_templates", ROOT / "scripts" / "add_templates.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    script_set = {e.lower() for e in mod.DECLARATION_FORMS}
    test_set = {e.lower() for e in DECLARATION_EXTENSIONS}

    missing_from_test = sorted(script_set - test_set)
    missing_from_script = sorted(test_set - script_set)

    assert not missing_from_test, (
        f"add_templates.py treats {missing_from_test} as declaration forms but "
        f"this test does not, so those files are unguarded")
    assert not missing_from_script, (
        f"this test guards {missing_from_script} but add_templates.py does not "
        f"treat them as declaration forms, so they are guarded against the "
        f"wrong thing")
