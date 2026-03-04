#!/bin/bash
# Probes two SDK versions: downloads npm packages, checks d.ts availability, fetches changelog.
# Usage: ./probe-versions.sh <CURRENT_VERSION> <TARGET_VERSION>
# Output: prints SDK_TMPDIR path and d.ts availability for each version.

set -euo pipefail

CURRENT="${1:?Usage: probe-versions.sh <CURRENT> <TARGET>}"
TARGET="${2:?Usage: probe-versions.sh <CURRENT> <TARGET>}"

SDK_TMPDIR=$(node -e "
  const path = require('path');
  const fs = require('fs');
  const dir = path.join(require('os').tmpdir(), 'sdk-diff-' + Date.now());
  fs.mkdirSync(dir, { recursive: true });
  console.log(dir);
")

mkdir -p "$SDK_TMPDIR/current" "$SDK_TMPDIR/target"

echo "Downloading SDK packages..."
(cd "$SDK_TMPDIR/current" && npm pack "@metabase/embedding-sdk-react@${CURRENT}" --quiet 2>/dev/null && tar xzf *.tgz) &
(cd "$SDK_TMPDIR/target"  && npm pack "@metabase/embedding-sdk-react@${TARGET}"  --quiet 2>/dev/null && tar xzf *.tgz) &

echo "Fetching changelog..."
curl -sL "https://raw.githubusercontent.com/metabase/metabase/master/enterprise/frontend/src/embedding-sdk-package/CHANGELOG.md" \
  -o "$SDK_TMPDIR/changelog.md" &

wait

echo ""
echo "SDK_TMPDIR=$SDK_TMPDIR"
echo "CHANGELOG=$SDK_TMPDIR/changelog.md"
echo ""

# Check d.ts availability for each version
if [ -f "$SDK_TMPDIR/current/package/dist/index.d.ts" ]; then
  echo "current_dts=yes"
else
  echo "current_dts=no"
fi

if [ -f "$SDK_TMPDIR/target/package/dist/index.d.ts" ]; then
  echo "target_dts=yes"
else
  echo "target_dts=no"
fi
