# metabase-database-metadata

Skill for fetching and caching database metadata (databases, tables, fields, field values) from a Metabase instance.

## Setup

This skill requires a `fetch-metadata.sh` script in the skill folder. Create it with the following contents:

```bash
#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 2 ]; then
  echo "Usage: $0 <metabase-url> <api-key>" >&2
  exit 1
fi

METABASE_URL="$1"
METABASE_API_KEY="$2"

base_url="${METABASE_URL%/}"
export_url="${base_url}/api/ee/serialization/export?all_collections=false&field_values=true&dirname=metadata"
target_dir="metadata/databases"

temp_dir=$(mktemp -d)
archive_path="${temp_dir}/export.tar.gz"

echo "Downloading metadata export..."
curl -fsSL -X POST \
  -H "x-api-key: ${METABASE_API_KEY}" \
  -o "${archive_path}" \
  "${export_url}"

echo "Extracting..."
extract_dir="${temp_dir}/extracted"
mkdir -p "${extract_dir}"
tar -xzf "${archive_path}" -C "${extract_dir}"

extracted_root="${extract_dir}/$(ls "${extract_dir}" | head -n1)"
source_databases="${extracted_root}/databases"

mkdir -p "$(dirname "${target_dir}")"
rm -rf "${target_dir}"
mv "${source_databases}" "${target_dir}"

rm -rf "${temp_dir}"

echo "Metadata saved to ${target_dir}"
```

After saving the file, make it executable:

```sh
chmod +x fetch-metadata.sh
```

## How it works

The script calls the Metabase serialization export API:

```
POST {METABASE_URL}/api/ee/serialization/export?all_collections=false&field_values=true&dirname=metadata
```

with header `x-api-key: {API_KEY}`. The response is a `.tar.gz` archive; the script keeps only the `databases/` directory and writes it to `metadata/databases` in the working directory.

The download may take several minutes depending on the size of the instance.
