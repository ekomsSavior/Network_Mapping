# How-To — Passive Subdomain Enumeration

Multi-source enumeration: certificate transparency + DNS history. This is Phase 1 of the
methodology — answer "every hostname that exists for these domains, including the ones
that were never meant to be public."

## The sources

| Source | What it gives you | Cost |
|---|---|---|
| **crt.sh** | Certificate transparency (largest CT database) | free, no key — but the backend is frequently flaky (502s). Retry, or use as last resort |
| **Certspotter** | CT issuances with SAN expansion | free tier, no key, reliable |
| **dns.bufferover.run** | Passive DNS (FDNS + RDNS) | free, no key |
| **hackertarget hostsearch** | Passive DNS lookup | free, no key |

CT is the star: every TLS certificate ever issued for a domain is in the public logs —
including certificates for internal services that were never meant to be visible.

## What you're hunting

- Wildcards (`*.evidence.com`) — "there are services here I haven't seen yet"
- Internal names (`vault.`, `jenkins.`, `k8s.`, `mongodb.global.`) — CT names internal tooling
- Tenant fleets (`bdc242.commander.` … `bdc260.commander.`) — scripted provisioning, countable
- Stage/test/dev clusters (`city-dev.`, `st.`, `sandbox.`)
- `*.local` hosts on public DNS — internal naming convention, leaked

## Usage

```
./sweep.sh axon.com evidence.com fusus.com
```

Outputs `all-subdomains.txt` (deduped, normalized, lowercase, wildcards stripped)
then probes every host with httpx (projectdiscovery) if installed.

**Gotchas learned the hard way:**

- crt.sh returns 502 under load — the script retries twice and falls back to the other sources
- Always normalize: strip `*.`, lowercase, strip port suffixes, dedupe
- Same-day rescans catch new certs (our Axon round-2 sweep went 364 → 419 subdomains
  purely because the Dedrone cert dump finally landed)
