#!/bin/bash
# Downloads the target SDK package and extracts its d.ts type definitions.
#
# Usage: ./prepare.sh <TARGET_VERSION>
#
# TARGET_VERSION: the SDK version to migrate to (e.g., 0.58.0, 0.59.3)
#
# Output: prints SDK_TMPDIR, d.ts availability, and paths.

set -euo pipefail

TARGET="${1:?Usage: prepare.sh <TARGET_VERSION>}"

SDK_TMPDIR=$(node -e "
  const path = require('path');
  const fs = require('fs');
  const dir = path.join(require('os').tmpdir(), 'sdk-migrate-' + Date.now());
  fs.mkdirSync(dir, { recursive: true });
  console.log(dir);
")

mkdir -p "$SDK_TMPDIR/target"

echo "Downloading SDK package v${TARGET}..."
(cd "$SDK_TMPDIR/target" && npm pack "@metabase/embedding-sdk-react@${TARGET}" --quiet 2>/dev/null && tar xzf *.tgz)

# Check d.ts availability
TARGET_DTS="no"
[ -f "$SDK_TMPDIR/target/package/dist/index.d.ts" ] && TARGET_DTS="yes"

echo ""
echo "SDK_TMPDIR=$SDK_TMPDIR"
echo "target_dts=$TARGET_DTS"

if [[ "$TARGET_DTS" == "yes" ]]; then
  echo "TARGET_DTS_PATH=$SDK_TMPDIR/target/package/dist/index.d.ts"
fi
