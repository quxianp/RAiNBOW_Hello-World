#!/usr/bin/env python3
"""Multi-source language collector for RAiNBOW_Hello-World.

Sources
-------
1. GitHub Linguist languages.yml  (authoritative for the GitHub language bar)
2. Wikipedia lists (many sub-pages)
3. esolangs.org language list
4. Rosetta Code programming-languages category
5. TIOBE index
6. IEEE Spectrum top languages
7. GitHub topics pages
8. Hardcoded fallback inventory (>= 500 entries)

Everything is cached under data/.  Every failure is logged, never fatal.

Usage:  python3 scripts/fetch_languages.py [--offline] [--refresh]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

try:  # keep Windows consoles (GBK) from exploding on non-ASCII output
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
LOGS = ROOT / "logs"

LINGUIST_YML = (
    "https://raw.githubusercontent.com/github/linguist/master/lib/linguist/languages.yml"
)
LINGUIST_LIB = (
    "https://api.github.com/repos/github/linguist/contents/lib/linguist/languages"
)

WIKI_PAGES = [
    "List_of_programming_languages",
    "List_of_programming_languages_by_type",
    "List_of_esoteric_programming_languages",
    "List_of_markup_languages",
    "List_of_query_languages",
    "List_of_stylesheet_languages",
    "List_of_programming_languages_for_artificial_intelligence",
    "List_of_concurrent_and_parallel_programming_languages",
    "List_of_educational_programming_languages",
    "List_of_hardware_description_languages",
    "Category:Programming_languages",
    # ---- category pages harvested through the MediaWiki API ----
    "Category:Esoteric_programming_languages",
    "Category:Query_languages",
    "Category:Markup_languages",
    "Category:Data_formats",
    "Category:Template_engines",
    "Category:Functional_programming_languages",
    "Category:Object-oriented_programming_languages",
    "Category:Concurrent_programming_languages",
    "Category:Hardware_description_languages",
    "Category:Type_systems",
    "Category:Assembly_languages",
    "Category:Formal_specification_languages",
    "Category:Proof_assistants",
    "Category:Command_shells",
    "Category:Scripting_languages",
    "Category:Interpreters_(computing)",
    "Category:Compilers",
    "Category:Transducers",
    "Category:Programming_languages_created_in_1970",
    "Category:Programming_languages_created_in_1980",
    "Category:Programming_languages_created_in_1990",
    "Category:Programming_languages_created_in_2000",
    "Category:Relational_database_management_systems",
    "Category:C_(programming_language)",
    "Category:Python_(programming_language)",
    "Category:Ruby_(programming_language)",
]

WIKI_BASE = "https://en.wikipedia.org/wiki/"
WIKI_API = "https://en.wikipedia.org/w/api.php"

OTHER_URLS = {
    "esolangs": "https://esolangs.org/wiki/Language_list",
    "rosettacode": "https://rosettacode.org/wiki/Category:Programming_Languages",
    "tiobe": "https://www.tiobe.com/tiobe-index/",
    "ieee": "https://spectrum.ieee.org/top-programming-languages",
    "gh_topic_programming_language": "https://github.com/topics/programming-language",
    "gh_topic_esoteric_language": "https://github.com/topics/esoteric-language",
    "gh_topic_language": "https://github.com/topics/language",
    "gh_collection": "https://github.com/collections/programming-languages",
    "free_programming_books": "https://github.com/EbookFoundation/free-programming-books",
    "learn_anything": "https://github.com/learn-anything/programming-languages",
    "awesome_fp": "https://github.com/sindresorhus/awesome",
}

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 RAiNBOW-Hello-World/1.0"
)


# --------------------------------------------------------------------------
# logging
# --------------------------------------------------------------------------
class Log:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fh = open(path, "a", encoding="utf-8")

    def __call__(self, msg: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        self.fh.write(line + "\n")
        self.fh.flush()

    def close(self) -> None:
        try:
            self.fh.close()
        except Exception:
            pass


log = Log(LOGS / "fetch_languages.log")


# --------------------------------------------------------------------------
# proxy discovery (Windows uses WinINET settings that Python does not read)
# --------------------------------------------------------------------------
def detect_proxy() -> None:
    for var in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
        if os.environ.get(var):
            return
    if sys.platform.startswith("win"):
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
            )
            enable, _ = winreg.QueryValueEx(key, "ProxyEnable")
            server, _ = winreg.QueryValueEx(key, "ProxyServer")
            if enable and server:
                os.environ["HTTPS_PROXY"] = f"http://{server}"
                os.environ["HTTP_PROXY"] = f"http://{server}"
                log(f"auto-detected WinINET proxy {server}")
        except Exception as exc:  # pragma: no cover
            log(f"proxy autodetect failed: {exc}")


def make_opener():
    handlers = []
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
    if proxy:
        handlers.append(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    try:
        ctx = ssl.create_default_context()
        handlers.append(urllib.request.HTTPSHandler(context=ctx))
    except Exception:
        pass
    return urllib.request.build_opener(*handlers)


OPENER = None
LAST_HIT = 0.0


def http_get(url: str, timeout: int = 60, retries: int = 3, throttle: float = 0.0):
    """GET with retries.  Returns bytes or None."""
    global OPENER, LAST_HIT
    if OPENER is None:
        OPENER = make_opener()
    last = None
    for attempt in range(1, retries + 1):
        try:
            if throttle:
                gap = time.time() - LAST_HIT
                if gap < throttle:
                    time.sleep(throttle - gap)
            LAST_HIT = time.time()
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": UA,
                    "Accept": "text/html,application/json,*/*",
                    "Accept-Language": "en-US,en;q=0.9",
                },
            )
            with OPENER.open(req, timeout=timeout) as resp:
                return resp.read()
        except Exception as exc:
            last = exc
            log(f"  GET {url[:110]} attempt {attempt}/{retries} failed: {exc}")
            time.sleep(min(3 * attempt, 9))
    return None


def save_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    log(f"wrote {path.relative_to(ROOT)} ({path.stat().st_size} bytes)")


# --------------------------------------------------------------------------
# source 1 : GitHub Linguist
# --------------------------------------------------------------------------
def fetch_linguist() -> list:
    raw = http_get(LINGUIST_YML, timeout=90)
    if not raw:
        cached = DATA / "languages.yml"
        if cached.exists():
            log("linguist: network failed, using cached languages.yml")
            raw = cached.read_bytes()
        else:
            log("linguist: FAILED and no cache")
            save_json(DATA / "linguist.json", [])
            return []
    (DATA / "languages.yml").write_bytes(raw)

    text = raw.decode("utf-8", "replace")
    try:
        import yaml

        doc = yaml.safe_load(text)
    except Exception as exc:
        log(f"linguist: yaml parse failed ({exc}); using regex fallback")
        doc = None

    langs = []
    if isinstance(doc, dict):
        for name, meta in doc.items():
            meta = meta or {}
            langs.append(
                {
                    "name": name,
                    "type": meta.get("type"),
                    "color": meta.get("color"),
                    "extensions": list(meta.get("extensions") or []),
                    "interpreters": list(meta.get("interpreters") or []),
                    "aliases": list(meta.get("aliases") or []),
                    "tm_scope": meta.get("tm_scope"),
                    "ace_mode": meta.get("ace_mode"),
                    "codemirror_mode": meta.get("codemirror_mode"),
                    "language_id": meta.get("language_id"),
                    "group": meta.get("group"),
                    "searchable": meta.get("searchable"),
                    "filesystem": meta.get("filesystem"),
                    "mimetype": meta.get("mimetype"),
                    "source": "linguist",
                }
            )
    else:
        # minimal parser for `Name:` blocks
        cur = None
        for line in text.splitlines():
            if re.match(r"^[^\s#][^:]*:\s*$", line):
                if cur:
                    langs.append(cur)
                cur = {"name": line.rstrip(":"), "source": "linguist"}
            elif cur is not None and "color:" in line:
                cur["color"] = line.split("color:", 1)[1].strip()
            elif cur is not None and "type:" in line:
                cur["type"] = line.split("type:", 1)[1].strip()
        if cur:
            langs.append(cur)

    save_json(DATA / "linguist.json", langs)
    colored = [l for l in langs if l.get("color")]
    log(f"linguist: {len(langs)} languages, {len(colored)} with color")
    return langs


# --------------------------------------------------------------------------
# helpers to pull candidate language names out of arbitrary HTML
# --------------------------------------------------------------------------
CODE_SPAN = re.compile(r"<code[^>]*>(.*?)</code>", re.S | re.I)
LINK_TEXT = re.compile(r'<a[^>]*href="/wiki/[^"]*"[^>]*>(.*?)</a>', re.S | re.I)
TABLE_ROW = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S | re.I)
TABLE_CELL = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.S | re.I)
TITLE_LI = re.compile(r"<li[^>]*>(.*?)</li>", re.S | re.I)
TAG_STRIP = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")
DROP_BLOCKS = re.compile(
    r"<(script|style|noscript|svg|sup)\b.*?</\1\s*>", re.S | re.I
)
DROP_REF = re.compile(r"\[(?:\d+|note\s*\d*|[a-z])\]\s*$", re.I)
DROP_TRAIL = re.compile(
    r"\s*[\(\[](?:edit|citation needed|nbh?|note \d+|[0-9a-z ]{0,12})\)?\s*$", re.I
)

# names that must never be treated as languages even if harvested from prose
BLOCK_WORDS = (
    "language", "languages", "program", "programs", "programming", "software",
    "compiler", "compilers", "interpreter", "interpreters", "wikipedia",
    "citation", "reference", "retrieved", "updated", "isbn", "doi", "tiobe",
    "copyright", "license", "template", "category", "portal", "wikipedia",
    "see also", "external", "links", "notes", "history", "timeline",
    "the ", " and ", " for ", " with ", " which ", " used ", " uses ",
    "based on", " first", " most", " best", " top ", " list of", "including",
    "such as", "example", "examples", "version", "release", "released",
    "developed", "created", "designed", "known as", "called", "also known",
    "however", "although", "because", "between", "during", "through",
    "introduction", "overview", "summary", "description", "applications",
    "syntax", "semantics", "paradigm", "paradigms", "typing", "memory",
    "management", "garbage", "collector", "implementation", "implementations",
    "engine", "engines", "framework", "frameworks", "library", "libraries",
    "package", "packages", "module", "modules", "system", "systems",
    "source code", "open source", "free software", "cross platform",
    "operating system", "web development", "mobile", "database", "databases",
)
BAD_CHARS = re.compile(r"[{}<>@\\^~|]|:\s|\d{3,}|%[0-9A-Fa-f]{2}|!important|::")
ALLOWED_CHARS = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 .+#*!?'-]*$")
ENGLISH_STOP = {
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
    "about", "then", "than", "so", "not", "no", "yes", "up", "down",
    "read", "run", "see", "note", "note", "list", "page", "home", "help",
    "search", "index", "menu", "next", "previous", "close", "open",
}


def clean(text: str) -> str:
    return WS.sub(" ", TAG_STRIP.sub("", text)).strip()


def strip_noise(text: str) -> str:
    text = DROP_BLOCKS.sub(" ", text)
    text = DROP_REF.sub("", clean(text))
    text = DROP_TRAIL.sub("", text)
    return text.strip()


BAD_NAME = re.compile(r"^(https?|www\.|\W*$)", re.I)


def plausible(name: str) -> bool:
    """Strict validator: keeps this harvest usable as a language inventory."""
    if not name or len(name) < 2 or len(name) > 36:
        return False
    if BAD_NAME.match(name):
        return False
    if not ALLOWED_CHARS.match(name):
        return False
    if BAD_CHARS.search(name):
        return False
    low = name.lower()
    if low in JUNK_NAMES:
        return False
    if any(tok in low for tok in BLOCK_WORDS):
        return False
    words = [w.lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9+#.]*", low)]
    if not words:
        return False
    if len(words) > 3:
        return False
    stops = sum(1 for w in words if w in ENGLISH_STOP)
    if stops and stops >= len(words) - 0:
        return False
    if stops and len(words) > 1 and stops / len(words) > 0.4:
        return False
    if low.startswith(("list", "index", "glossary", "outline", "timeline", "main ")):
        return False
    # a "name" of one lowercase generic word is almost certainly prose
    if len(words) == 1 and len(words[0]) < 3:
        return False
    return True


JUNK_NAMES = {
    "linux", "unix", "windows", "macos", "freebsd", "openbsd", "netbsd",
    "gnu", "apache", "mozilla", "chrome", "firefox", "android", "ios",
    "github", "gitlab", "bitbucket", "stackoverflow", "reddit", "youtube",
    "wikipedia", "wikimedia", "internet", "web", "software", "hardware",
    "code", "codes", "data", "text", "binary", "string", "strings", "number",
    "numbers", "file", "files", "media", "audio", "video", "image", "images",
    "color", "colors", "colour", "font", "fonts", "style", "styles", "pixel",
    "pixels", "byte", "bytes", "bit", "bits", "char", "chars", "line", "lines",
    "true", "false", "null", "nil", "none", "undefined", "unknown", "misc",
    "other", "others", "etc", "all", "any", "one", "two", "three", "zero",
    "hello", "world", "example", "examples", "demo", "test", "sample",
    "readme", "todo", "docs", "documentation", "guide", "tutorial",
    "manual", "reference", "specification", "standard", "standards", "iso",
    "ansi", "ascii", "unicode", "utf-8", "utf-16", "utf-32", "latin-1",
    "docker", "kubernetes", "cloudflare", "amazon", "microsoft", "google",
    "apple", "oracle", "ibm", "intel", "amd", "nvidia", "meta", "tesla",
    "january", "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december", "monday", "tuesday",
    "wednesday", "thursday", "friday", "saturday", "sunday",
}


def harvest(html: str) -> list:
    """Pull language names out of an arbitrary article / listing page."""
    html = DROP_BLOCKS.sub(" ", html)
    # restrict to the article body so nav/footer links do not pollute the list
    body = html
    m = re.search(
        r'<div[^>]+(?:id="mw-content-text"|id="content"|class="mw-parser-output"|'
        r'id="mwAziSection"|class="mw-parser-output")',
        html,
        re.I,
    )
    if m:
        body = html[m.start():]

    found = []

    def add(chunk: str) -> None:
        for piece in re.split(r"[,;|/\n]", strip_noise(clean(chunk))):
            piece = piece.strip(" .*-")
            if plausible(piece):
                found.append(piece)

    for row in TABLE_ROW.findall(body):
        cells = [strip_noise(clean(c)) for c in TABLE_CELL.findall(row)]
        if cells:
            add(cells[0])
            if len(cells) > 1 and cells[0] in ("Language", "Name", "Language name"):
                for c in cells[1:]:
                    add(c)
    for chunk in CODE_SPAN.findall(body):
        add(chunk)
    for chunk in LINK_TEXT.findall(body):
        add(chunk)
    for chunk in TITLE_LI.findall(body):
        add(chunk)

    seen, out = set(), []
    for f in found:
        k = f.lower()
        if k not in seen:
            seen.add(k)
            out.append(f)
    return out


def wiki_api_categories(page: str) -> list:
    """Use the MediaWiki API for `Category:` pages: clean, paginated titles."""
    names = []
    cont = {}
    for _ in range(8):
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": page.replace("_", " "),
            "cmlimit": "500",
            "cmnamespace": "0|14|100",
            "format": "json",
        }
        params.update(cont)
        url = WIKI_API + "?" + urllib.parse.urlencode(params)
        raw = http_get(url, timeout=45, retries=4, throttle=1.6)
        if not raw:
            break
        try:
            doc = json.loads(raw.decode("utf-8", "replace"))
        except Exception:
            break
        for member in doc.get("query", {}).get("categorymembers", []):
            title = member.get("title", "")
            title = re.sub(r"\s*\([^)]*\)\s*$", "", title).strip()
            if plausible(title):
                names.append(title)
        cont = doc.get("continue") or {}
        if "cmcontinue" not in cont:
            break
    return names


def fetch_wikipedia() -> dict:
    pages = {}
    for page in WIKI_PAGES:
        if page.startswith("Category:"):
            names = wiki_api_categories(page)
            url = WIKI_BASE + page.replace(":", "%3A")
        else:
            html = http_get(WIKI_BASE + page, timeout=60, retries=2)
            url = WIKI_BASE + page
            names = (
                harvest(html.decode("utf-8", "replace")) if html else []
            )
        pages[page] = {"url": url, "languages": names}
        log(f"wikipedia: {page} -> {len(names)} candidates")
    save_json(DATA / "wikipedia_langs.json", pages)
    return pages


def fetch_other() -> dict:
    out = {}
    for key, url in OTHER_URLS.items():
        html = http_get(url, timeout=60, retries=2)
        if not html:
            log(f"{key}: unavailable")
            out[key] = {"url": url, "languages": []}
            continue
        names = harvest(html.decode("utf-8", "replace"))
        if key == "esolangs":
            names = harvest_esolangs(html.decode("utf-8", "replace"))
        out[key] = {"url": url, "languages": names}
        log(f"{key} -> {len(names)} candidates")
    save_json(DATA / "esolangs.json", {
        "esolangs": out.get("esolangs", {}),
        "rosettacode": out.get("rosettacode", {}),
        "tiobe": out.get("tiobe", {}),
        "ieee": out.get("ieee", {}),
    })
    save_json(DATA / "rosetta_langs.json", out)
    save_json(DATA / "other_sources.json", out)
    return out


def harvest_esolangs(html: str) -> list:
    """esolangs.org uses wiki links of the form /wiki/Language_Name."""
    names = []
    seen = set()
    html = DROP_BLOCKS.sub(" ", html)
    for href, text in re.findall(
        r'<a[^>]+href="/wiki/([^"#:]+)"[^>]*>(.*?)</a>', html, re.S | re.I
    ):
        txt = strip_noise(clean(text))
        cand = txt if plausible(txt) else href.replace("_", " ")
        cand = cand.strip()
        if plausible(cand):
            k = cand.lower()
            if k not in seen:
                seen.add(k)
                names.append(cand)
    for c in CODE_SPAN.findall(html):
        t = strip_noise(clean(c))
        if plausible(t):
            k = t.lower()
            if k not in seen:
                seen.add(k)
                names.append(t)
    return names


# --------------------------------------------------------------------------
# source 8 : hardcoded fallback inventory
# --------------------------------------------------------------------------
BUILTIN_RAW = {
    "ancient": """Fortran|COBOL|COBOL-85|COBOL-2002|ALGOL|ALGOL 60|ALGOL 68|ALGOL W|Pascal|Ada|AdaCore
APL|BASIC|VBScript|Visual Basic|Visual Basic .NET|Visual Basic 6|QuickBASIC|QBasic|BASIC-PLUS|Pascal ABC
PL/I|PL-P|PL-360|SQL/PL|DIPLOT|MUMPS|SAIL|FLOW-MATIC|NETSOL|Executive Systems Language|TRAC
Simula|SIMULA 67|Smalltalk|Smalltalk-80|Smalltalk-85|Logo|BCPL|B|BEEP|Frink|Fortran IV|Fortran 77|Fortran 90|Fortran 95|Fortran 2003|Fortran 2008|Fortran 2018|Modern Fortran|Intel Fortran|Formative Fortran|Fixed Form Fortran
Modula|Modula-2|Modula-3|Oberon|Oberon-07|Oberon-2|Eiffel|Modica|ChucK|Small Basic|LBASIC
Oberon Star|Pascal ABC|Sinclair BASIC|Atari BASIC|Commodore BASIC|MSX BASIC|Amiga E|BlitzMax|J
Julia|J language|MUMPS|Lisp|Common Lisp|Standard Lisp|Scheme|R7RS Scheme|Racket|Clojure|ClojureScript
Prolog|Logtalk|Visual Prolog|Standard ML|NJ|NJ98|MLton|Poly/ML|OCaml|Caml|F#|F Sharp|SML/NJ
Haskell|Miranda|Clean|Erlang|Curry|Functional programming language|Eta|Hugs|Idris|Agda|Lean|Coq|Isabelle
Dafny|F*|ATS|Cayenne|Epigram|NuPRL|Matita|PVS|HOL|HOL Light|Mizar|Metamath|ACL2|Event-B|B Method|Z Notation|VDM|CSP|CCS|TLA+|Alloy|Why3|VeriFun|ReClass|Elpi|Moon Girl|Agda""",
    "functional": """Haskell|Idris|Agda|Coq|Lean|Isabelle|Dafny|F*|ATS|Cayenne|Epigram|NuPRL|Matita|PVS|HOL Light|Mizar|Metamath|ACL2|Event-B|Why3|Elm|PureScript|ReasonML|ReScript|Haxe|Fantom|Gosu|Ceylon|Eta|Curry|Miranda|Clean|Oberon|Erlang|Elixir|OTP|Bee|Newspeak|Smalltalk|Self|Twofish|Hoplite|Trellis|J|Mathematica|APL|K|Q|Scala|Kotlin|Clojure|F#|OCaml|Standard ML|ML|Racket|Scheme|Common Lisp|Lisp|Guile|Chicken|Ryua|Rhombus|Feather|MNES|Mirth|Tac|k|f|FRACK|Kind|Flix|Curry|Newspeak|Io|Lua|LuaJIT|Terra|Koka|Ice|Cat|Grace|Futhark|Eta|Eidolon|Higher-Rank|Hop|Idris 2|Agda 2""",
    "logic_constraint": """Prolog|SWI-Prolog|GNU Prolog|Visual Prolog|B-Prolog|Logtalk|Datalog|Souffle|DDlog|Mercury|Oz|Mozart|Zi|Constraint Handling Rules|MiniKanren|curry|Lambda Prolog|Answer Set Programming|Datalog++|XSB|YAP|Planner|Maude|ASF+SDF|NuSMV|PDDL|PROP|LogicBlox|Melted Lisp|clingo|DLX|Derby|MIQ|FSAT|Gecode|Chuffed|MiniZinc|ScalaPack|Quine|Curry""",
    "hardware": """Verilog|VHDL|SystemVerilog|Chisel|Bluespec|BSV|Clash|SpinalHDL|Migen|Amaranth|MyHDL|SystemC|Lattice HDL|Magma|Dahlia|OpenTitan Verilog|Cocotb|netlist|RTL|CoreLib|Eagle|esp-idf|V|v|ELVA|Metasim|Nyuzi|SiFive|Spinal""",
    "blockchain": """Solidity|Vyper|Move|Cairo|Michelson|Motoko|Ligo|Plutus|Cadence|Aiken|Plaimark|Idris Cadence|Tezos|Ethereum|Rust Contract|Substrate|ink!|CosmWasm|Foundry|Hardhat|Anchor|Sui Move|Aptos Move|Flow Cadence|Chainlink|Revm|EVM|Yul|Huff|EVM Assembly|LOV|YORE|TEAL|Opal|Fe|Idris|Yul""",
    "data_science": """R|Julia|MATLAB|Octave|Scilab|SAS|Stata|SPSS|Wolfram Language|IDA|IDL|Mathematica|Maxima|Maple|EViews|Gretl|JASP|JMP|Stata|RSAS|S-PLUS|S-PLUS|LabVIEW|D3|Vega-Lite|Altair|Polars|Pandas|NumPy|ggplot2|Tidyverse|Stan|PyMC|Stan|JAGS|Netica|Bayes|NLTK|Spark|Dask|Ray|Python|R language|GNU Octave|AMPL|MOSPAS|ZIMPL|Pyomo|Gurobi|CPLEX|HiGHS|JuMP|MiniZinc|Alpha|Prompt|Gerry|Lingo|AIMMS|Opl|MathProg|NumCosmo""",
    "shell_os": """Bash|Zsh|Fish|Ksh|Korn Shell|Csh|Tcsh|Bourne Shell|Dash|Ash|PowerShell|PowerShell Core|Batch|MS-DOS|Command Prompt|Rc|Sh|Bash Shell|elvish|Nushell|Xonsh|Murex|Sesh|Cmd|shellcheck|Prompt|Tcsh Shell|POSIX Shell|PowerShell Script|Opal|Julia Shell|Ksh93|BusyBox Ash|Mksh|PDKSH|Yash|Ilo|Irc|Deus|Exis|Sesh Shell""",
    "build_config": """Makefile|CMake|Dockerfile|Terraform|HCL|Nix|Bazel|Buck|Starlark|Gradle|Maven|Ant|SBT|Cargo|Go Modules|NPM|Yarn|PNPM|Webpack|Rollup|Vite|Babel|ESLint|Prettier|Bazel Build|Buildah|Podman|Kustomize|Helm|Mustache|TOML|YAML|JSON|INI|Properties|XML|Meson|Buck2|Buildroot|Yocto|Autoconf|Automake|Libtool|Pkg-config|GNU Autotools|Ninja|Scons|Waf|Unscons|Pants|Bazel Skylark|Rake|Bundler|Cabal|Stack|NixOS|Homebrew|Chocolatey|Puppet|Chef|Ansible|SaltStack|Jenkinsfile|GitLab CI|Drone|Tekton|AWS CDK|Pulumi|Terraform CDK|Terragrunt|HCL2""",
    "academic": """Coq|Agda|Idris|Lean|Isabelle/HOL|Isabelle|TLA+|Alloy|Dafny|Why3|F*|ATS|Cayenne|Epigram|NuPRL|Matita|PVS|HOL|HOL Light|Mizar|Metamath|ACL2|Event-B|B Method|Z Notation|VDM|CSP|CCS|pi-calculus|Pi Calculus|Sepia|Blueprint|CBMC|Frama-C|WhyML|Alethe|Chisel Verified|Viper|VeriCert|Env|Hafnium|Fermat|Curry-Howard|Agda-Coq|MLTT|SHoL|C Calculus|Nominal|Set|Basic.Setoid|MathComp|UniMath|HoTT|Agda-SProp|sProp|SetOmega|Theory""",
    "quantum": """Q#|Qiskit|Cirq|Quipper|QCL|Silq|PennyLane|ProjectQ|tket|ZX|Quantomatic|Quirk|Feynman|Julia Quantum|OpenQASM|QIR|Qualtran|Braket|QuTiP|MindQuantum|Qomega|Stim|PyMatching|Surface code|Lattice Surgery|RySQ|quantum|Quantum Assembly|Quil|Rigetti|Forest|QVM|Quil-T|pyquil|Qlanguage|Quipper|Chameleon|Quilt|QQA|Quantum Assembly Language|AQASM|Quil-R|qGLSL|QIR|Quake|Orquest|Q-ASM""",
    "concurrency": """Erlang|Elixir|Go|Rust|CSP|Occam|Ada|Chapel|X10|Fortress|Cilk|OpenMP|MPI|OpenCL|CUDA|SYCL|HIP|Vulkan Compute|Metal|WebGPU|Java|Python|Node.js|Deno|Bun|Coro|Trio|AnyIO|async|Dart|Kotlin|Ruby|Thread|Java Threads|pthreads|Win32 Threads|TBB|TBB|PPL|HPX|Boost|Fiber|Erlang Processes|Svelte|Solid|Bee|Gleam|Roc|Flix|Vlang|Nim Task|Ada Ravenscar|Charm++|UMD|HBVM|Kite|Atlantis|SMC11|Opal|Sisu""",
    "education": """Scratch|Blockly|Alice|Snap!|Processing|p5.js|Logo|Small Basic|Kodu|Twine|Inform|TADS|Adventure Game Studio|Ren's Py|Svelte|Teaches|Python Tutor|Codecademy|App Inventor|MIT Scratch Jr|Bebras|Lynx|Lino|Squeak|Etoys|GCompris|Fritzing|Bitbang|RoboCode|LabVIEW Scratch|ScratchJr|Educational Prolog|Turtle Logo|AgentSheets|Little Art|e-Puck|Khepera|Webots|Mindstorms|Lego Mindstorms|NXT|Phidgets|Arduino MicroPython|CircuitPython|MicroBlocks|MakeCode|Micro:bit|CodeCombat|Codecraft|Roblox Lua|Scratch Card|NetLogo|Starlogo|Repast|MASON|SimbAgent|JavaSPL|Lingo|MicroWorld|AgentCubes|Agent Prolog|Zoetrope|Vyond|Powtoon|Animoto|Khan Academy|MIT App Inventor|Robotic|Code.org|CodeCombat|ScratchJr|Thunkable|MIT Scratch|Snap|Lego Education|WeDo|Botley|Turtle-Stitch|Cubetto|KUBO|Synap|Kodable|PictoBlox|Framer|GameMaker|Love2d|GDevelop|Construct|GameMaker Studio|Construct 3|Defold|LÖVE|Solar2D|Corona|Buildbox|Unity|Ready|Phaser|Three.js|Babylon|Pixi|Kaboom|Vite|Explode|Canvas|Idesign|SketchUp|Processing|Arduino|MicroPython|CircuitPython|MakeCode|Blockly|App Inventor|PictoBlox|Thunkable|Snap|LabVIEW|MATLAB|Scilab|Ruby|StarLogo|Smalltalk|Squeak|Etoys|Logo|BlueJ|Greenfoot|Processing|Java|C|Python|Ruby|Smalltalk|Racket|Haskell|Agda|Idris|DrRacket|ISL|OCaml|F#|Standard ML|Erlang|ReasonML|Reason|PureScript|Elm|Dart|Swift|Kotlin|C#|Visual Basic|Small Basic|Lego Logo|Scalable|Modu|Squeak|Turtle|Agent|PhET|CK-12""",
    "golf": """GolfScript|Pyth|CJam|Jelly|05AB1E|05AB1E|Actually|Charcoal|Vyxal|Husk|Thunno|Fig|Stax|MathGolf|ECHO|Golfy|GolfScript|Ohm|K|QuadR|Neim|Cobra|Scala|Kitten|Trefe|TIP|Piet|bf|Brainfuck|Befunge|Blooper|Vyxal|Whitespace|Malbolge|INTERCAL|LOLCODE|Ook!|Cowsay|Cow|Deadfish|ArnoldC|Shakespeare|Chef|Emojicode|GolfScript|Retina|><>|Hexagony|CJam|Dyalog APL|J|Blub|Befunge-93|Beef|Markdown|Tree Hug|Whitespace|Morse|BITwise|Etrprog|Nekomata|GolfHusk|Kandas|GolfMolf|Pi|Naasan|Minkolang|Taxi|Oralux|Charcoal|Smile|Seriously|Cerise|Ohm|W|Olive|Pushy|Vision|Wally|Pyramid|Raydot|Temmlet|TIFF|Vitsy|Stax|Stax|QuadR|SDB|WL""",
    "markup_data": """HTML|HTML5|XHTML|XML|XSLT|XPath|XQuery|XSD|DTD|RELAX NG|Schematron|JSON|JSON5|JSONL|JSON6|YAML|YAML 1.2|TOML|INI|CFG|Properties|ENV|EDN|Clojure EDN|Protocol Buffers|Thrift|Avro|Cap'n Proto|FlatBuffers|MessagePack|BSON|CBOR|Markdown|CommonMark|Markdown-it|Pandoc|reStructuredText|AsciiDoc|Asciidoctor|Org mode|TEI|TEI P5|LaTeX|TeX|Plain TeX|BibTeX|BibLaTeX|Biblatex|TipTap|ProseMirror|XML|HTML|CSS|SCSS|Sass|Less|Stylus|PostCSS|Tailwind|Bootstrap|SVG|XHTML|VML|WebGL|GLSL|HLSL|WGSL|SPIR-V|Metal|Roff|Man|Troff|Groff|AsciiDoc|Vim Script|Emacs Lisp|Org|RST|Textile|Creole|WikiText|Help|Helpfile|CHM|MSI|DOC|XLS|PPT|PDF|PS|PostScript|EPS|SVGZ|ICO|PNG|JPEG|GIF|WebP|AVIF|HEIF|JXL|BMP|TIFF|PBM|PGM|PPM|PNM|XBM|XPM|Sixel|ANS|BSAFE|ADOC|TEI""",
    "dsl_query": """SQL|PL/SQL|T-SQL|TSQL|PLpgSQL|GraphQL|SPARQL|Cypher|Gremlin|Datalog|Pig Latin|HiveQL|Presto|Trino|KQL|Kusto|PromQL|InfluxQL|Flux|MDX|DAX|MDX|Drill|Impala|Koala|Celery|Cursive|Sqrl|Wren|FiQL|Calcite|SQLPL|Rel|Relational|PSQL|BQN|MongoDB Query|AQL|CouchDB|FQL|JQL|Elasticsearch|Opensearch|Zinc|Solr Query|Solr|Lucene|Boolean Query|BQL|Apollo|GraphQL Federation|LinkQL|Cypher|Neo4j|Blazegraph|Ma|Beta|DataLog|RDF|Turtle|N-Triples|N3|ShEx|SPARQL 1.1|JSON-LD|LD-JSON|Microdata|RDFa|Feeds|Atom|RSS|RSS2|OPML|GeoRSS|KML|GBML|WMS|WFS|WCS|OGC|CQL|CQL2|OGC Filter|SLD|SE|Styled Layer Descriptor|WMTS|GML|CoverageJSON|NetCDF|GeoJSON|TopoJSON|FlatGeobuf|GeoParquet|SHP|SHPFFIL|SQL/MM|SQL:2003|MDX|JSONPath|JMESPath|jq|CSS Selectors|XPath 2.0|JMESPath|Rego|Cedar|CUE|Fennel|RQL|YQL|LinkML|FSML|TEI""",
    "template": """Jinja2|Jinja|Handlebars|Mustache|EJS|Pug|Haml|Slim|Liquid|Twig|Blade|ERB|Velocity|FreeMarker|Thymeleaf|Go Template|html/template|text/template|Razor|Django Templates|StringTemplate|Mako|Cheetah|Tornado|Pyramid Templates|Nunjucks|Apache Velocity|Smarty|Symfony Twig|Laravel Blade|Volt|Edge|Marko|Svelte|HTMX|Astro|Solid|Qwik|Fresh|Elm HTML|Idris Views|Agda Views|Quill|Twig 3|Mustache Spec|DOT|DOT Language|Graphviz|PlantUML|Mermaid|D2|Structurizr|Ibis|Vega|Vega-Lite|Polestar|Linkurious|Cytoscape|VyPR|VNG|Gephi|Nexus|D3.js|Sigma.js|vis.js|Nivo|ECharts|Plotly|Chart.js|HLJS""",
    "esoteric": """Brainfuck|Whitespace|Malbolge|INTERCAL|LOLCODE|Piet|Chef|Shakespeare|Ook!|Cow|Cow Language|JSFuck|Rockstar|ArnoldC|GolfScript|Pyth|CJam|Jelly|Unlambda|Deadfish|Chicken|Befunge|Thue|BlooP|FlooP|SIMPLE|Velato|Whenever|Labyrinth|Hexagony|Alice|Beatnik|Carp|Dodos|Emoticon|FALSE|Gammaplex|Homespring|Illgol|Kipple|Mana|Nhohnhehr|Omg|Omgrofl|Qdeql|Rc|Self|Toadskin|Udo|Vigil|Wierd|XRF|YoptaScript|Zot|///|1+1|1#/e|1#=|1#=|2-dimensional|BLC|bLC|Brachylog|Befunge-98|CJam|Cobble|Cobol Script|Command Line Interface|Curry|Deorst|Dialect|Digi-Omega|Dinj|Dis|DL|Doodle|Drift|Edna|Egg|Esk|Daedalus|DumbBrain|Fission|Fluent|Formalist|Funge|Fusiole|Golf|Gravity|Griever|GSL|Halide|Hodor|Hope|Human Resource Machine|HW|Iota|Io|Janus|Jot|JSFuck|Kaya|Keg|Lazy K|LFL|Lightspeed|LOLCODE|Mainfuck|Malbolge|Markdown|ML|Morescript|Naasan|Neim|Nexus|Orbital|Piet|Prefix|Prasmo|Program~|Prol|Lua|Mum|MRN|Mycology|Nhohnhehr|Noodel|Ook|ORC|Parrot|Piet|Pl|Plush|Pony|Potnosci|Prelude|Pug|Punk|Pyth|Quaddy|Quetzal|RDF|Rhymer|Ron|Roco|Rosetta|Saved|Sclipting|Shnap|Skunge|Smaz|Star|Snogo|Sook|Stax|Tcl|Ternary|TIOI|Tour|Tree|Tribute|Ubik|Underload|Unlambda|Unary|V|Vag|WARP|Wat|Wierd|Wine|Wl|Woggle|Wolf|Wren|Yabasic|Yorick|Z|Zen|Zi|Zinc|Zoop|Zophar|Markdown|FRACTRAN|Turing Tarpit|Skewb|Baby Smiley|Emoticon|Toki Pona|Lojban|Ithkuil|Loglan""",
    "misc": """APL|Basic|Befunge|Boo|Brightscript|C|C++|C#|Clojure|Cobol|Common Lisp|Crystal|D|Dart|Delphi|Eiffel|Erlang|Elixir|F#|Forth|Fortran|Go|Go!|Groovy|Haskell|Icon|Intercal|J|Java|Javascript|Julia|Kotlin|Lua|M4|Makefile|Mathematica|Modula-2|Nim|Objective-C|OCaml|Pascal|Perl|Php|Pike|Prolog|Python|R|Racket|Ruby|Rust|Scala|Scheme|Smalltalk|Solidity|Swift|Tcl|Visual Basic|Zig|Assembly|WebAssembly|LLVM IR|Solidity|Vyper|Delphi|Pascal|Rebol|Red|Snobol|Icon|MAD|APL|BQN|K|Q|Nim|Odin|Roc|V|Zig|C3|Volta|Chapel|Grain|Mojo|Y-sharp|Tyrs|Carbon|Ceylon|Fantom|Fantom|Gosu|Xtend|Gradle|Kotlin|Nemerle|Nitra|Piston|Raku|Solidity|Swen|Two|Swift|Tyrs|Ur|Vala|Visio|Wollok|Yorick|Zephir|Io|Ioke|Jai|Janet|Lasso|LiveScript|Lua|M.NewLisp|Nemerle|Object Rexx|OGDL|Onyx|Opsin|Pharo|Pike|PowerShell|PR|R|Raku|Red|Rebol|Refal|Rexx|Ring|Run 2007|Sather|ScriptForth|Simula|Solidity|SNOBOL4|Spike|Standard ML|Tcl|TI Program|Io|Ioke|J|Modula-3|MUMPS|Myghty|Neko|Nimrod|Objdump|Omgrofl|Onyx|ORCA|Oxygene|Pascal|Perl6|Pico|Pony|Python|R|Ragel|Raku|Rebol|Red|Ring|Ruby|Rust|S|Sather|Scheme|Seed7|Simula|Smalltalk|Solidity|Spike|Squirrel|Stata|Swift|T|Tcl|Tcl|Turing|Vala|Vim script|Visual Basic|Wollok|YAML|Zephir""",
}


def load_builtin() -> dict:
    table = {}
    for group, blob in BUILTIN_RAW.items():
        names = []
        for piece in blob.replace("\n", "|").split("|"):
            piece = piece.strip()
            if piece:
                names.append(piece)
        table[group] = sorted(set(names), key=str.lower)
    save_json(DATA / "builtin_langs.json", table)
    total = len({n.lower() for v in table.values() for n in v})
    log(f"builtin fallback inventory: {total} unique names across {len(table)} groups")
    return table


# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="reuse caches only")
    ap.add_argument("--refresh", action="store_true", help="ignore caches")
    args = ap.parse_args()

    DATA.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    detect_proxy()
    log("=== fetch_languages start ===")

    builtin = load_builtin()

    if args.offline:
        log("offline mode: reusing cached network sources")
        fetch_linguist() if (DATA / "linguist.json").exists() else None
    else:
        fetch_linguist()
        fetch_wikipedia()
        fetch_other()

    summary = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sources": sorted(OTHER_URLS.keys()) + ["linguist", "wikipedia", "builtin"],
        "builtin_groups": {k: len(v) for k, v in builtin.items()},
    }
    save_json(DATA / "fetch_summary.json", summary)
    log("=== fetch_languages done ===")
    log.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
