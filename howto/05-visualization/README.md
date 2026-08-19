# How-To — Network Visualization with GitHub Pages

Phase 6: turn the model into a **galaxy**. Planets = zones, satellites = services,
orbiting pools = cloud CIDRs, directional particles = data streams.

**Field examples of the finished product:**

- [AXON NETWORK](https://saviorsec.github.io/axon-network/) — 9 planets / 54 services / 9 IP pools / 84 links
- [FLOCK GLOBE](https://saviorsec.github.io/flock-globe/) — 12 planets / 125+ services / 208 links

## Stack

- **three.js** + **3d-force-graph** (both from unpkg CDN — no build step, no dependencies)
- One HTML file (the renderer) + one JS file (your data) + GitHub Pages (free hosting)
- Everything is client-side — the graph is a force simulation that lays itself out

## The data model

One machine-readable object drives everything (`data.js`):

```js
const NET_INT = {
  "zones": [            // planets — the functional groups
    {"id":"z-core","name":"CORE // PLATFORM","color":"#00e5ff","note":"..."}
  ],
  "services": [         // satellites — every hostname you found
    {"id":"s-api","name":"api.example.com","zone":"z-core","role":"API GATEWAY",
     "note":"...","dns":["1.2.3.4"],"endpoints":["/v1"],"keys":[],"cert":null}
  ],
  "ipPools": [          // orbiting pools — cloud CIDRs / colos
    {"id":"i-azure","name":"Azure US East 52.227.0.0/16","zone":"z-core","role":"hosting","ips":["52.227.251.93"]}
  ],
  "links": [            // membership + data streams
    ["s-api","z-core"],         // service belongs to zone
    ["s-api","s-identity"]      // data stream between services
  ]
};
```

Full schema with field semantics: [`data-schema.md`](data-schema.md).

## Step-by-step

### 1. Build your data

Collect the zones/services/links from Phases 1–5. Group by **function** (core, identity,
devops, corporate, acquired, ecosystem, third-party) — that grouping IS the map.
Write `data.js` (see the template).

### 2. Drop in the renderer

Use [`galaxy-template.html`](galaxy-template.html) — the same engine as our field
deployments. Point it at your data file:

```html
<script src="data.js"></script>
```

### 3. Test locally

```
python3 -m http.server 8000
# open http://localhost:8000/
```

(Works from `file://` too — but an HTTP server matches the deployed behavior.)

### 4. Create the repo and enable Pages

```
gh repo create YOURNAME/net-map --public --source . --push \
  --description "network galaxy — passive mapping visualization"
gh api repos/YOURNAME/net-map/pages -X POST \
  -f "source[branch]=main" -f "source[path]=/"
```

### 5. Wait for the build, verify

```
curl -s -o /dev/null -w "%{http_code}\n" https://YOURNAME.github.io/net-map/
```

**Known gotcha:** the first Pages build occasionally sits in `building` for several
minutes. Kick it with an empty commit:

```
git commit --allow-empty -m "ci: kick pages build" && git push
```

### 6. Verify content, not just status

A 200 on the URL only proves the file exists — it says nothing about whether the
graph rendered. Check the stats that the renderer prints (zones/services/links):

```
chromium --headless --disable-gpu --no-sandbox --enable-unsafe-swiftshader \
  --dump-dom "https://YOURNAME.github.io/net-map/" 2>/dev/null \
  | grep -oE 'id="statZones">[0-9]+|id="statSvc">[0-9]+|id="statLinks">[0-9]+'
```

If they're `0`, the script died — open the page, check the console, fix the data.

## The renderer's features (all in the template)

- Planets sized by service count, labeled with sprites
- Click a planet → member services (drill into any of them)
- Click a service → role / DNS / certs / keys / endpoints / note
- Directional particle streams on links (the "data flow" feel)
- Hover tooltips, drag, zoom, auto-rotate
- Deep links: `?focus=nodeId`

## Going further

- **Geo globe** (for location-based data): globe.gl — same data, plotted by lat/lng,
  with arcs for links. See [AXON GLOBE](https://saviorsec.github.io/axon-globe/).
- **2D canvas galaxy** (lightweight, no WebGL): a 2D canvas renderer with the same
  data model. See [AXON GALAXY](https://saviorsec.github.io/axon-galaxy/).
- **Multi-view dashboard**: index/network/globe tabs in one repo, like flock-globe.
- **Sanitize public renders** — redact keys/tokens from anything you publish;
  keep the full dataset in a private repo.
