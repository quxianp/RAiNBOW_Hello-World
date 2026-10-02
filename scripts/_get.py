import os, ssl, sys, urllib.request

url = sys.argv[1]
p = os.environ.get("HTTPS_PROXY")
h = urllib.request.build_opener(
    urllib.request.ProxyHandler({"http": p, "https": p}),
    urllib.request.HTTPSHandler(context=ssl.create_default_context()),
)
req = urllib.request.Request(url, headers={"User-Agent": "rainbow-fetch"})
print(h.open(req, timeout=60).read().decode("utf-8", "replace"))
