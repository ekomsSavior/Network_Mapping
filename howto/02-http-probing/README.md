# How-To — Benign HTTP Probing

Phase 2 fingerprinting: resolve, geolocate, and probe every host with a plain GET.
No auth, no exploitation — just the same request any browser makes.

## The signals

| Signal | Meaning |
|---|---|
| **Status** | 200 = public · 401/403 = exists, gated · 502 = exists, upstream broken |
| **Server header** | `istio-envoy` = K8s mesh · `nginx/1.14.0 (Ubuntu)` = old box · `awselb` = AWS LB · `Cloudflare` = WAF front |
| **`<title>`** | `Sign In - Axon` = login SPA · `Sign in · GitLab` = internal GitLab reachable from the internet |
| **Redirect chain** | `fusus.com → axon.com/products/axon-fusus` = absorbed acquisition |
| **Tech fingerprints** | Salesforce (`my.` subdomains), WordPress (`/wp-json/`), Tomcat, Quarkus, Jenkins, Icinga |

## Geolocation — the IP is a fingerprint

```
dig +short evidence.com          # 52.227.251.93
curl -s ipinfo.io/52.227.251.93/json
```

- `52.227.0.0/16` → Microsoft Azure (the platform is Azure-hosted)
- `52.59.x.x` → AWS Frankfurt · `108.129.x.x` → AWS Dublin · `3.146.x.x` → AWS Ohio
- `AS12025 Iron Mountain` → colocated box (likely a VPN concentrator)
- `AS2639 Zoho` → a product subdomain on Zoho is a tell worth chasing

## Usage

```
python3 probe.py                 # reads all-subdomains.txt, writes probe-results.jsonl
jq -r 'select(.status != null and .status < 400) | [.host, .status, .title, (.tech|join(","))] | @tsv' probe-results.jsonl
```

~400 hosts in ~40 seconds with 40 threads. Output is JSONL — one row per host —
with status, final URL, server header, page title, content-type, redirect count,
and detected tech stack.

**The tells you're hunting** (all real finds from field work):

- `401 Authorization Required` on `enpass.*` — a password-vault front door, public
- `200` GitLab sign-in on `infra-fra-0001.*` — internal source control, exposed
- `code-with-quarkus - 1.0.0-SNAPSHOT` — the **default Quarkus scaffold**, unconfigured and live
- `403 AmazonS3` on a host named after an engineer — a dev bucket with a person's name on it
- Old `Apache Tomcat/8.5.16` banners — unmanaged legacy
