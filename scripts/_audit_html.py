import os, re, ssl, sys, urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

URL = "https://github.com/quxianp/RAiNBOW_Hello-World"


def opener():
    h = []
    p = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
    if p:
        h.append(urllib.request.ProxyHandler({"http": p, "https": p}))
    h.append(urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    return urllib.request.build_opener(*h)


req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
html = opener().open(req, timeout=60).read().decode("utf-8", "replace")

# language segments on the bar carry "title=<Name> %" or "title=Name"
titles = re.findall(r'<span class="color-"[^>]*title="([^"]+)"', html)
if not titles:
    titles = re.findall(r'class="language-bar[^"]*"[^>]*>.*?</div>', html, re.S)
    print("language-bar html length:", len(titles))

names = []
for t in titles:
    m = re.match(r"^(.+?)\s+[\d.]+%$", t)
    names.append(m.group(1) if m else t)
print("segments on the repo bar:", len(names))
print(sorted(set(names))[:30])
