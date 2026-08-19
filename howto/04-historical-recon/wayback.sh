#!/bin/bash
# Wayback CDX pull — historical URL inventory per domain.
# Usage: ./wayback.sh domain1 domain2 ...
set -uo pipefail
for d in "${@:-example.com}"; do
  curl -s --max-time 60 "http://web.archive.org/cdx/search/cdx?url=*.${d}/*&output=text&fl=original&collapse=urlkey&limit=2000" \
    > "wayback-$d.txt"
  echo "$d: $(wc -l < wayback-$d.txt) urls"
  sleep 2
done
