#!/usr/bin/env python3
"""Merge every fetched source into one deduplicated language inventory.

Outputs
-------
data/merged_langs.json   master record (name, slug, aliases, extensions, color,
                         type, source, linguist_name, has_linguist_color, is_core)
config/all-langs.json    flat list used by the README / generator
config/core-langs.txt    one Linguist-coloured language name per line

Usage: python3 scripts/merge_language_sources.py [--target 3000]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CONFIG = ROOT / "config"
LOGS = ROOT / "logs"
DATA.mkdir(parents=True, exist_ok=True)
CONFIG.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)

TARGET_TOTAL = 3000

# Sources whose harvest is already curated -> trust names verbatim.
TRUSTED_SOURCES = {"linguist", "builtin"}
# Wikipedia list pages are prose/table heavy -> medium trust.
MEDIUM_SOURCES = {"wikipedia", "esolangs", "rosettacode", "tiobe", "ieee"}

ALLOWED_CHARS = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 .+#*!?'-]*$")
BAD_CHARS = re.compile(r"[{}<>@\\^~|]|:\s|\d{3,}|%[0-9A-Fa-f]{2}|!important|::")
BLOCK_SUBSTRINGS = (
    "language", "program", "software", "compiler", "interpreter", "wiki",
    "citation", "reference", "retrieved", "updated", "isbn", "doi", "tiobe",
    "copyright", "license", "template", "category", "portal", "see also",
    "external", "notes", "history", "timeline", "introduction", "overview",
    "summary", "description", "application", "syntax", "semantics",
    "paradigm", "typing", "memory", "management", "garbage", "collector",
    "implementation", "engine", "framework", "library", "package", "module",
    "system", "source code", "open source", "free software", "cross platform",
    "operating system", "development", "framework", "specification",
    "standard", "version", "release", "released", "developed", "created",
    "designed", "called", "also known", "however", "although", "because",
    "between", "during", "through", "based on", "such as", "including",
    " used ", " uses ", "example", "the ", " and ", " for ", " with ",
    " which ", "most ", " best ", "list of", "more than", "as well as",
    # harvested from people / talk / blog indexes instead of language lists
    "paper", "papers", "talk", "talks", "watch", "tutor", "initialization",
    "translation", "skeleton", "critic", "neural", "turing", "love",
    "author", "authors", "poetry", "songs", "movies", "films", "people",
    "musicians", "conference", "workshop", "interview", "podcast",
    "newsletter", "blog", "essay", "reading", "checklist", "curriculum",
    "roadmap", "cheatsheet", "cheat sheet", "best practices", "anti-patterns",
)
ENTITY_LIKE = re.compile(r"^0(x[0-9a-f]{2,}|[a-z])", re.I)
STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "if", "of", "to", "in", "on", "at",
    "by", "for", "with", "from", "as", "is", "are", "was", "were", "be",
    "been", "it", "its", "this", "that", "these", "those", "there", "here",
    "when", "where", "which", "who", "what", "why", "how", "all", "any",
    "some", "each", "every", "more", "most", "less", "least", "such", "both",
    "other", "another", "same", "own", "very", "just", "only", "also", "can",
    "could", "will", "would", "shall", "should", "may", "might", "must",
    "do", "does", "did", "have", "has", "had", "use", "used", "uses", "using",
    "make", "made", "get", "gets", "set", "add", "added", "new", "old",
    "one", "two", "three", "first", "second", "third", "last", "next",
    "up", "down", "out", "into", "over", "under", "about", "after", "before",
    "then", "than", "so", "not", "no", "yes", "read", "run", "see", "note",
    "list", "page", "home", "help", "search", "index", "menu", "close",
    "open", "top", "first", "well", "still", "even", "too", "here", "now",
}

# --------------------------------------------------------------------------
# normalisation + noise rejection
# --------------------------------------------------------------------------
PAREN_SUFFIX = re.compile(r"\s*\(([^)]*)\)\s*$")
NON_LANG_WORDS = {
    "software", "compiler", "compilers", "interpreter", "interpreters",
    "implementation", "implementations", "programming", "language",
    "languages", "computer", "computing", "program", "programs",
    "system", "systems", "library", "libraries", "framework", "frameworks",
    "list", "lists", "category", "template", "templates", "file", "files",
    "wiki", "wikipedia", "history", "portal", "help", "overview", "index",
    "comparison", "applications", "development", "environment", "source",
    "code", "codes", "convention", "specification", "specifications",
    "standard", "standards", "operating", "kernel", "distribution",
    "release", "version", "tutorial", "reference", "glossary", "timeline",
    "theory", "practice", "syntax", "semantics", "features", "example",
    "examples", "tools", "tooling", "framework", "engine", "engines",
    "community", "projects", "project", "software_engineering", "note",
    "notes", "people", "person", "authors", "creator", "created",
}
JUNK_EXACT = {
    "linux", "unix", "windows", "macos", "freebsd", "openbsd", "netbsd",
    "github", "gitlab", "google", "microsoft", "apple", "ibm", "oracle",
    "c", "c++", "c#", "java", "javascript", "python", "ruby", "rust",
    "go", "swift", "kotlin", "scala", "perl", "php", "haskell", "elixir",
    "lua", "tcl", "r", "julia", "dart", "zig", "nim", "crystal", "ocaml",
    "fortran", "cobol", "pascal", "delphi", "ada", "prolog", "lisp",
    "scheme", "racket", "erlang", "clojure", "elisp", "emacs", "vim",
    "visual basic", "assembly", "bash", "zsh", "fish", "sql", "html", "css",
    "json", "yaml", "toml", "xml", "markdown", "tex", "latex", "sql92",
    "apache", "nginx", "docker", "kubernetes", "aws", "azure", "gcp",
    "unicode", "ascii", "utf-8", "utf-16", "iso-8859-1", "latin-1",
    "1", "2", "3", "4", "5", "one", "two", "three", "zero", "true", "false",
    "none", "null", "nil", "undefined", "unknown", "misc", "other", "others",
    "list", "lists", "index", "outline", "glossary", "history", "timeline",
    "programming_language", "markup_language", "query_language",
    "template_engine", "stylesheet_language", "configuration_language",
    "data_format", "data_formats", "file_format", "file_formats",
    "page", "pages", "article", "articles", "book", "books", "media",
    "audio", "video", "image", "images", "text", "binary", "string",
    "strings", "number", "numbers", "integer", "integers", "float",
    "boolean", "byte", "bytes", "bit", "bits", "char", "chars",
}
STRIP_WORDS = re.compile(
    r"\b(programming|computer|web|scripting|query|markup|data|template|"
    r"stylesheet|configuration|config|core|system|development|formal|"
    r"specification|query|query|academic|education|functional|logic|"
    r"logic|hardware|description|blockchain|quantum|concurrent|parallel|"
    r"esoteric|assembly|domain|specific|first|class|imperative|"
    r"object|oriented|procedural|array|stack|typed|low|level|high|"
    r"level|byte|bytecode|compiled|interpreted|legacy|modern)\b",
    re.I,
)


def norm_key(name: str) -> str:
    """Case/punctuation-insensitive key.  CJK and other scripts are kept."""
    s = unicodedata.normalize("NFKC", name).lower().strip()
    s = PAREN_SUFFIX.sub("", s)
    out = []
    for ch in s:
        if ch.isalnum() or ch in "+#*/-.":
            out.append(ch)
        else:
            out.append(" ")
    return re.sub(r"\s+", " ", "".join(out)).strip()


def accept(name: str, trusted: bool = False) -> bool:
    """Reject harvested prose; `trusted` skips the aggressive heuristics."""
    n = name.strip()
    if not n or len(n) > 34:
        return False
    if not trusted and len(n) < 2:
        return False
    low = n.lower()
    if not any(ch.isalnum() for ch in n):
        return False
    if low in JUNK_EXACT:
        return True  # real language names that collide with common words
    if trusted:
        return len(n) >= 1
    if not ALLOWED_CHARS.match(n):
        return False
    if BAD_CHARS.search(n):
        return False
    if low in JUNK_EXACT:
        return True
    if " - " in n or low.startswith("awesome") or "awesome " in low:
        return False
    if ENTITY_LIKE.match(n):
        return False
    if any(tok in low for tok in BLOCK_SUBSTRINGS):
        return False
    if low.startswith(("list", "index", "glossary", "outline", "timeline")):
        return False
    words = re.findall(r"[A-Za-z][A-Za-z0-9+#.]*", low)
    if not words or len(words) > 3:
        return False
    stops = sum(1 for w in words if w in STOP_WORDS)
    if stops and stops >= len(words):
        return False
    if stops and len(words) > 1 and stops / len(words) > 0.34:
        return False
    if len(words) == 1 and len(words[0]) < 3:
        return False
    return True


RESERVED = {
    "con", "prn", "aux", "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}


def slugify(name: str) -> str:
    """Filesystem-safe slug that keeps non-Latin scripts (仓颉, 文言, 易语言).

    Slashes, backslashes and Windows device names are avoided so the result is
    usable as a directory name on every platform.
    """
    s = unicodedata.normalize("NFKC", name).lower().strip()
    out = []
    for ch in s:
        if ch.isalnum() or ch in "+#":
            out.append(ch)
        else:
            out.append("-")
    s = re.sub(r"-{2,}", "-", "".join(out)).strip("-.")
    s = s.lstrip(".") or "lang"
    if s in RESERVED or re.fullmatch(r"[-_. ]+", s):
        s = f"lang-{s}"
    return s[:80] or "lang"


def load(path: Path, default=None):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"  ! cannot parse {path.name}: {exc}", file=sys.stderr)
        return default


# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=TARGET_TOTAL)
    args = ap.parse_args()

    log_path = LOGS / "merge_language_sources.log"
    log_fh = open(log_path, "a", encoding="utf-8")

    def log(msg: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        log_fh.write(line + "\n")
        log_fh.flush()

    log("=== merge_language_sources start ===")

    records: dict[str, dict] = {}
    source_counter: Counter = Counter()
    source_first: dict[str, set] = defaultdict(set)
    rejected: Counter = Counter()

    def ingest(name: str, source: str, meta: dict | None = None) -> None:
        name = (name or "").strip()
        if not name:
            return
        key = norm_key(name)
        if not key:
            return
        rec = records.get(key)
        if rec is None:
            trusted = source in TRUSTED_SOURCES or source.startswith("builtin")
            if not accept(name, trusted=trusted):
                rejected[source] += 1
                return
            rec = {
                "name": name,
                "slug": slugify(name),
                "key": key,
                "aliases": [],
                "extensions": [],
                "color": None,
                "type": None,
                "source": [],
                "linguist_name": None,
                "has_linguist_color": False,
                "is_core": False,
                "groups": [],
            }
            records[key] = rec
        if source not in rec["source"]:
            rec["source"].append(source)
        source_first[key].add(source)
        source_counter[source] += 1
        if source == "linguist" and rec["name"] != name:
            # Linguist is authoritative: two of its languages can normalise to
            # the same key ("G-code" / "G Code"); keep the canonical spelling.
            old = rec["name"]
            rec["name"] = name
            rec["slug"] = slugify(name)
            records[key] = rec
        if meta:
            meta = {k: v for k, v in meta.items() if v not in (None, [], "")}
            if meta.get("extensions") and not rec["extensions"]:
                rec["extensions"] = meta["extensions"][:6]
            if meta.get("aliases"):
                for a in meta["aliases"]:
                    if a not in rec["aliases"] and len(rec["aliases"]) < 12:
                        rec["aliases"].append(a)
            if meta.get("color") and not rec["color"]:
                rec["color"] = meta["color"]
            if meta.get("type") and not rec["type"]:
                rec["type"] = meta["type"]

    # --- 1. linguist (authoritative names + metadata) ---------------------
    linguist = load(DATA / "linguist.json", []) or []
    alias_to_name = {}
    for entry in linguist:
        meta = {
            "color": entry.get("color"),
            "type": entry.get("type"),
            "extensions": entry.get("extensions") or [],
            "aliases": entry.get("aliases") or [],
        }
        ingest(entry["name"], "linguist", meta)
        for a in entry.get("aliases") or []:
            alias_to_name[norm_key(a)] = entry["name"]
        rec = records.get(norm_key(entry["name"]))
        if rec:
            rec["linguist_name"] = entry["name"]
    colored = 0
    for entry in linguist:
        if entry.get("color"):
            colored += 1
            rec = records.get(norm_key(entry["name"]))
            if rec:
                rec["has_linguist_color"] = True
    log(f"linguist: {len(linguist)} records, {colored} coloured")

    # --- 2. wikipedia -----------------------------------------------------
    wiki = load(DATA / "wikipedia_langs.json", {}) or {}
    for page, payload in wiki.items():
        for nm in payload.get("languages", []):
            ingest(nm, "wikipedia")
    log(f"wikipedia: {len(wiki)} pages ingested")

    # --- 3. esolangs / rosetta / tiobe / ieee / topics ---------------------
    other = load(DATA / "other_sources.json", {}) or {}
    for src, payload in other.items():
        for nm in payload.get("languages", []):
            ingest(nm, src)
    log(f"other sources: {len(other)} ingested")

    # --- 4. builtin fallback inventory ------------------------------------
    builtin = load(DATA / "builtin_langs.json", {}) or {}
    for group, names in builtin.items():
        for nm in names:
            ingest(nm, f"builtin:{group}")
            rec = records.get(norm_key(nm))
            if rec and group not in rec["groups"]:
                rec["groups"].append(group)
    log(f"builtin groups: {len(builtin)}")

    # --- 5. resolve alias-only sightings ----------------------------------
    for key in list(records):
        canon = alias_to_name.get(key)
        if canon and norm_key(canon) != key and norm_key(canon) in records:
            a, b = records[norm_key(canon)], records[key]
            for f in ("extensions", "aliases"):
                for v in b[f]:
                    if v not in a[f] and len(a[f]) < 12:
                        a[f].append(v)
            if b["color"] and not a["color"]:
                a["color"] = b["color"]
            for s in b["source"]:
                if s not in a["source"]:
                    a["source"].append(s)
            del records[key]

    out = sorted(records.values(), key=lambda r: r["key"])

    # --- core selection: every Linguist language that has a colour ---------
    core = [r for r in out if r["has_linguist_color"]]
    core.sort(key=lambda r: (r["color"] or "ffffff").lower())
    for rec in core:
        rec["is_core"] = True

    log(f"merged unique languages: {len(out)}")
    log(f"core (linguist coloured) : {len(core)}")
    if len(core) < 600:
        log(f"WARNING core below 600: {len(core)}")
    if len(out) < args.target:
        log(f"WARNING total below target {args.target}: {len(out)}")

    stats = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_unique": len(out),
        "core_colored": len(core),
        "linguist_total": len(linguist),
        "linguist_colored": colored,
        "target_total": args.target,
        "source_mentions": dict(source_counter.most_common()),
        "rejected_as_noise": dict(rejected.most_common()),
        "unique_from_source": {k: len(v) for k, v in source_first.items()},
        "records_by_source": {
            "linguist": len([r for r in out if "linguist" in r["source"]]),
            "wikipedia": len([r for r in out if "wikipedia" in r["source"]]),
            "esolangs": len([r for r in out if "esolangs" in r["source"]]),
            "tiobe": len([r for r in out if "tiobe" in r["source"]]),
            "ieee": len([r for r in out if "ieee" in r["source"]]),
            "github_topics": len(
                [r for r in out if any(s.startswith("gh_") for s in r["source"])]
            ),
            "builtin": len([r for r in out if any(s.startswith("builtin") for s in r["source"])]),
        },
        "core_percent_target": (100.0 / len(core)) if core else 0.0,
    }
    (DATA / "merged_langs.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    (CONFIG / "all-langs.json").write_text(
        json.dumps(
            {
                "generated": stats["generated"],
                "total": len(out),
                "core": len(core),
                "target_total": args.target,
                "stats": stats,
                "languages": [
                    {
                        "name": r["name"],
                        "slug": r["slug"],
                        "extensions": r["extensions"],
                        "color": r["color"],
                        "type": r["type"],
                        "is_core": r["is_core"],
                        "sources": r["source"],
                    }
                    for r in out
                ],
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    (CONFIG / "core-langs.txt").write_text(
        "\n".join(r["name"] for r in core) + "\n", encoding="utf-8"
    )
    (DATA / "merge_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    log(f"wrote data/merged_langs.json ({len(out)} entries)")
    log(f"wrote config/all-langs.json, config/core-langs.txt ({len(core)} lines)")
    log("=== merge done ===")
    log_fh.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
