import json, os, ssl, sys, urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REPO = "https://api.github.com/repos/quxianp/RAiNBOW_Hello-World"


def opener():
    handlers = []
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
    if proxy:
        handlers.append(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    handlers.append(urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    return urllib.request.build_opener(*handlers)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "rainbow-audit",
                                               "Accept": "application/vnd.github+json"})
    with opener().open(req, timeout=60) as r:
        return json.loads(r.read().decode())


langs = get(REPO + "/languages")
print("languages GitHub reports:", len(langs))
total = sum(langs.values())
print("total counted bytes:", total)
top = sorted(langs.items(), key=lambda kv: -kv[1])[:25]
for k, v in top:
    print(f"  {k:<28}{v:>12}  {v / total * 100:6.3f} %")

rainbow = json.load(open("config/rainbow_langs.json", encoding="utf-8"))
core = {r["name"] for r in rainbow["languages"]}
seen = set(langs)
print()
print("core languages missing from GitHub's report:", len(core - seen))
print(sorted(core - seen)[:40])
print("languages GitHub reports that we did not plan:", sorted(seen - core)[:40])

missing = [(k, langs[k] / total * 100) for k in sorted(seen)]
tiny = [x for x in missing if x[1] < 0.1]
print()
print("reported languages below 0.1%:", len(tiny))
print("reported languages above 0.1%:", len(missing) - len(tiny))
