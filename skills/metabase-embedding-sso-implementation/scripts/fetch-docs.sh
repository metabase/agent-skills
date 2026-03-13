#!/bin/bash
# Fetches Metabase embedding auth doc pages for a given version.
# Uses the GitHub Contents API to dynamically find available .md files.
#
# Usage: ./fetch-docs.sh <VERSION>
#   VERSION: Metabase version. Accepts any format: 58, 0.58, v0.58, 0.58.1
#
# Output: Downloads docs to /tmp/embedjs-docs/ and prints each fetched file.

set -euo pipefail

VERSION="${1:?Usage: fetch-docs.sh <VERSION>}"

# Normalize version: "0.58.1" -> "58", "v0.52" -> "52", "54" -> "54"
VERSION=$(echo "$VERSION" | sed 's/^v//; s/^0\.//; s/\..*//')

OUTDIR="/tmp/embedjs-docs"
mkdir -p "$OUTDIR"

REPO="metabase/docs.metabase.github.io"
API_BASE="https://api.github.com/repos/${REPO}/contents"
RAW_BASE="https://raw.githubusercontent.com/${REPO}/master"
DOCS_PATH="_docs/v0.${VERSION}/embedding"

# Discover available .md files via GitHub Contents API
echo "Listing ${DOCS_PATH} ..."
API_RESPONSE=$(curl -sL -w "\n%{http_code}" "${API_BASE}/${DOCS_PATH}")
API_STATUS=$(echo "$API_RESPONSE" | tail -1)
API_BODY=$(echo "$API_RESPONSE" | sed '$d')

if [[ "$API_STATUS" != "200" ]]; then
  echo "FAIL: GitHub API returned $API_STATUS for ${DOCS_PATH}" >&2
  echo "This version's docs directory may not exist." >&2
  exit 1
fi

MD_FILES=$(echo "$API_BODY" | node -e "
  const data = JSON.parse(require('fs').readFileSync('/dev/stdin', 'utf8'));
  if (Array.isArray(data)) {
    data
      .filter(f => f.type === 'file' && f.name.endsWith('.md'))
      .forEach(f => console.log(f.name));
  }
" 2>/dev/null || true)

if [[ -z "$MD_FILES" ]]; then
  echo "No .md files found in ${DOCS_PATH}"
  exit 0
fi

echo "Found: $(echo "$MD_FILES" | tr '\n' ' ')"
echo ""

# Fetch all discovered .md files in parallel
PIDS=()
URLS=()
FILES=()

for filename in $MD_FILES; do
  url="${RAW_BASE}/${DOCS_PATH}/${filename}"
  outfile="${OUTDIR}/${filename}"
  curl -sL -w "%{http_code}" -o "$outfile" "$url" > "${outfile}.status" &
  PIDS+=($!)
  URLS+=("$url")
  FILES+=("$outfile")
done

FAILED=0
for i in "${!PIDS[@]}"; do
  wait "${PIDS[$i]}" || true
  STATUS=$(cat "${FILES[$i]}.status" 2>/dev/null || echo "000")
  rm -f "${FILES[$i]}.status"

  if [[ "$STATUS" == "200" ]]; then
    echo "OK   ${FILES[$i]}"
  else
    echo "FAIL $STATUS ${URLS[$i]}"
    rm -f "${FILES[$i]}"
    FAILED=1
  fi
done

echo ""
echo "OUTDIR=$OUTDIR"
exit $FAILED
