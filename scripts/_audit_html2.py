import os, re, ssl, sys, urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

p = os.environ.get("HTTPS_PROXY")
h = urllib.request.build_opener(
    urllib.request.ProxyHandler({"http": p, "https": p}),
    urllib.request.HTTPSHandler(context=ssl.create_default_context()),
)
req = urllib.request.Request(
    "https://github.com/quxianp/RAiNBOW_Hello-World", headers={"User-Agent": "Mozilla/5.0"}
)
html = h.open(req, timeout=60).read().decode("utf-8", "replace")
print("len", len(html))
for pat in ["language-color", "Linguist", "programmingLanguage", "repo-language", "color-fg-default", "python"]:
    print(pat, html.count(pat))
i = html.find("language-color")
print(html[max(0, i - 400):i + 400] if i >= 0 else "language-color NOT FOUND")
i = html.find("repository-lang")
print(html[max(0, i - 200):i + 400] if i >= 0 else "repository-lang NOT FOUND")
