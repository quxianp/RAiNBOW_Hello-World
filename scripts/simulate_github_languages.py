"""Offline simulation of GitHub's language-bar pipeline.

Ports the pieces of github/linguist that decide what /api/.../languages shows:

  1. per-file language detection (filename -> modeline -> extension), see
     lib/linguist/strategy/*.rb
  2. include_in_language_stats? from blob_helper.rb:

         !vendored? && !documentation? && !generated? &&
         language && (detectable? || type in [:programming, :markup])

  3. the .gitattributes handling of the linguist-* attributes

Nothing here needs network or Ruby, so it can verify the repo before every
push.  Run:  python scripts/simulate_github_languages.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CONFIG = ROOT / "config"
HELLO = ROOT / "hello"

# ---------------------------------------------------------------------------
# Regexes ported from lib/linguist/strategy/modeline.rb (v7.x)
# ---------------------------------------------------------------------------

# EMACS_MODELINE: "-*- mode: <alias> -*-" (alias may contain . + # - _ etc.)
EMACS_MODELINE = re.compile(
    r"-\*-"
    r"(?:"
    r"[ \t]*(?=[^:;\s]+[ \t]*-\*-)"
    r"|(?:.*?[\t ;]|(?<=-\*-))[ \t]*mode[ \t]*:[ \t]*"
    r")"
    r"([^:;\s]+)"
    r"(?=[\t ;]|(?<![-*])-\*-)"
    r".*?-\*-"
)

# VIM_MODELINE: "vim: set ft=<alias>:" — Ruby's (\w+) capture, so only
# word characters (dashed aliases like objective-c silently fail here).
VIM_MODELINE = re.compile(
    r"(?:[ \t]|^)(?:vi|vim)(?:[0-9:.]+)?(?:<[^>]+>)?:"
    r"[ \t]*(?:se|set|setlocal)[ \t]+"
    r"(?:f(?:ile)?type|ft)=([^ \t:]+)"
)

DETECTABLE_TYPES = {"programming", "markup"}


def default_alias(name: str) -> str:
    # Language#default_alias = name.downcase.gsub(/\s/, '-')
    return re.sub(r"\s", "-", name.lower())


def build_alias_index(linguist: list[dict]) -> dict:
    index: dict = {}
    for lang in linguist:
        index.setdefault(default_alias(lang["name"]), lang["name"])
        for alias in lang.get("aliases") or []:
            if isinstance(alias, str):
                index.setdefault(alias.lower(), lang["name"])
    return index


def detect_modeline(text: str, alias_index: dict) -> str | None:
    match = EMACS_MODELINE.search(text)
    if match:
        return alias_index.get(match.group(1).lower())
    match = VIM_MODELINE.search(text)
    if match:
        return alias_index.get(match.group(1).lower())
    return None


def git_attributes(paths: list[Path]) -> dict:
    """Ask git what the linguist-* attributes are for each path."""
    rel = [p.relative_to(ROOT).as_posix() for p in paths]
    # bytes stdin: text mode on Windows would translate \n -> \r\n and git
    # would then quote the paths (trailing \r), breaking the key lookup.
    proc = subprocess.run(
        ["git", "check-attr", "linguist-vendored", "linguist-documentation",
         "linguist-generated", "linguist-detectable", "--stdin"],
        input="\n".join(rel).encode("utf-8"),
        capture_output=True, cwd=ROOT,
    )
    result: dict = {}
    for line in proc.stdout.decode("utf-8", "replace").splitlines():
        # path: attr: value   (path is C-quoted if it contains odd chars)
        parts = line.rsplit(": ", 2)
        if len(parts) != 3:
            continue
        path, attr, value = parts
        if path.startswith('"') and path.endswith('"'):
            path = path[1:-1].replace("\\r", "").replace("\\n", "\n")
        path = path.rstrip("\r")
        result.setdefault(path, {})[attr] = value
    return result


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    linguist = json.loads((DATA / "linguist.json").read_text(encoding="utf-8"))
    by_name = {e["name"]: e for e in linguist}
    alias_index = build_alias_index(linguist)

    manifest = json.loads((HELLO / "manifest.json").read_text(encoding="utf-8"))
    core_files = [
        f for f in manifest["files"]
        if f["path"].replace("\\", "/").startswith("hello/core/")
    ]
    print(f"core files in manifest : {len(core_files)}")

    paths = [ROOT / f["path"].replace("\\", "/") for f in core_files]
    attrs = git_attributes(paths)
    missing_attrs = [p for p in paths
                     if p.relative_to(ROOT).as_posix() not in attrs]
    if missing_attrs:
        print(f"ERROR: git check-attr returned nothing for "
              f"{len(missing_attrs)} paths (e.g. {missing_attrs[0]})")
        return 2

    total = 0
    counted: dict = defaultdict(int)
    problems: list[str] = []
    excluded: list[tuple[str, str]] = []

    for entry, path in zip(core_files, paths):
        rel = path.relative_to(ROOT).as_posix()
        expected = entry["language"]
        attr = attrs.get(rel, {})

        if attr.get("linguist-vendored") == "set":
            excluded.append((expected, "vendored"))
            continue
        if attr.get("linguist-documentation") == "set":
            excluded.append((expected, "documentation"))
            continue
        if attr.get("linguist-generated") == "set":
            excluded.append((expected, "generated"))
            continue

        data = path.read_bytes()
        total += len(data)
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            problems.append(f"{rel}: not valid UTF-8 (binary -> excluded)")
            excluded.append((expected, "binary"))
            continue

        # binary heuristic: NUL bytes or long undecodable runs
        if "\x00" in text:
            problems.append(f"{rel}: contains NUL (binary -> excluded)")
            excluded.append((expected, "binary"))
            continue

        detected = detect_modeline(text, alias_index)
        source = "modeline"
        if detected is None:
            ext = path.suffix
            ext_hits = [
                e["name"] for e in linguist
                if ext and ext in (e.get("extensions") or [])
            ]
            detected = ext_hits[0] if ext_hits else None
            source = f"extension{ext_hits or ''}"
            problems.append(f"{rel}: no modeline match; fell back to {detected}")

        if detected is None:
            excluded.append((expected, "no language"))
            continue
        if detected != expected:
            problems.append(f"{rel}: modeline resolved to {detected!r}, "
                            f"expected {expected!r} ({source})")
            continue

        lang_type = by_name.get(detected, {}).get("type")
        detectable = attr.get("linguist-detectable") == "set"
        if lang_type not in DETECTABLE_TYPES and not detectable:
            excluded.append((expected, f"type={lang_type}"))
            continue

        counted[detected] += len(data)

    print(f"counted languages      : {len(counted)}")
    print(f"counted bytes          : {total}")
    print(f"excluded files         : {len(excluded)}")
    reasons = defaultdict(int)
    for _, why in excluded:
        reasons[why] += 1
    for why, n in sorted(reasons.items(), key=lambda kv: -kv[1]):
        print(f"   {why:24s} {n}")

    # without the linguist-detectable attribute, how many would count?
    typed = defaultdict(int)
    for entry, path in zip(core_files, paths):
        name = entry["language"]
        if by_name.get(name, {}).get("type") in DETECTABLE_TYPES:
            typed[name] += path.stat().st_size
    print(f"without detectable attr: {len(typed)} languages "
          f"({sum(typed.values())} bytes)")

    shares = [100.0 * v / total for v in counted.values()] if total else []
    if shares:
        mean = sum(shares) / len(shares)
        stdev = (sum((s - mean) ** 2 for s in shares) / len(shares)) ** 0.5
        print(f"share min/mean/max     : "
              f"{min(shares):.5f}% / {mean:.5f}% / {max(shares):.5f}%")
        print(f"share stdev            : {stdev:.6f} pp")

    top = sorted(counted.items(), key=lambda kv: -kv[1])[:8]
    print("top bytes:")
    for name, size in top:
        print(f"   {name:28s} {size:8d} {100.0 * size / total:.3f}%")

    if problems:
        print(f"\nPROBLEMS ({len(problems)}):")
        for p in problems[:40]:
            print("  " + p)
        return 1

    print("\nOK: every core file detects as its manifest language and is "
          "stats-eligible.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
