#!/bin/bash
set -euo pipefail

if [ $# -lt 3 ]; then
  echo "Usage: bash fetch-metadata.sh <METABASE_URL> <API_KEY> <FOLDER_PATH>"
  echo "Example: bash fetch-metadata.sh https://my-company.metabaseapp.com mb_abc123... .metadata_cache"
  exit 1
fi

METABASE_URL="${1%/}"
API_KEY="$2"
FOLDER_PATH="$3"

# Create a temp directory for the archive; clean it up on exit
TMPDIR="$(mktemp -d)"
trap 'rm -rf "${TMPDIR}"' EXIT

# Download the serialization export as a .tar.gz archive
curl -X POST "${METABASE_URL}/api/ee/serialization/export?all_collections=false&field_values=true&dirname=metadata" \
  -H "x-api-key: ${API_KEY}" \
  --output "${TMPDIR}/metabase-export.tar.gz"

# Clear any previous cache
rm -rf "${FOLDER_PATH}"

# Extract the archive into the target folder
mkdir -p "${FOLDER_PATH}"
tar -xzf "${TMPDIR}/metabase-export.tar.gz" --strip-components=1 -C "${FOLDER_PATH}"

# Only keep the databases folder — discard everything else
find "${FOLDER_PATH}" -mindepth 1 -maxdepth 1 ! -name databases -exec rm -rf {} +

# Remove Metabase's internal database — not useful for understanding the data model
rm -rf "${FOLDER_PATH}/databases/internal_metabase_database"
