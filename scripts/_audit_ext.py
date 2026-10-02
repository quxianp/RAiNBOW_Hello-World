import json, sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

L = json.load(open("data/linguist.json", encoding="utf-8"))
colored = [e for e in L if e.get("color")]
R = json.load(open("config/rainbow_langs.json", encoding="utf-8"))["languages"]
byname = {e["name"]: e for e in colored}

claims = defaultdict(set)
nameclaims = defaultdict(set)
for e in colored:
    for x in e.get("extensions") or []:
        claims[x].add(e["name"])
    for f in e.get("filenames") or []:
        nameclaims[f].add(e["name"])

rows = []
for r in R:
    e = byname.get(r["name"])
    ext = r["extension"]
    fn = r.get("filename")
    sharers = set()
    if fn:
        sharers |= nameclaims.get(fn, set())
    else:
        sharers |= claims.get(ext, set())
    sharers.discard(r["name"])
    rows.append((len(sharers), r["name"], ext, fn, sorted(sharers)[:5]))

rows.sort(reverse=True)
print("core languages whose identifier is SHARED with other coloured languages:")
shared = [x for x in rows if x[0] > 0]
print("count:", len(shared), "of", len(rows))
for n, name, ext, fn, sh in shared[:45]:
    print(f"  {name:<32} {ext:<12} -> shared with {len(sh)}: {', '.join(sh)}")

unique = [x for x in rows if x[0] == 0]
print()
print("core languages with a unique identifier:", len(unique))

# how many coloured languages have ANY exclusive identifier?
excl = 0
for e in colored:
    ok = any(len(claims[x]) == 1 and x in [y for y in claims[x]] for x in (e.get("extensions") or []))
    # an extension is usable if it is claimed only by this language
    usable = [x for x in (e.get("extensions") or []) if claims.get(x) == {e["name"]}]
    usable += [f for f in (e.get("filenames") or []) if nameclaims.get(f) == {e["name"]}]
    if usable:
        excl += 1
print("coloured languages with at least one exclusive identifier:", excl, "of", len(colored))
