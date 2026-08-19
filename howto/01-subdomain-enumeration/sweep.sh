#!/bin/bash
# Passive multi-source subdomain enumeration — CT logs + passive DNS.
# Boundary: public artifacts only. No auth, no exploitation.
# Usage: ./sweep.sh domain1 domain2 ...
set -uo pipefail
OUT=recon-$(date +%F)
mkdir -p "$OUT"
cd "$OUT"

DOMAINS="${@:-example.com}"

for d in $DOMAINS; do
  # 1. certspotter (free CT API, no key)
  curl -s --max-time 30 "https://api.certspotter.com/v1/issuances?domain=$d&include_subdomains=true&expand=dns_names" \
    | jq -r '.[].dns_names[]?' 2>/dev/null >> raw.txt
  # 2. hackertarget hostsearch
  curl -s --max-time 30 "https://api.hackertarget.com/hostsearch/?q=$d" >> raw.txt
  # 3. dns.bufferover.run
  curl -s --max-time 30 "https://dns.bufferover.run/dns?q=.$d" | jq -r '.FDNS_A[], .RDNS[]?' 2>/dev/null | cut -d, -f2 >> raw.txt
  # 4. crt.sh (retry x2 — it's flaky)
  for try in 1 2; do
    curl -s --max-time 45 "https://crt.sh/?q=%25.$d&output=json" -o "ct-$d.json"
    if jq -e 'type=="array"' "ct-$d.json" >/dev/null 2>&1; then
      jq -r '.[].name_value' "ct-$d.json" 2>/dev/null | tr ',' '\n' >> raw.txt
      break
    fi
    sleep 8
  done
  echo "  $d done"
  sleep 3
done

echo "[*] dedupe + normalize"
sed 's/^\*\.//' raw.txt | tr 'A-Z' 'a-z' | sed 's/^[0-9.]*,//' \
  | grep -E '^[a-z0-9._-]+\.[a-z0-9-]+\.(com|net|org|io|co|dev|app|cloud)$' \
  | sort -u > all-subdomains.txt
wc -l all-subdomains.txt
rm -f raw.txt

echo "[*] probe with httpx (projectdiscovery) if available"
if command -v httpx >/dev/null; then
  httpx -l all-subdomains.txt -silent -status-code -title -tech-detect \
    -no-color -timeout 8 -retries 1 -o httpx-results.txt 2>/dev/null || \
    echo "note: system httpx is the python client — install projectdiscovery's binary for this step"
fi
