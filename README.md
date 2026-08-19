# Net_Mapping — Passive Network Mapping Methodology

**Field-proven approach to mapping modern infrastructure from the outside — without touching a single system you don't own.**

> Written from the operator's seat. Every technique here has been exercised against real
> production targets and the results are live
> for you to inspect at the end of this document. Nothing here requires authentication,
> exploitation, or an active scanner. Everything is already public — you're just learning
> to read it.

---

## 1. The Philosophy

The internet is a machine. A company is not a website — it's an **ecosystem of machines**:
edge proxies, identity providers, API gateways, CI/CD, cloud buckets, tenant fleets,
acquisition leftovers, and a thousand services chained together by DNS records and
certificates.

Most people try to attack a network by looking for vulnerabilities. That's backwards.
First you **map** — you learn how the machine is built. Then you know what it is you're
actually looking at.

And here's the secret: **you don't need credentials to read the architecture. The
architecture tells you about itself.** DNS doesn't hide. Certificates can't lie — they
have to be public to work. JavaScript ships to your browser and begs to be read. Every
request your browser makes is a confession.

**The passive principle:**

| | |
|---|---|
|  **Passive** | certificate transparency, DNS records, public HTTP responses, public JavaScript bundles, web archives |
|  **Not passive** | port scans, vulnerability scanners, brute force, authentication attempts, exploitation, writes |

Passive wins for four reasons:
1. **Legal surface** — you're reading public records and public endpoints
2. **No footprint** — no logs at the target, no alarms, no burn
3. **Richer data** — certificates reveal *internal* hostnames that no scanner will ever find
4. **Scale** — you can map a Fortune 500 in an afternoon from a laptop

---

## 2. The Approach — Six Phases

```
PHASE 0   DEFINE      what are we mapping? which domains own this ecosystem?
PHASE 1   ENUMERATE   certificate transparency + DNS — every name that exists
PHASE 2   FINGERPRINT resolve, geolocate, probe — what is each name, and what runs on it?
PHASE 3   HARVEST     public JS, APIs, OIDC — what do the machines say to each other?
PHASE 4   TIME TRAVEL web archives — what used to exist and was forgotten?
PHASE 5   CORRELATE   group, name, connect — build the mental model
PHASE 6   VISUALIZE   render it as a galaxy so the picture is legible
```

Each phase is detailed below with the exact moves and the exact tells you're hunting for.
Full tool walkthroughs live in [`howto/`](howto/) — one folder per technique, scripts included.

---

## 3. Phase 0 — Define the Target Surface

Before a single query, answer:

1. **What are the root domains?** `company.com` is the start — but so are the domains of
   every company they acquired (`fusus.com`, `dedrone.com`, `carbyne.com` — all Axon's).
   Acquisitions are gold: legacy infrastructure is rarely decommissioned, just orphaned.
2. **What are the product domains?** SaaS platforms often run on their own root
   (`evidence.com` is Axon's entire cloud — not on axon.com).
3. **Who are the partners?** Data-sharing ecosystems (Flock ↔ Axon ↔ RapidSOS ↔ 3Si) mean
   third-party surfaces that touch the primary target.

Write the domain list down. Everything else hangs off it.

## 4. Phase 1 — Enumerate

**Goal:** every hostname that exists for these domains, including ones that were never
meant to be public.

### 4.1 Certificate transparency — the biggest leak in the industry

Every TLS certificate issued for a domain is logged publicly (CT logs). That includes
certificates for **internal services** — because someone once issued a wildcard or a
specific cert for them, and the log entry is permanent.

```
curl -s "https://crt.sh/?q=%25.axon.com&output=json" | jq -r '.[].name_value'
curl -s "https://api.certspotter.com/v1/issuances?domain=axon.com&include_subdomains=true&expand=dns_names" | jq -r '.[].dns_names[]'
```

**What you're hunting:**

- **Wildcards** — `*.evidence.com` means "there are services here I haven't seen"
- **Internal naming conventions** — `vault.evidence.com`, `jenkins.evidence.com`,
  `k8s.evidence.com`, `mongodb.global.dedrone.com` — CT names the internal tooling for you
- **Stage/test clusters** — `st.axon.com`, `city-dev.dedrone.com`, `sensorprovisioning.vadim.city-dev.dedrone.com`
- **Tenant fleets** — `bdc242.commander.evidence.com` … `bdc260.commander.evidence.com`
  is a whole fleet revealed by sequential hostnames
- **"local" hosts on public DNS** — `axon.local.evidence.com` is an internal naming
  convention that leaked into a public cert

### 4.2 DNS — the address book

Cross-reference CT with DNS:
- **bufferover.run** — `curl -s "https://dns.bufferover.run/dns?q=.axon.com"`
- **hackertarget hostsearch** — `curl -s "https://api.hackertarget.com/hostsearch/?q=axon.com"`
- **dig** — resolve everything: `dig +short host.example.com`

Normalize (strip wildcards, dedupe, lowercase) and you have your target list.
The full battle-tested multi-source sweep is in
[`howto/01-subdomain-enumeration/`](howto/01-subdomain-enumeration/) — it pulls
certspotter + hackertarget + bufferover + crt.sh and dedupes everything for you.

## 5. Phase 2 — Fingerprint

**Goal:** what is each host, where does it live, and what runs on it?

### 5.1 Resolve and geolocate

```
dig +short evidence.com            → 52.227.251.93
curl -s ipinfo.io/52.227.251.93/json
```

The IP is a fingerprint in itself:
- `52.227.0.0/16` = **Microsoft Azure** → the platform runs on Azure
- `52.59.x.x` = **AWS Frankfurt**, `108.129.x.x` = AWS Dublin, `3.146.x.x` = AWS Ohio
- `AS12025 Iron Mountain` = a colo box (that's your VPN concentrator, probably)
- `AS2639 Zoho` = wait, why is a product subdomain on Zoho? — that's a tell worth chasing

Cloud regions tell you where data lives. ASN tells you what kind of operator runs it.

### 5.2 Benign HTTP probing

Send a plain GET with a normal browser User-Agent. Record:

| Signal | What it tells you |
|---|---|
| **Status code** | 200 = public · 401/403 = exists, gated · 502 = exists, upstream broken |
| **Server header** | `istio-envoy` = Kubernetes mesh · `nginx/1.14.0 (Ubuntu)` = old box · `awselb` = AWS LB · `Cloudflare` = WAF front |
| **`<title>`** | `Sign In - Axon` = login SPA · `Sign in · GitLab` = internal GitLab, publicly reachable |
| **Redirects** | `fusus.com → axon.com/products/axon-fusus` = absorbed acquisition |
| **Tech hints** | Salesforce (`my.company.com`), WordPress (`/wp-json/`), Tomcat, Quarkus, Jenkins |

**The tells you're hunting:**

- `401 Authorization Required` on `enpass.dedrone.com` — a password-vault front door on the public internet
- `200` on `infra-fra-0001.dedrone.com` showing **GitLab's sign-in page** — internal source control, exposed
- `code-with-quarkus - 1.0.0-SNAPSHOT` — the **default Quarkus scaffold** served by
  `api.global.city-dev.dedrone.com` means an unconfigured dev app is live in front of the internet
- `403 AmazonS3` on `vadim.city-dev.dedrone.com` — a dev bucket named after an engineer

None of these required a single packet beyond an HTTP GET. The machine confessed.

The threaded probe script we use (400 hosts in ~40 seconds, status/title/server/tech
extraction, JSONL output) is in [`howto/02-http-probing/`](howto/02-http-probing/).

## 6. Phase 3 — Harvest

**Goal:** what do the machines say to each other? Read their conversations.

### 6.1 Public JavaScript bundles

Every SPA ships its backend map to the browser. Fetch the page, collect every
`<script src>`, download the bundles, and mine them for:

- **API endpoints** — `/api/telemetry/mixpanel/track/`, `/api/oauth2/login`
- **Backend hostnames** — `auth.c2.dedrone.com`, `axon-static-site.s3.us-west-1.amazonaws.com`
- **Key patterns** — `AKIA…` (AWS), `LTAI…` (Aliyun), `sk_live_…` (Stripe), `client_secret`
- **Internal IPs** — RFC1918 addresses baked into frontends (they leak when devs are sloppy)
- **Platform tells** — `AuraClientService`, `LWRSiteSearch` = Salesforce

The harvester is in [`howto/03-js-harvesting/`](howto/03-js-harvesting/).

### 6.2 OIDC / SSO discovery

If there's an identity host, ask it who it is — the spec makes it answer:

```
curl -s https://id.evidence.com/.well-known/openid-configuration
```

`authorization_endpoint`, `token_endpoint`, **`device_authorization_endpoint`** —
a device-code flow means the platform supports a flow designed for *unattended*
authentication. Knowing the identity architecture tells you how every other service
authenticates.

### 6.3 Public buckets

When JS references `something.s3.amazonaws.com` or `something.oss-…aliyuncs.com`,
probe the bucket. Listing may be denied — but object URLs are often public, and the
naming conventions (`/project/version.json`) are guessable in a disciplined way.
This exact pattern (public bucket + embedded credential + unsigned update path) is how
an entire wireless CarPlay adapter fleet was mapped — documented in our CarPlay
research (see [saviorSEC/CarPlay](https://github.com/saviorSEC/CarPlay)).

## 7. Phase 4 — Time Travel

**Goal:** what used to be here and was forgotten?

The Wayback Machine's CDX API gives you the full URL history of a domain:

```
curl -s "http://web.archive.org/cdx/search/cdx?url=*.evidence.com/*&output=text&fl=original&collapse=urlkey&limit=2000"
```

- Old API paths (`/api/oauth2/login`) that still resolve
- `/html/uix/index.aspx` — a **previous-generation UI** still hosted (TASER-era, in Axon's case)
- Endpoints removed from the current frontend but still live server-side
- `/.well-known/ai-plugin.json`, `/.well-known/openid-configuration` on roots you didn't check

The CDX puller is in [`howto/04-historical-recon/`](howto/04-historical-recon/).

## 8. Phase 5 — Correlate

**Goal:** turn a list of hosts into a model of the machine.

Group everything by **function**, not by domain — that's the insight that makes the map:

| Zone | What lives there |
|---|---|
| **CORE** | the main platform (portal, API gateway, upload plane, admin) |
| **IDENTITY** | OIDC provider, auth, SSO, login |
| **DEVOPS** | jenkins, jira, vault, grafana, k8s, consul — the internal tooling |
| **CORPORATE** | marketing, help, community, VPN, staging |
| **ACQUIRED** | every company they bought, still running |
| **ECOSYSTEM** | data partners — the third parties they exchange data with |
| **THIRD-PARTY** | Salesforce, Cloudflare, Auth0 — the platforms they rent |

Then connect them. Who talks to whom? Identity talks to everyone. Upload talks to API.
The ecosystem partners feed data INTO core. Acquisitions point back at the parent.

Now you have the machine's architecture — including the rooms that were never meant
to have doors.

## 9. Phase 6 — Visualize

**Goal:** make the model legible. A spreadsheet of 400 hosts is a list; a galaxy is understanding.

We render the model as a **3D galaxy**:

- **Planets = zones** — the functional groups, sized by how many services orbit them
- **Satellites = services** — every hostname, colored by its zone
- **Data streams = links** — directional particles flowing between connected services
- **IP pools orbit in** — the cloud ranges, colos, and hosting platforms

Two field examples, built from real data:

- **AXON NETWORK** — https://saviorsec.github.io/axon-network/
  (9 planets, 54 services, 9 IP pools, 84 links — evidence.com, Dedrone, Fusus, ecosystem)
- **FLOCK GLOBE** — https://saviorsec.github.io/flock-globe/
  (12 planets, 125+ services — Cloudflare edge, GovCloud, EKS, SaaS stack)

Both run on plain HTML + three.js + 3d-force-graph, hosted free on GitHub Pages,
data in a single machine-readable JSON.

**Full walkthrough** — data schema, the renderer template, the builder script, and the
exact GitHub Pages deployment steps — is in
[`howto/05-visualization/`](howto/05-visualization/).

---

## 10. Reading the Machine — Field Notes

Things that look like noise until you've seen them once:

- **Sequential tenant hostnames** (`bdc242…bdc260`) = a fleet provisioned by script. Count them.
- **`*.local` on public DNS** = internal naming leaked via certs. Flag it.
- **Old Apache/Tomcat versions** on a Fortune 500 = unmanaged legacy. Note it.
- **Default framework scaffolds** live (`code-with-quarkus`) = dev environment shipped to prod. High signal.
- **Acquired company still on its own stack** (WordPress + wp-json on a 911 platform) = integration debt. Check it.
- **A login page where there shouldn't be one** (GitLab, Icinga, enpass on the public edge) = exposure. Document it.
- **Cloud region spread** = data residency story. German states on `commander.evidence.com`
  are tenants; a Frankfurt API for a drone company is a data path.

## 11. Ethics & Boundaries

- **Passive only.** No authentication, no exploitation, no writes, no active scanning.
- **Public artifacts only.** CT logs, DNS, benign HTTP GETs, JS bundles, archives.
- **Don't touch what you don't own** or lack written authorization to test.
- When you find something real: **document, don't demonstrate.** Then follow a
  responsible disclosure path. Credentials found in the wild get recorded privately and
  reported — never used, never published.
- Visualizations published publicly get **sanitized** — real secrets stay in private archives.


*— Church of Malware. We teach the humans to understand the machines around them.*
