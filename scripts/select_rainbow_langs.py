#!/usr/bin/env python3
"""Pick the rainbow core layer.

Core layer = *every* GitHub Linguist language that declares a `color`.
Those are the only languages GitHub will paint on the repository language bar,
so they all go into hello/core/ and every one of them gets an equal share of
the bytes.  The list is ordered by hue so the resulting bar reads
red -> orange -> yellow -> green -> cyan -> blue -> purple -> pink -> brown -> grey.

Outputs
-------
config/rainbow_langs.json   ordered core records (hue, colour, extension, path)
config/core-langs.txt       plain name list
logs/rainbow_selection.txt  human readable report + hue histogram
"""

from __future__ import annotations

import colorsys
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CONFIG = ROOT / "config"
LOGS = ROOT / "logs"
for d in (DATA, CONFIG, LOGS):
    d.mkdir(parents=True, exist_ok=True)

MIN_CORE = 600
MAX_CORE = 800

HUE_BUCKETS = [
    (0, "red"), (15, "red-orange"), (30, "orange"), (45, "amber"),
    (60, "yellow"), (80, "yellow-green"), (100, "green"), (140, "spring-green"),
    (165, "green-cyan"), (185, "cyan"), (200, "cyan-blue"), (220, "azure"),
    (245, "blue"), (265, "violet"), (285, "purple"), (305, "magenta"),
    (325, "pink"), (345, "rose"), (360, "red"),
]

# extensions that Linguist maps to several languages at once -> de-prioritise
AMBIGUOUS = {
    ".h": "C++/Objective-C headers", ".m": "Objective-C/Matlab/Octave/Mercury",
    ".inc": "many languages", ".t": "Perl/Tcl/Turing", ".l": "Lex/Common Lisp",
    ".cls": "TeX/Visual Basic class/Apex", ".bas": "BASIC dialects",
    ".sql": "SQL dialects", ".pl": "Prolog/Perl", ".sc": "Scala/Scilab",
    ".g": "Graph/GNU/Golo", ".r": "R/Rebol/Rexx", ".p": "Pascal/Pike/Prolog",
    ".s": "Assembly/Scheme/Smalltalk", ".f": "Fortran/FORTRAN/Futhark",
    ".d": "D/DTrace", ".es": "JavaScript/EJS", ".mod": "Go/Modula",
    ".bs": "Brainfuck/Boo", ".nl": "Logtalk/Nix", ".pde": "Processing/PDE",
    ".gs": "Ghostscript/Grammar", ".fcgi": "many (CGI)", ".ncl": "NetCDF/NCL",
}


def load(path: Path, default=None):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"! cannot read {path}: {exc}", file=sys.stderr)
        return default


def hex_to_rgb(value: str):
    v = (value or "").lstrip("#").strip()
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    if len(v) != 6 or not re.fullmatch(r"[0-9a-fA-F]{6}", v):
        return None
    return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))


def classify(hue: float) -> str:
    for edge, label in HUE_BUCKETS:
        if hue < edge:
            return label
    return "red"


RESERVED = {
    "con", "prn", "aux", "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}


def slugify(name: str) -> str:
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


SAFE_EXT = re.compile(r"^\.[A-Za-z0-9._#+-]{0,24}$")

# Linguist's Modeline strategy is the highest priority detector: a Vim/Emacs
# modeline beats every extension heuristic.  Emitting one per core file is what
# keeps 100+ languages that share `.bas`, `.cls`, `.sql`, `.yml`, ... on separate
# segments of the bar.
MODELINE_PREFIX = {
    "hash": ("#", "# vim: set ft={alias}:"),
    "slash": ("//", "// vim: set ft={alias}:"),
    "dash": ("--", "-- vim: set ft={alias}:"),
    "semi": (";", "; vim: set ft={alias}:"),
    "block": ("/*", "/* vim: set ft={alias}: */"),
    "html": ("<!--", "<!-- vim: set ft={alias}: -->"),
}


def comment_prefix_for(ext: str, fname: str | None) -> str:
    """Best guess at a comment token Linguist's modeline scanner accepts."""
    e = (ext or "").lower()
    if fname:
        f = fname.lower()
        if f.startswith(".") or f in {
            "npmrc", "torrc", "crontab", "procfile", "hosts", "root",
            "requirements.txt", "browserslist", "singularity", "earthfile",
            "apkbuild", "meson.build", "dune-project", "xmake.lua",
        }:
            return MODELINE_PREFIX["hash"][0]
        if f.endswith((".yml", ".yaml", ".toml", ".ini", ".cfg", ".conf",
                        ".properties", ".gitignore", ".gitattributes")):
            return MODELINE_PREFIX["hash"][0]
    if e in {".py", ".rb", ".sh", ".pl", ".r", ".jl", ".yaml", ".yml", ".toml",
             ".ini", ".cfg", ".conf", ".properties", ".rs", ".go", ".jl",
             ".nim", ".cr", ".ex", ".exs", ".hs", ".elm", ".purs", ".coffee",
             ".tf", ".hcl", ".nix", ".starlark", ".bazel", ".mk", ".make",
             ".cmake", ".groovy", ".tcl", ".ps1", ".fish", ".zsh", ".ksh",
             ".csh", ".nu", ".crontab", ".editorconfig", ".gitignore",
             ".gitattributes", ".npmrc", ".dockerfile"}:
        return MODELINE_PREFIX["hash"][0]
    if e in {".md", ".markdown", ".mkd", ".html", ".htm", ".xml", ".svg",
             ".xhtml", ".rss", ".atom", ".xsl", ".xslt", ".plist", ".ipynb"}:
        return MODELINE_PREFIX["html"][0]
    if e in {".sql", ".tsql", ".plpgsql", ".psql", ".hql", ".presto", ".sparql",
             ".lisp", ".lsp", ".scm", ".ss", ".rkt", ".clj", ".cljs", ".cljc",
             ".el", ".elisp", ".asm", ".s", ".sed", ".tcl", ".vb", ".bas",
             ".cls", ".frm", ".ctl", ".vbs", ".vba", ".pas", ".pp", ".ada",
             ".adb", ".ads", ".sv", ".svh", ".vhd", ".vhdl", ".4dm", ".csd",
             ".tcl", ".smt", ".smt2", ".z3", ".v", ".vi"}:
        return MODELINE_PREFIX["semi" if e in {
            ".lisp", ".lsp", ".scm", ".ss", ".rkt", ".clj", ".cljs", ".cljc",
            ".el", ".elisp", ".asm", ".s", ".sed", ".bas", ".cls", ".frm",
            ".ctl", ".vb", ".vba", ".vbs", ".smt", ".smt2", ".z3", ".csd",
        } else "dash"][0]
    if e in {".c", ".h", ".cpp", ".hpp", ".cc", ".hh", ".cxx", ".cs", ".java",
             ".kt", ".kts", ".scala", ".groovy", ".swift", ".dart", ".zig",
             ".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx", ".css", ".scss",
             ".less", ".sol", ".move", ".glsl", ".vert", ".frag", ".wgsl",
             ".hlsl", ".metal", ".cu", ".cuh", ".ino", ".vue", ".svelte",
             ".astro", ".json5", ".jsonc", ".d", ".vala", ".v", ".sv", ".hcl",
             ".proto", ".thrift", ".graphql", ".gql", ".rhai", ".odin", ".vlang"}:
        return MODELINE_PREFIX["slash"][0]
    return MODELINE_PREFIX["hash"][0]


def modeline_for(entry: dict, ext: str, fname: str | None):
    """Return (linguist alias, modeline template) for a coloured language."""
    aliases = [a for a in (entry.get("aliases") or []) if a]
    name = entry["name"]
    candidates = aliases + [name.lower(), name.lower().replace(" ", "-")]
    alias = None
    for c in candidates:
        if c and re.fullmatch(r"[A-Za-z0-9_.#+-]{1,40}", c):
            alias = c
            break
    if not alias:
        alias = re.sub(r"[^A-Za-z0-9_.#+-]+", "-", name.lower())[:40]
    prefix = comment_prefix_for(ext, fname)
    template = {
        "#": MODELINE_PREFIX["hash"][1],
        "//": MODELINE_PREFIX["slash"][1],
        "--": MODELINE_PREFIX["dash"][1],
        ";": MODELINE_PREFIX["semi"][1],
        "/*": MODELINE_PREFIX["block"][1],
        "<!--": MODELINE_PREFIX["html"][1],
    }.get(prefix, MODELINE_PREFIX["hash"][1])
    return alias, template


def pick_extension(entry: dict, exclusive: set) -> str:
    exts = [
        e for e in (entry.get("extensions") or [])
        if e and SAFE_EXT.match(e) and "/" not in e and "\\" not in e
    ]
    if not exts:
        return ""
    # prefer an extension no other core language claims, then the shortest
    exts = sorted(exts, key=lambda e: (e not in exclusive, len(e)))
    return exts[0]


def main() -> int:
    linguist = load(DATA / "linguist.json", []) or []
    merged = load(DATA / "merged_langs.json", []) or []
    merged_by_name = {m["name"].lower(): m for m in merged}

    colored = [e for e in linguist if e.get("color")]
    print(f"linguist languages with a colour: {len(colored)}")

    # Which extensions are claimed by exactly one coloured language?
    claims: dict[str, int] = defaultdict(int)
    for e in colored:
        for ext in e.get("extensions") or []:
            claims[ext] += 1
    exclusive = {ext for ext, n in claims.items() if n == 1}

    records = []
    deferred = []
    for e in colored:
        rgb = hex_to_rgb(e.get("color"))
        if not rgb:
            continue
        h, l, s = colorsys.rgb_to_hls(*[c / 255.0 for c in rgb])
        hue = round(h * 360.0, 2)
        slug = slugify(e["name"])
        ext = pick_extension(e, exclusive)
        fname = None
        if not ext:
            names = [f for f in (e.get("filenames") or []) if f]
            if names:
                fname = names[0]
                ext = Path(fname).suffix
        alias, prefix = modeline_for(e, ext, fname)
        mm = merged_by_name.get(e["name"].lower(), {})
        records.append(
            {
                "name": e["name"],
                "slug": slug,
                "color": (e["color"] or "").lstrip("#").lower(),
                "rgb": list(rgb),
                "hue": hue,
                "hue_bucket": classify(hue),
                "saturation": round(s, 4),
                "lightness": round(l, 4),
                "extension": ext,
                "filename": fname,
                "modeline_alias": alias,
                "modeline_prefix": prefix,
                "extension_exclusive": ext in exclusive or fname is not None,
                "type": e.get("type"),
                "ace_mode": e.get("ace_mode"),
                "tm_scope": e.get("tm_scope"),
                "interpreters": e.get("interpreters") or [],
                "aliases": e.get("aliases") or [],
                "all_extensions": e.get("extensions") or [],
                "path": f"hello/core/{slug}/hello{ext}",
                "sources": mm.get("source", ["linguist"]),
                "is_core": True,
            }
        )

    # de-duplicate slugs defensively (generator uses the same scheme)
    used: set[str] = set()
    for r in records:
        base = r["slug"]
        slug, n = base, 1
        while slug in used:
            slug = f"{base}-{n}"
            n += 1
        used.add(slug)
        r["slug"] = slug
        fname = r.get("filename")
        r["path"] = (
            f"hello/core/{slug}/{fname}" if fname else f"hello/core/{slug}/hello{r['extension']}"
        )

    records.sort(key=lambda r: (r["hue"], r["lightness"], r["name"].lower()))

    n = len(records)
    if n > MAX_CORE:
        print(f"! {n} > {MAX_CORE}: trimming the least saturated entries")
        records.sort(key=lambda r: (r["hue"], -r["saturation"]))
        records = records[:MAX_CORE]
        records.sort(key=lambda r: (r["hue"], r["lightness"], r["name"].lower()))
        n = len(records)

    per = 100.0 / n if n else 0.0
    for r in records:
        r["target_percent"] = round(per, 6)

    payload = {
        "generated_by": "scripts/select_rainbow_langs.py",
        "core_count": n,
        "target_percent_each": round(per, 6),
        "hue_order": "ascending HSL hue",
        "min_core": MIN_CORE,
        "max_core": MAX_CORE,
        "deferred_to_full_layer": deferred,
        "languages": records,
    }
    (CONFIG / "rainbow_langs.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    (CONFIG / "core-langs.txt").write_text(
        "\n".join(r["name"] for r in records) + "\n", encoding="utf-8"
    )

    buckets = Counter(r["hue_bucket"] for r in records)
    types = Counter(r["type"] for r in records)
    no_ext = [r["name"] for r in records if not r["extension"]]
    by_name = [r["name"] for r in records if r.get("filename")]
    lines = []
    lines.append("core language selection report")
    lines.append("=" * 60)
    lines.append(f"core languages              : {n}")
    lines.append(f"target share per language   : {per:.4f} %")
    lines.append(f"recognised by filename only : {len(by_name)}")
    lines.append(f"deferred to full layer      : {len(deferred)} -> {', '.join(deferred)}")
    lines.append(f"languages without extension : {len(no_ext)}")
    lines.append(f"                            : {', '.join(no_ext)}")
    lines.append("")
    lines.append("hue buckets (18 named slices of the colour wheel)")
    for edge, label in HUE_BUCKETS[:-1]:
        lines.append(f"  {label:<16} {buckets.get(label, 0):>4}")
    lines.append("")
    lines.append("linguist types")
    for k, v in types.most_common():
        lines.append(f"  {str(k):<16} {v:>4}")
    lines.append("")
    lines.append("first 20 by hue (start of the bar)")
    for r in records[:20]:
        lines.append(f"  {r['color']}  hue={r['hue']:>6.2f}  {r['name']}")
    lines.append("")
    lines.append("last 20 by hue (end of the bar)")
    for r in records[-20:]:
        lines.append(f"  {r['color']}  hue={r['hue']:>6.2f}  {r['name']}")
    report = "\n".join(lines) + "\n"
    (LOGS / "rainbow_selection.txt").write_text(report, encoding="utf-8")
    print(report)
    print(f"wrote config/rainbow_langs.json ({n} core languages)")
    if n < MIN_CORE:
        print(f"! only {n} core languages (< {MIN_CORE})")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
