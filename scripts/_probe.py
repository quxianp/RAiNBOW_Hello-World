import json, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = json.load(open("config/rainbow_langs.json", encoding="utf-8"))["languages"]
by = {r["name"]: r for r in R}
want = sys.argv[1:] or [
    "CSV", "AsciiDoc", "BibTeX", "ApacheConf", "EditorConfig", "Dotenv", "CSON",
    "Bison", "2-Dimensional Array", "AL", "ALGOL", "ACTIONScript", "Cairo Zero",
    "Elvish Transcript", "Browserslist", "Bluespec BH", "Ant Build System",
]
for n in want:
    r = by.get(n)
    if not r:
        print(f"{n}: NOT IN CORE LIST")
        continue
    p = Path(r["path"])
    ex = p.exists()
    first = p.read_text(encoding="utf-8").splitlines()[0] if ex else "<missing>"
    print(f"{n:<24} ext={r['extension']!r:<14} fname={r.get('filename')!r:<22} "
          f"alias={r.get('modeline_alias')!r:<22} exists={ex}  | {first[:60]}")
