#!/bin/bash
# Deploy a network galaxy to GitHub Pages.
# Usage: ./deploy-pages.sh YOURNAME repo-name "description"
set -euo pipefail
NAME="${1:?usage: deploy-pages.sh USER REPO DESC}"
REPO="${2:?}"
DESC="${3:-network galaxy — passive mapping visualization}"

# 1. create repo (public) and push
git init -q
git add -A
git -c user.email="you@example.com" -c user.name="You" commit -q -m "network galaxy: data + renderer"
git branch -M main
gh repo create "$NAME/$REPO" --public --source . --push --description "$DESC"

# 2. enable Pages on main
gh api "repos/$NAME/$REPO/pages" -X POST \
  -f "source[branch]=main" -f "source[path]=/" || true

# 3. wait + verify
URL="https://$NAME.github.io/$REPO/"
for i in $(seq 1 12); do
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$URL" || true)
  if [ "$code" = "200" ]; then echo "LIVE: $URL"; exit 0; fi
  sleep 10
done
echo "still building — if stuck >5min, kick it:"
echo "  git commit --allow-empty -m 'ci: kick pages build' && git push"
