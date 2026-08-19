#!/usr/bin/env python3
"""Passive HTTP probe — benign GETs, parallel. Records status/title/server/redirect/tech."""
import concurrent.futures as cf
import json, re, time
import requests

requests.packages.urllib3.disable_warnings()

IN = "all-subdomains.txt"
OUT = "probe-results.jsonl"

HOSTS = [l.strip() for l in open(IN) if l.strip()]
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
           "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8"}

TECH = {
    "salesforce|force.com|lightning": "Salesforce", "okta": "Okta", "auth0": "Auth0",
    "globalprotect|pan-os": "PaloAlto", "istio": "Istio", "envoy": "Envoy",
    "kubernetes": "K8s", "nginx": "nginx", "vercel": "Vercel", "cloudflare": "Cloudflare",
    "azure": "Azure", "aws|amazonaws": "AWS", "wp-json|wordpress": "WordPress",
    "jira": "Jira", "confluence": "Confluence", "jenkins": "Jenkins",
    "sonarqube": "SonarQube", "grafana": "Grafana", "gitlab": "GitLab",
    "s3|minio": "S3/MinIO", "sharepoint": "SharePoint", "outlook|microsoft": "MS/O365",
    "docusign": "DocuSign", "zendesk": "Zendesk", "servicenow": "ServiceNow",
    "tomcat": "Tomcat", "quarkus": "Quarkus", "icinga": "Icinga", "zoho": "Zoho",
}

def probe(host):
    row = {"host": host, "time": int(time.time())}
    for scheme in ("https", "http"):
        try:
            r = requests.get(f"{scheme}://{host}", headers=HEADERS, timeout=8,
                             allow_redirects=True, verify=False)
            m = re.search(r"<title[^>]*>(.*?)</title>", r.text[:20000], re.I | re.S)
            row.update({
                "scheme": scheme, "status": r.status_code,
                "final": r.url[:160], "server": r.headers.get("Server", "")[:60],
                "title": (m.group(1).strip()[:100] if m else ""),
                "ctype": r.headers.get("Content-Type", "")[:50],
                "redirects": len(r.history),
            })
            blob = (r.headers.get("Server", "") + " " + r.headers.get("X-Powered-By", "")
                    + " " + r.text[:4000]).lower()
            row["tech"] = sorted({v for k, v in TECH.items() if re.search(k, blob, re.I)})
            return row
        except requests.exceptions.SSLError:
            continue
        except Exception as e:
            row["error"] = type(e).__name__
            return row
    row["error"] = "no-response"
    return row

with open(OUT, "w") as f:
    with cf.ThreadPoolExecutor(max_workers=40) as ex:
        for i, row in enumerate(ex.map(probe, HOSTS), 1):
            f.write(json.dumps(row) + "\n")
            if i % 100 == 0:
                print(f"[{i}/{len(HOSTS)}]", flush=True)
print("done")
