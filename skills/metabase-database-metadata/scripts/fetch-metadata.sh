#!/bin/bash
set -euo pipefail

if [ $# -lt 3 ]; then
  echo "Usage: bash fetch-metadata.sh <METABASE_URL> <API_KEY> <OUTPUT_DIR>"
  echo "Example: bash fetch-metadata.sh https://my-company.metabaseapp.com mb_abc123... .metadata_cache"
  exit 1
fi

METABASE_URL="${1%/}"
API_KEY="$2"
OUTPUT_DIR="$3"

# Create a temp directory for the archive and extraction; clean it up on exit
TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TEMP_DIR}"' EXIT

# Download the serialization export as a .tar.gz archive
curl -X POST "${METABASE_URL}/api/ee/serialization/export?all_collections=false&field_values=true&dirname=metadata" \
  -H "x-api-key: ${API_KEY}" \
  --output "${TEMP_DIR}/metabase-export.tar.gz"

# Extract the archive into the temp directory
tar -xzf "${TEMP_DIR}/metabase-export.tar.gz" --strip-components=1 -C "${TEMP_DIR}"

# Remove Metabase's internal database — not useful for understanding the data model
rm -rf "${TEMP_DIR}/databases/internal_metabase_database"

# Replace the databases folder in the target directory
mkdir -p "${OUTPUT_DIR}"
rm -rf "${OUTPUT_DIR}/databases"
mv "${TEMP_DIR}/databases" "${OUTPUT_DIR}/databases"
