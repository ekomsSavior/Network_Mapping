# How-To — Public JavaScript Harvesting

Phase 3: every SPA ships its backend map to the browser. Fetch the pages, collect every
`<script src>`, download the bundles, mine them.

## What you're mining for

| Pattern | Meaning |
|---|---|
| `https://host/api/…`, `graphql`, `oauth` | backend endpoints |
| `auth.` / `token` / `sso` hosts | identity plane |
| `AKIA[0-9A-Z]{16}` | AWS access key |
| `LTAI[0-9A-Za-z]{20}` | Aliyun access key |
| `sk_live_…` | Stripe secret key |
| `client_secret" : "…"` | OAuth client secret |
| `10.x`, `172.16-31.x`, `192.168.x` | RFC1918 internal IPs leaked into frontends |
| `*.internal`, `*.svc`, `*.local`, `*.corp` | internal hostnames |
| `*.s3.amazonaws.com`, `*.oss-…aliyuncs.com` | public buckets |

## Usage

1. Edit `PAGES` in `harvest.py` — the URLs you want to harvest (start with the
   root of every domain in scope, plus any login/portal subdomains found in Phase 2).
2. `python3 harvest.py`
3. Bundles land in `bundles/`, findings in `harvest-results.json` — one record per
   page: `scripts`, `endpoints`, `hosts`, `internal_ips`, `keys`.

## Field notes

- No plaintext credentials in most production frontends — mature teams env-inject
  secrets. The absence is itself a data point: it tells you the auth model is
  server-side and the interesting keys live behind the API.
- When you DO find a bucket reference (`axon-static-site.s3.us-west-1.amazonaws.com`):
  probe it. Listing may be denied, but object URLs are often public — and naming
  conventions (`/<project>/version.json`) are guessable in a disciplined way.
- OIDC discovery is part of the same phase — the spec makes identity hosts answer:

```
curl -s https://id.example.com/.well-known/openid-configuration
```

`device_authorization_endpoint` present = the platform supports device-code flows
(designed for unattended auth). Know the identity architecture and you know how every
other service authenticates.
