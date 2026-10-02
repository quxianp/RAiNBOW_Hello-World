import os, ssl, sys, urllib.request

rt = sys.stdout
try:
    rt.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

p = os.environ.get("HTTPS_PROXY")
h = urllib.request.build_opener(
    urllib.request.ProxyHandler({"http": p, "https": p}),
    urllib.request.HTTPSHandler(context=ssl.create_default_context()),
)
req = urllib.request.Request(
    "https://github.com/quxianp/RAiNBOW_Hello-World",
    headers={"User-Agent": "Mozilla/5.0"},
)
html = h.open(req, timeout=60).read().decode("utf-8", "replace")

for pat in ['"languages":[', "languagesUrl", "repositoryLanguageUsage", '"languages":']:
    idx = html.find(pat)
    print(f"{pat!r}: count unknown, first at {idx}")
    if idx >= 0:
        print(html[idx:idx + 800])
        print("-----")
