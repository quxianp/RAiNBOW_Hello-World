"""Poll the GitHub languages endpoint until it stops changing.

Usage: python scripts/_poll_langs.py [minutes] [interval_seconds]
"""
import json, os, ssl, sys, time, urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

URL = "https://api.github.com/repos/quxianp/RAiNBOW_Hello-World/languages"
minutes = float(sys.argv[1]) if len(sys.argv) > 1 else 12.0
interval = float(sys.argv[2]) if len(sys.argv) > 2 else 45.0


def opener():
    h = []
    p = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
    if p:
        h.append(urllib.request.ProxyHandler({"http": p, "https": p}))
    h.append(urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    return urllib.request.build_opener(*h)


def fetch():
    req = urllib.request.Request(
        URL,
        headers={
            "User-Agent": "rainbow-poll",
            "Accept": "application/vnd.github+json",
            "Cache-Control": "no-cache",
        },
    )
    with opener().open(req, timeout=60) as r:
        return json.loads(r.read().decode())


deadline = time.time() + minutes * 60
last = None
stable = 0
while time.time() < deadline:
    try:
        d = fetch()
        n, tot = len(d), sum(d.values())
        print(f"{time.strftime('%H:%M:%S')} languages={n} bytes={tot}", flush=True)
        if last == (n, tot):
            stable += 1
            if stable >= 3:
                print("stable for 3 polls", flush=True)
                break
        else:
            stable = 0
            last = (n, tot)
    except Exception as exc:
        print(f"{time.strftime('%H:%M:%S')} error {exc}", flush=True)
    time.sleep(interval)
