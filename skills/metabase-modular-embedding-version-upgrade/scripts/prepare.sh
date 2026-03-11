#!/bin/bash
# Combined probe + fetch: downloads SDK packages, checks d.ts, fetches changelog,
# and fetches docs for versions without d.ts — all in one call.
#
# Usage: ./prepare.sh <CURRENT_VERSION> <TARGET_VERSION> --sdk
#        ./prepare.sh <CURRENT_VERSION> <TARGET_VERSION> --embedjs
#
# Requires --sdk or --embedjs flag to specify embedding type.
# For SDK upgrades (--sdk): probes both versions via npm pack, then fetches docs
# for whichever version lacks a d.ts file.
# For Modular Embedding upgrades (--embedjs): skips npm pack, fetches docs for both versions.
#
# Output: prints SDK_TMPDIR, d.ts availability, and fetched doc/d.ts paths.

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
CURRENT="${1:?Usage: prepare.sh <CURRENT> <TARGET> --sdk|--embedjs}"
TARGET="${2:?Usage: prepare.sh <CURRENT> <TARGET> --sdk|--embedjs}"
MODE="${3:?Usage: prepare.sh <CURRENT> <TARGET> --sdk|--embedjs. Must specify --sdk or --embedjs.}"

if [[ "$MODE" != "--sdk" && "$MODE" != "--embedjs" ]]; then
  echo "ERROR: Third argument must be --sdk or --embedjs, got: $MODE" >&2
  exit 1
fi

SDK_TMPDIR=$(node -e "
  const path = require('path');
  const fs = require('fs');
  const dir = path.join(require('os').tmpdir(), 'sdk-diff-' + Date.now());
  fs.mkdirSync(dir, { recursive: true });
  console.log(dir);
")

DOCS_DIR="$SDK_TMPDIR/docs"
mkdir -p "$SDK_TMPDIR/current" "$SDK_TMPDIR/target" "$DOCS_DIR"

if [[ "$MODE" == "--embedjs" ]]; then
  # Modular Embedding (embed.js): no npm pack, fetch docs for both versions
  echo "Modular Embedding mode — fetching docs for both versions..."

  echo "Fetching changelog..."
  curl -sL "https://raw.githubusercontent.com/metabase/metabase/master/enterprise/frontend/src/embedding-sdk-package/CHANGELOG.md" \
    | head -1000 > "$SDK_TMPDIR/changelog.md" &

  bash "$SKILL_DIR/fetch-docs.sh" --version "$CURRENT" --type embedjs --prefix current --outdir "$DOCS_DIR" &
  bash "$SKILL_DIR/fetch-docs.sh" --version "$TARGET" --type embedjs --prefix target --outdir "$DOCS_DIR" &
  wait

  echo ""
  echo "SDK_TMPDIR=$SDK_TMPDIR"
  echo "CHANGELOG=$SDK_TMPDIR/changelog.md"
  echo "DOCS_DIR=$DOCS_DIR"
  echo "current_dts=no"
  echo "target_dts=no"
  exit 0
fi

# SDK mode: npm pack both versions + fetch changelog in parallel
echo "Downloading SDK packages..."
(cd "$SDK_TMPDIR/current" && npm pack "@metabase/embedding-sdk-react@${CURRENT}" --quiet 2>/dev/null && tar xzf *.tgz) &
(cd "$SDK_TMPDIR/target"  && npm pack "@metabase/embedding-sdk-react@${TARGET}"  --quiet 2>/dev/null && tar xzf *.tgz) &

echo "Fetching changelog..."
curl -sL "https://raw.githubusercontent.com/metabase/metabase/master/enterprise/frontend/src/embedding-sdk-package/CHANGELOG.md" \
  | head -1000 > "$SDK_TMPDIR/changelog.md" &

wait

# Check d.ts availability
CURRENT_DTS="no"
TARGET_DTS="no"
[ -f "$SDK_TMPDIR/current/package/dist/index.d.ts" ] && CURRENT_DTS="yes"
[ -f "$SDK_TMPDIR/target/package/dist/index.d.ts" ] && TARGET_DTS="yes"

echo ""
echo "current_dts=$CURRENT_DTS"
echo "target_dts=$TARGET_DTS"

# Fetch docs for versions without d.ts
if [[ "$CURRENT_DTS" == "no" ]]; then
  echo ""
  echo "--- Fetching current version docs (no d.ts) ---"
  bash "$SKILL_DIR/fetch-docs.sh" --version "$CURRENT" --type sdk --prefix current --outdir "$DOCS_DIR"
fi

if [[ "$TARGET_DTS" == "no" ]]; then
  echo ""
  echo "--- Fetching target version docs (no d.ts) ---"
  bash "$SKILL_DIR/fetch-docs.sh" --version "$TARGET" --type sdk --prefix target --outdir "$DOCS_DIR"
fi

echo ""
echo "SDK_TMPDIR=$SDK_TMPDIR"
echo "CHANGELOG=$SDK_TMPDIR/changelog.md"
echo "DOCS_DIR=$DOCS_DIR"

# If both d.ts exist, auto-diff them (saves reading 4k lines of raw d.ts)
if [[ "$CURRENT_DTS" == "yes" && "$TARGET_DTS" == "yes" ]]; then
  DIFF_PATH="$SDK_TMPDIR/dts-diff.txt"
  diff -u \
    "$SDK_TMPDIR/current/package/dist/index.d.ts" \
    "$SDK_TMPDIR/target/package/dist/index.d.ts" \
    > "$DIFF_PATH" || true  # diff exits 1 when files differ
  DIFF_LINES=$(wc -l < "$DIFF_PATH" | tr -d ' ')
  echo "DTS_DIFF_PATH=$DIFF_PATH"
  echo "DTS_DIFF_LINES=$DIFF_LINES"
fi

# Print d.ts paths only for hybrid mode (one side needs raw d.ts)
if [[ "$CURRENT_DTS" == "yes" && "$TARGET_DTS" == "no" ]]; then
  echo "CURRENT_DTS_PATH=$SDK_TMPDIR/current/package/dist/index.d.ts"
fi

if [[ "$TARGET_DTS" == "yes" && "$CURRENT_DTS" == "no" ]]; then
  echo "TARGET_DTS_PATH=$SDK_TMPDIR/target/package/dist/index.d.ts"
fi
