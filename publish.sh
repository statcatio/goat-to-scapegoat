#!/bin/bash
# Publish wc-hatewatch/index.html to the live site.
# wc-hatewatch is the source of truth; site/goat-to-scapegoat/ is output only.
set -e
SRC=~/Desktop/wc-hatewatch/index.html
DST=~/Desktop/site/goat-to-scapegoat/index.html

if ! git -C ~/Desktop/wc-hatewatch diff --quiet; then
  echo "!! wc-hatewatch has uncommitted changes. Commit them first:"
  echo "   cd ~/Desktop/wc-hatewatch && git add -A && git commit -m '...'"
  exit 1
fi

cp "$SRC" "$DST"
cd ~/Desktop/site
if git diff --quiet goat-to-scapegoat/index.html; then
  echo "== already up to date, nothing to publish"
else
  git add goat-to-scapegoat/index.html
  git commit -q -m "Publish goat-to-scapegoat from wc-hatewatch"
  echo "== committed"
fi
git push
echo "== live: https://statcatio.github.io/goat-to-scapegoat/"
