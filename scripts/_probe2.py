import json, sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
L = json.load(open("data/linguist.json", encoding="utf-8"))
claims = defaultdict(set)
for e in L:
    if e.get("color"):
        for x in e.get("extensions") or []:
            claims[x].add(e["name"])

for name in ("Java", "C", "OCaml", "Rust", "Markdown", "CSV", "AsciiDoc"):
    for e in L:
        if e["name"] == name:
            print(f"{name:<10} colour={e.get('color')} exts={e.get('extensions')}")
            for x in e.get("extensions") or []:
                print(f"           {x:<14} exclusive={claims[x] == {name}} sharers={sorted(claims[x])}")
