# How-To — Historical Recon (Web Archives)

Phase 4: what used to be here and was forgotten? The Wayback Machine's CDX API returns
the full URL history of a domain — including endpoints removed from today's frontend
but still live server-side.

## The core query

```
curl -s "http://web.archive.org/cdx/search/cdx?url=*.example.com/*&output=text&fl=original&collapse=urlkey&limit=2000"
```

Parameters that matter:

| Param | Purpose |
|---|---|
| `url=*.domain/*` | everything under the domain (wildcard + path glob) |
| `fl=original` | return just the URL |
| `collapse=urlkey` | dedupe — one capture per unique URL |
| `limit=2000` | cap the response (default is heavy) |

Run it per root domain (`example.com`, plus every acquired domain).

## What you're hunting

- **Old API paths** — `/api/oauth2/login`, `/api/telemetry/mixpanel/track/` — endpoints
  that shipped in a previous frontend generation. Probe them: they often still resolve.
- **Legacy UI** — `/html/uix/index.aspx` (a TASER-era UI in Axon's case). A previous
  product generation still hosted = unmanaged surface.
- **Well-known files** — `/.well-known/openid-configuration`, `/.well-known/ai-plugin.json`,
  `/.well-known/security.txt` on roots you didn't think to check.
- **Partner portals** — `trust.*`, `sales.*`, `go.*` subdomains (Fusus's trust portal
  had 1,100 captured URLs — a whole security-documentation surface).
- **Campaign-specific paths** that reveal org structure (`/contact/axon-evidence`,
  `/contact/axon-fusus` — product lines and team names).

## Usage

```
./wayback.sh example.com acquired-company.com
```

Writes `wayback-<domain>.txt` per domain. Then:

```
# unique hosts in the archive
cat wayback-*.txt | sed 's|https\?://||' | cut -d/ -f1 | sort | uniq -c | sort -rn | head -25
# interesting paths
cat wayback-*.txt | grep -iE "admin|api|internal|dev|staging|jenkins|jira|vault|swagger|oauth|token|console" | grep -vE "\.(css|js|png|jpg|svg|ico|woff)"
```
