import json, os, ssl, sys, time, urllib.request
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REPO = "https://api.github.com/repos/quxianp/RAiNBOW_Hello-World"


def opener():
    h = []
    p = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
    if p:
        h.append(urllib.request.ProxyHandler({"http": p, "https": p}))
    h.append(urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    return urllib.request.build_opener(*h)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "rainbow-poll",
                                               "Accept": "application/vnd.github+json",
                                               "Cache-Control": "no-cache"})
    with opener().open(req, timeout=60) as r:
        return json.loads(r.read().decode())


rainbow = json.load(open("config/rainbow_langs.json", encoding="utf-8"))
core = {r["name"] for r in rainbow["languages"]}
target = len(core)
prev = None
end = time.time() + 55 * 60
i = 0
while time.time() < end:
    i += 1
    try:
        repo = get(REPO)
        langs = get(REPO + "/languages")
    except Exception as exc:
        print(f"[{datetime.now():%H:%M:%S}] error {exc}", flush=True)
        time.sleep(120)
        continue
    total = sum(langs.values())
    missing = len(core - set(langs))
    extra = sorted(set(langs) - core)
    line = (f"[{datetime.now():%H:%M:%S}] push={repo.get('pushed_at')} "
            f"langs={len(langs)} target={target} missing={missing} "
            f"counted={total}")
    if line != prev:
        print(line + (f" extra={extra[:6]}" if extra else ""), flush=True)
        prev = line
    if missing == 0 and len(langs) >= target:
        print("DONE: every core language is on the bar", flush=True)
        break
    time.sleep(90)
print("poller finished", flush=True)
