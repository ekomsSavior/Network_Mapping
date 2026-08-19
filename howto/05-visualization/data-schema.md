# Galaxy Data Schema

The visualization engine reads one object. This is the contract.

```js
const NET_INT = {
  "zones":    [ /* planets */ ],
  "services": [ /* satellites */ ],
  "ipPools":  [ /* orbiting cloud/colo ranges */ ],
  "links":    [ /* membership + data streams */ ]
};
```

## zones — the planets

| Field | Type | Meaning |
|---|---|---|
| `id` | string | unique, lowercase, `z-` prefixed (`z-core`) |
| `name` | string | display name, `GROUP // DETAIL` style (`CORE // EVIDENCE.COM`) |
| `color` | string | hex — the planet's glow color; services in the zone inherit it |
| `note` | string | one-line summary of what lives here |

**Tip:** keep the group list tight (7–12). Functional groups, not domains:
CORE / IDENTITY / DEVOPS / CORPORATE / ACQUIRED / ECOSYSTEM / THIRD-PARTY.
Split a group into its own planet when it's big enough to matter on its own
(e.g. a 80-host tenant fleet, or an acquisition with its own cluster).

## services — the satellites

| Field | Type | Meaning |
|---|---|---|
| `id` | string | unique, `s-` prefixed (`s-api`) |
| `name` | string | hostname or cluster label |
| `zone` | string | which planet this orbits (zone `id`) |
| `role` | string | what it does (`API GATEWAY`, `OIDC IDP`, `CI — SSO-GATED`) |
| `note` | string | findings / tells (free text) |
| `dns` | string[] | IPs / CNAME targets |
| `endpoints` | string[] | known paths (`/.well-known/openid-configuration`) |
| `keys` | string[] | credentials — **redact before publishing** |
| `cert` | string\|null | notable certificate info (`*.evidence.com wildcard`) |

## ipPools — the orbiting ranges

| Field | Type | Meaning |
|---|---|---|
| `id` | string | unique, `i-` prefixed |
| `name` | string | `Azure US East // Boydton VA 52.227.0.0/16` |
| `zone` | string | which planet it orbits (hosting relationship) |
| `role` | string | what runs there (`evidence.com core + tenant fleet`) |
| `ips` | string[] | member addresses |

## links — membership + streams

Pairs of ids. Two kinds:

```js
["s-api", "z-core"]        // membership: service → its zone
["s-api", "s-identity"]    // data stream: service → service
```

Direction matters — particles flow from the first id to the second. Model real
data flow (`upload → api`, `identity → everything`, `partner → core`).

## Rendering rules (what the engine does with it)

- Planet radius ∝ √(member count)
- Service color = its zone's color
- Pools render slightly larger than services, in their zone's color
- Streams between co-located services (same region) are skipped to reduce noise
- Click behavior: planet → member list (drill-in) · service → full detail

## Sanitization checklist (before pushing to a public Pages site)

- [ ] `keys` arrays contain redaction markers, not secrets
- [ ] no live tokens / session material / private keys anywhere in `note`
- [ ] internal IPs kept only when they're evidence of a finding worth publishing
- [ ] consider a private archive repo for the full dataset (public mirror = sanitized)
