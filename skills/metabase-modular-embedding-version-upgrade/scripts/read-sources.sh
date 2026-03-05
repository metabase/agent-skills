#!/bin/bash
# Reads all source files needed for the upgrade and prints them to stdout.
# This replaces multiple parallel Read calls with a single Bash call.
#
# Usage: ./read-sources.sh <SDK_TMPDIR> <file1> [file2] [file3] ...
#
# SDK_TMPDIR: the temp directory from prepare.sh (contains d.ts diff, docs, changelog)
# Remaining args: project file paths to read (from grep results)
#
# Output format:
#   ════ FILE: <path> ════
#   <file contents>
#   (repeated for each file)

set -euo pipefail

SDK_TMPDIR="${1:?Usage: read-sources.sh <SDK_TMPDIR> <file1> [file2] ...}"
shift

print_file() {
  local filepath="$1"
  if [[ -f "$filepath" ]]; then
    echo "════ FILE: $filepath ════"
    cat "$filepath"
    echo ""
  fi
}

# --- Project files ---
echo "═══════════════════════════════"
echo "  PROJECT FILES"
echo "═══════════════════════════════"
echo ""

for f in "$@"; do
  print_file "$f"
done

# --- d.ts diff or raw d.ts ---
echo "═══════════════════════════════"
echo "  SDK TYPE DATA"
echo "═══════════════════════════════"
echo ""

if [[ -f "$SDK_TMPDIR/dts-diff.txt" ]]; then
  # Both versions have d.ts — print the diff (compact, ~200-500 lines)
  print_file "$SDK_TMPDIR/dts-diff.txt"
elif [[ -f "$SDK_TMPDIR/current/package/dist/index.d.ts" ]]; then
  # Hybrid: current has d.ts
  print_file "$SDK_TMPDIR/current/package/dist/index.d.ts"
elif [[ -f "$SDK_TMPDIR/target/package/dist/index.d.ts" ]]; then
  # Hybrid: target has d.ts
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
