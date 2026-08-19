#!/usr/bin/env python3
"""Public JS harvest — download script bundles from target pages, extract
endpoints, hostnames, and key material. Passive: public artifacts only."""
import concurrent.futures as cf
import json, os, re
import requests

requests.packages.urllib3.disable_warnings()
BASE = "js-harvest"
os.makedirs(BASE + "/bundles", exist_ok=True)
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}

PAGES = [  # <-- EDIT: your targets
    "https://www.example.com/",
    "https://portal.example.com/",
]

SRC_RE = re.compile(r'<script[^>]+src=["\']([^"\']+)["\']', re.I)
URL_RE = re.compile(r'https?://[a-zA-Z0-9._\-]+', re.I)
KEY_RE = re.compile(r'(AKIA[0-9A-Z]{16}|LTAI[0-9A-Za-z]{20}|sk_live_[a-zA-Z0-9]+|client_secret["\']?\s*[:=]\s*["\'][^"\']+|api[_-]?key["\']?\s*[:=]\s*["\'][^"\']+|aws_secret|access[_-]?token["\']?\s*[:=]\s*["\'][^"\']+)', re.I)
INT_RE = re.compile(r'\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})\b')
HOST_RE = re.compile(r'\b([a-z0-9][a-z0-9\-]+\.)+(internal|svc|cluster\.local|local|corp|intranet)[a-z0-9\-\.]*\b', re.I)

def fetch(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=12, verify=False, allow_redirects=True)
        return r.status_code, r.text
    except Exception as e:
        return 0, str(e)

def harvest(page):
    status, html = fetch(page)
    out = {"page": page, "status": status, "scripts": [], "endpoints": set(),
           "hosts": set(), "keys": set(), "internal_ips": set()}
    if status != 200:
        out["error"] = html[:80]
        return out
    srcs = [s if s.startswith("http") else requests.compat.urljoin(page, s)
            for s in SRC_RE.findall(html)]
    out["scripts"] = srcs[:30]
    for s in srcs[:30]:
        fn = re.sub(r'[^a-zA-Z0-9]+', '_', s)[-60:] + ".js"
        try:
            js = requests.get(s, headers=HEADERS, timeout=15, verify=False).text
        except Exception:
            continue
        open(f"{BASE}/bundles/{page.split('//')[1].split('/')[0]}_{fn}", "w", errors="ignore").write(js)
        out["endpoints"] |= set(URL_RE.findall(js))
        for k in KEY_RE.findall(js):
            out["keys"].add(str(k[0] if isinstance(k, tuple) else k)[:80])
        for ip in INT_RE.findall(js):
            out["internal_ips"].add(ip[0])
        for h in HOST_RE.findall(js):
            out["hosts"].add(h[0] if isinstance(h, tuple) else h)
    out["endpoints"] = sorted(out["endpoints"])
    out["hosts"] = sorted(out["hosts"])
    out["internal_ips"] = sorted(out["internal_ips"])
    out["keys"] = sorted(out["keys"])
    return out

results = []
with cf.ThreadPoolExecutor(max_workers=6) as ex:
    for r in ex.map(harvest, PAGES):
        results.append(r)
        print(f"[{r['page']}] status={r['status']} scripts={len(r['scripts'])} "
              f"eps={len(r['endpoints'])} keys={len(r['keys'])}", flush=True)

json.dump(results, open(f"{BASE}/harvest-results.json", "w"), indent=1)
print("saved ->", f"{BASE}/harvest-results.json")
