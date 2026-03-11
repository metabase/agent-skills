#!/bin/bash
# Dumps SDK reference data (d.ts diff, docs, changelog) to stdout.
# Replaces multiple parallel Read calls to avoid cancellations.
#
# Usage: ./read-sources.sh <SDK_TMPDIR>
#
# SDK_TMPDIR: the temp directory from prepare.sh (contains d.ts diff, docs, changelog)
#
# Output format:
#   ════ FILE: <path> ════
#   <file contents>

set -euo pipefail

SDK_TMPDIR="${1:?Usage: read-sources.sh <SDK_TMPDIR>}"

print_file() {
  local filepath="$1"
  if [[ -f "$filepath" ]]; then
    echo "════ FILE: $filepath ════"
    cat "$filepath"
    echo ""
  fi
}

# --- d.ts diff or raw d.ts ---
echo "═══════════════════════════════"
echo "  SDK TYPE DATA"
echo "═══════════════════════════════"
echo ""

if [[ -f "$SDK_TMPDIR/dts-diff.txt" ]]; then
  print_file "$SDK_TMPDIR/dts-diff.txt"
elif [[ -f "$SDK_TMPDIR/current/package/dist/index.d.ts" ]]; then
  print_file "$SDK_TMPDIR/current/package/dist/index.d.ts"
elif [[ -f "$SDK_TMPDIR/target/package/dist/index.d.ts" ]]; then
  print_file "$SDK_TMPDIR/target/package/dist/index.d.ts"
fi

# --- Doc files ---
DOCS_DIR="$SDK_TMPDIR/docs"
if [[ -d "$DOCS_DIR" ]] && ls "$DOCS_DIR"/*.md &>/dev/null; then
  echo "═══════════════════════════════"
  echo "  DOC FILES"
  echo "═══════════════════════════════"
  echo ""
  for doc in "$DOCS_DIR"/*.md; do
    print_file "$doc"
  done
fi

# --- Changelog ---
if [[ -f "$SDK_TMPDIR/changelog.md" ]]; then
  echo "═══════════════════════════════"
  echo "  CHANGELOG"
  echo "═══════════════════════════════"
  echo ""
  print_file "$SDK_TMPDIR/changelog.md"
fi
