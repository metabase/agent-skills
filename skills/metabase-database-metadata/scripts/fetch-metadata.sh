#!/bin/bash
set -euo pipefail

if [ $# -lt 2 ]; then
  echo "Usage: bash fetch-metadata.sh <METABASE_URL> <API_KEY>"
  echo "Example: bash fetch-metadata.sh https://my-company.metabaseapp.com mb_abc123..."
  exit 1
fi

METABASE_URL="${1%/}"
API_KEY="$2"

curl -X POST "${METABASE_URL}/api/ee/serialization/export?all_collections=false&field_values=true&dirname=metadata" \
  -H "x-api-key: ${API_KEY}" \
  --output metabase-export.tar.gz
