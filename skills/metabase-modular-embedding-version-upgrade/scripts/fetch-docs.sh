#!/bin/bash
# Discovers and fetches all Metabase embedding doc pages for a given version.
# Uses the GitHub Contents API to dynamically find available .md files —
# no hardcoded version-specific logic.
#
# Usage:
#   ./fetch-docs.sh --version 58 --type sdk --prefix target --outdir /tmp/sdk-docs
#   ./fetch-docs.sh --version 57 --type embedjs --prefix current --outdir /tmp/embedjs-docs
#
# Options:
#   --version    Version number. Accepts any format: 58, 0.58, v0.58, 0.58.1. Required.
#   --type       Product type: "sdk" or "embedjs". Required.
#   --prefix     Output prefix for filenames: "current" or "target". Required.
#   --outdir     Output directory. Required.
#
# How it works:
#   1. Lists files in the docs repo for the given version via GitHub Contents API
#   2. Fetches all discovered .md files in parallel via raw.githubusercontent.com
#   3. For SDK docs: also discovers and fetches snippet files referenced via include_file directives
#
# Output:
#   Downloads docs to $OUTDIR/{prefix}-{filename}
#   Prints each fetched URL and its HTTP status.
#   Exit code 0 on success, 1 if directory listing or required fetches failed.

set -euo pipefail

VERSION=""
TYPE=""
PREFIX=""
OUTDIR=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version)   VERSION="$2"; shift 2 ;;
    --type)      TYPE="$2";    shift 2 ;;
    --prefix)    PREFIX="$2";  shift 2 ;;
    --outdir)    OUTDIR="$2";  shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$VERSION" || -z "$TYPE" || -z "$PREFIX" || -z "$OUTDIR" ]]; then
  echo "Error: --version, --type, --prefix, and --outdir are all required." >&2
  exit 1
fi

# Normalize version: "0.58.1" -> "58", "v0.52" -> "52", "54" -> "54"
VERSION=$(echo "$VERSION" | sed 's/^v//; s/^0\.//; s/\..*//')

mkdir -p "$OUTDIR"

REPO="metabase/docs.metabase.github.io"
API_BASE="https://api.github.com/repos/${REPO}/contents"
RAW_BASE="https://raw.githubusercontent.com/${REPO}/master"

# Determine the docs directory to list based on type
if [[ "$TYPE" == "sdk" ]]; then
  DOCS_PATH="_docs/v0.${VERSION}/embedding/sdk"
elif [[ "$TYPE" == "embedjs" ]]; then
  DOCS_PATH="_docs/v0.${VERSION}/embedding"
else
  echo "Error: --type must be 'sdk' or 'embedjs'" >&2
  exit 1
fi

# --- Step 1: Discover available .md files via GitHub Contents API ---
echo "Listing ${DOCS_PATH} ..."
API_RESPONSE=$(curl -sL -w "\n%{http_code}" "${API_BASE}/${DOCS_PATH}")
API_STATUS=$(echo "$API_RESPONSE" | tail -1)
API_BODY=$(echo "$API_RESPONSE" | sed '$d')

if [[ "$API_STATUS" != "200" ]]; then
  echo "FAIL: GitHub API returned $API_STATUS for ${DOCS_PATH}" >&2
  echo "This version's docs directory may not exist." >&2
  exit 1
fi

# Extract .md filenames from the API response
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

# --- Step 2: Fetch all discovered .md files in parallel ---
PIDS=()
URLS=()
FILES=()

for filename in $MD_FILES; do
  url="${RAW_BASE}/${DOCS_PATH}/${filename}"
  outfile="${OUTDIR}/${PREFIX}-${filename}"
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

# --- Step 3: Discover and fetch snippet files (SDK only) ---
# Doc pages may contain {% include_file %} directives referencing snippet files.
# Scan fetched pages for these directives and fetch the referenced snippets.

# Match lines like: {% include_file "{{ dirname }}/api/snippets/FooProps.md" snippet="properties" %}
# Extract just the snippet filename (e.g., "FooProps")
SNIPPET_NAMES=$(grep -h 'include_file.*api/snippets/.*\.md.*snippet=' "${OUTDIR}/${PREFIX}-"*.md 2>/dev/null \
  | sed 's/.*api\/snippets\/\([^"]*\)\.md.*/\1/' | sort -u || true)

if [[ -n "$SNIPPET_NAMES" ]]; then
  echo ""
  echo "--- Fetching snippets ---"

  # Use GitHub API to discover the actual snippets directory path
  SNIP_API_PATH="${DOCS_PATH}/api/snippets"
  SNIP_RAW_PATH="${RAW_BASE}/${SNIP_API_PATH}"

  SNIP_PIDS=()
  SNIP_URLS=()
  SNIP_FILES=()

  for name in $SNIPPET_NAMES; do
    url="${SNIP_RAW_PATH}/${name}.md"
    file="${OUTDIR}/${PREFIX}-snippet-${name}.md"
    curl -sL -w "%{http_code}" -o "$file" "$url" > "${file}.status" &
    SNIP_PIDS+=($!)
    SNIP_URLS+=("$url")
    SNIP_FILES+=("$file")
  done

  for i in "${!SNIP_PIDS[@]}"; do
    wait "${SNIP_PIDS[$i]}" || true
    STATUS=$(cat "${SNIP_FILES[$i]}.status" 2>/dev/null || echo "000")
    rm -f "${SNIP_FILES[$i]}.status"

    if [[ "$STATUS" == "200" ]]; then
      echo "OK   ${SNIP_FILES[$i]}"
    else
      echo "FAIL $STATUS ${SNIP_URLS[$i]}"
      rm -f "${SNIP_FILES[$i]}"
      FAILED=1
    fi
  done
fi

echo ""
echo "OUTDIR=$OUTDIR"
exit $FAILED
