#!/bin/bash
# Dumps SDK type definitions to stdout.
# Replaces parallel Read calls to avoid cancellations.
#
# Usage: ./read-sources.sh <SDK_TMPDIR>
#
# SDK_TMPDIR: the temp directory from prepare.sh
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

echo "═══════════════════════════════"
echo "  SDK TYPE DEFINITIONS"
echo "═══════════════════════════════"
echo ""

if [[ -f "$SDK_TMPDIR/target/package/dist/index.d.ts" ]]; then
  print_file "$SDK_TMPDIR/target/package/dist/index.d.ts"
else
  echo "(no d.ts found — SDK version may predate TypeScript definitions)"
fi
