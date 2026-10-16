#!/usr/bin/env python3
"""Add curated Hello World programs to the generator, safely.

`scripts/generate_all_hello.py` holds one table of programs, keyed by lowercased
language name. Filling it in is the work of adding real programs to
`hello/full/`, and doing that by hand means editing a 1 100-entry dictionary with
a text editor, which is exactly the situation where a typo becomes a language's
entire content.

So batches go through here instead. A batch is a JSON object of
`{"language": "program"}`. This tool:

  1. refuses any language that is not in the manifest -- a program for a language
     this repository does not ship is a program nobody can check;
  2. refuses a blank program, which is the `HELLO["coff"] = ""` defect again;
  3. refuses a program that does not mention "Hello World", unless it is on the
     declaration-form allowlist, where the fields are the answer (a `.properties`
     file has no body to print);
  4. writes the entries into the generator, sorted, and regenerates;
  5. runs the template guard and the test suite.

Usage:
    python scripts/add_templates.py --from batch.json
    python scripts/add_templates.py --from batch.json --dry-run
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GEN = ROOT / "scripts" / "generate_all_hello.py"

# Formats with no program body: the declaration IS the content. Listed by
# extension, because that is what the generator has to decide on.
#
# Extended when the document-kind bucket was worked through: a Maven POM, a
# webpack config and a CircleCI file were all being rejected for not containing
# the string "Hello World", which is the wrong question to ask of a file whose
# whole purpose is to declare something about a project.
DECLARATION_FORMS = {
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


def load_manifest() -> dict:
    man = json.loads((ROOT / "hello" / "manifest.json").read_text(encoding="utf-8"))
    out = {}
    for f in man["files"]:
        out.setdefault(f["language"], []).append(f)
    return out


def existing_keys() -> set[str]:
    src = GEN.read_text(encoding="utf-8")
    start = src.index("HELLO: dict[str, str] = {")
    end = src.index("\n}\n", start)
    body = src[start:end]
    keys = set()
    for m in re.finditer(r'^\s{4}"((?:[^"\\]|\\.)*)"\s*:', body, re.M):
        keys.add(m.group(1))
    return keys


def normalise_key(k: str) -> str:
    return k.strip().lower()


def src_text() -> str:
    return GEN.read_text(encoding="utf-8")


def templates_value(src: str, key: str) -> str:
    """The literal currently in HELLO for `key`, or '' if there is none.

    Used by --replace to tell a genuine change from a no-op, so re-running a
    batch does not produce an empty commit.
    """
    start = src.index("HELLO: dict[str, str] = {")
    end = src.index("\n}\n", start)
    m = re.search(r'^\s{4}"' + re.escape(key) + r'"\s*:\s*',
                  src[start:end], re.M)
    if not m:
        return ""
    rest = src[start + m.end():end]
    try:
        return json.loads(rest.split("\n", 1)[0].rstrip().rstrip(","))
    except ValueError:
        return ""


def validate(batch: dict, manifest: dict, have: set[str],
             replace: bool = False) -> tuple[list, list, list]:
    """Return (accepted, duplicates, rejected)."""
    accepted, dupes, rejected = [], [], []
    for lang, program in sorted(batch.items()):
        key = normalise_key(lang)
        if key in have:
            if not replace:
                dupes.append((lang, "already has a template"))
                continue
            if templates_value(src_text(), key) == program:
                dupes.append((lang, "identical to what is already there"))
                continue
        if lang not in manifest:
            rejected.append((lang, "not a language this repository ships"))
            continue
        if not isinstance(program, str) or not program.strip():
            rejected.append((lang, "blank program"))
            continue
        exts = {f.get("extension") for f in manifest[lang]}
        declaration = bool(exts & DECLARATION_FORMS)
        if "hello world" not in program.lower() and not declaration:
            rejected.append((lang, "never says Hello World"))
            continue
        accepted.append((key, program))
    return accepted, dupes, rejected


def splice(entries: list[tuple[str, str]], replace: bool = False) -> str:
    src = GEN.read_text(encoding="utf-8")
    start = src.index("HELLO: dict[str, str] = {")
    end = src.index("\n}\n", start)
    body = src[start:end]

    def key_repr(k: str) -> str:
        return json.dumps(k, ensure_ascii=False)

    def val_repr(v: str) -> str:
        return json.dumps(v, ensure_ascii=False)

    lines = body.splitlines()
    added = 0
    for key, program in entries:
        new_line = f"    {key_repr(key)}: {val_repr(program)},"
        # keep the table sorted by key
        inserted = False
        for i, line in enumerate(lines):
            m = re.match(r'\s{4}"((?:[^"\\]|\\.)*)"\s*:', line)
            if m and m.group(1) == key and replace:
                lines[i] = new_line
                inserted = True
                added += 1
                break
            if m and m.group(1) > key:
                lines.insert(i, new_line)
                inserted = True
                added += 1
                break
        if not inserted:
            # after the last entry, before any trailing comment block
            insert_at = len(lines)
            while insert_at > 0 and lines[insert_at - 1].strip().startswith("#"):
                insert_at -= 1
            lines.insert(insert_at, new_line)
            added += 1

    new_body = "\n".join(lines)
    return src[:start] + new_body + src[end:], added


def run(*args) -> int:
    proc = subprocess.run([sys.executable, *args], cwd=str(ROOT),
                          capture_output=True, text=True)
    tail = (proc.stdout + proc.stderr).strip().splitlines()
    for line in tail[-6:]:
        print(f"  {line}")
    return proc.returncode


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from", dest="path", required=True,
                    help="JSON object of {language: program}")
    ap.add_argument("--dry-run", action="store_true",
                    help="validate and report, change nothing")
    ap.add_argument("--replace", action="store_true",
                    help="overwrite an existing template when the text differs")
    ap.add_argument("--skip-tests", action="store_true")
    args = ap.parse_args()

    batch = json.loads(pathlib.Path(args.path).read_text(encoding="utf-8"))
    if not isinstance(batch, dict):
        print("batch must be a JSON object of {language: program}", file=sys.stderr)
        return 2

    manifest = load_manifest()
    have = existing_keys()
    accepted, dupes, rejected = validate(batch, manifest, have,
                                         replace=args.replace)

    print(f"batch offers {len(batch)}")
    print(f"  accepted   : {len(accepted)}")
    print(f"  duplicates : {len(dupes)}")
    print(f"  rejected   : {len(rejected)}")

    if rejected:
        print("\nrejected:")
        for lang, why in rejected[:40]:
            print(f"    {lang:34} {why}")
    if dupes:
        print("\nduplicates:")
        for lang, why in dupes[:40]:
            print(f"    {lang:34} {why}")

    if not accepted:
        print("\nnothing to add")
        return 1

    if args.dry_run:
        print(f"\nwould add {len(accepted)}:")
        for key, _ in accepted[:60]:
            print(f"    {key}")
        return 0

    new_src, added = splice(accepted, replace=args.replace)
    GEN.write_text(new_src, encoding="utf-8", newline="\n")
    print(f"\nspliced {added} into HELLO")

    print("\nregenerating:")
    if run("scripts/generate_all_hello.py") != 0:
        print("  generation failed", file=sys.stderr)
        return 1
    print("balancing:")
    if run("scripts/balance_bytes.py") != 0:
        print("  balancing failed", file=sys.stderr)
        return 1
    print("template guard:")
    if run("scripts/check_templates.py") != 0:
        print("  template guard failed", file=sys.stderr)
        return 1
    if not args.skip_tests:
        print("tests:")
        if run("scripts/run_tests.py") != 0:
            print("  tests failed", file=sys.stderr)
            return 1

    print(f"\nadded {added} program(s); stage scripts/generate_all_hello.py and hello/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
