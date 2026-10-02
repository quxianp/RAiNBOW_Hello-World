import os, ssl, sys, urllib.request

p = os.environ.get("HTTPS_PROXY")
h = urllib.request.build_opener(
    urllib.request.ProxyHandler({"http": p, "https": p}),
    urllib.request.HTTPSHandler(context=ssl.create_default_context()),
)
url, dest = sys.argv[1], sys.argv[2]
req = urllib.request.Request(url, headers={"User-Agent": "rainbow"})
with h.open(req, timeout=120) as r, open(dest, "wb") as f:
    while True:
        chunk = r.read(1 << 16)
        if not chunk:
            break
        f.write(chunk)
print("downloaded", dest, os.path.getsize(dest))
