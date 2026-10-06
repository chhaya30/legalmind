import os
import urllib.request

BASE = os.getenv("LEGALMIND_URL", "http://127.0.0.1:8000")

for path in ("/", "/api/v1/health"):
    with urllib.request.urlopen(BASE + path, timeout=10) as r:
        print(path, r.status, r.read().decode()[:500])
print("Smoke check passed.")
