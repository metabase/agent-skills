#!/usr/bin/env python3
"""Download and extract database metadata from a Metabase instance."""

import os
import shutil
import sys
import tarfile
import tempfile
import urllib.parse
import urllib.request

if len(sys.argv) < 4:
    print("Usage: python fetch-metadata.py <METABASE_URL> <API_KEY> <OUTPUT_DIR>")
    print("Example: python fetch-metadata.py https://my-company.metabaseapp.com mb_abc123... .metadata_cache")
    sys.exit(1)

base_url = sys.argv[1].rstrip("/") + "/"
api_key = sys.argv[2]
output_dir = sys.argv[3]

params = urllib.parse.urlencode(
    {"all_collections": "false", "field_values": "true", "dirname": "metadata"}
)
export_url = urllib.parse.urljoin(base_url, "api/ee/serialization/export")
url = urllib.parse.urlparse(export_url)._replace(query=params).geturl()
req = urllib.request.Request(url, method="POST", headers={"x-api-key": api_key})

temp_dir = tempfile.mkdtemp()
archive_path = os.path.join(temp_dir, "export.tar.gz")

try:
    print("Downloading metadata export...")
    with urllib.request.urlopen(req) as response, open(archive_path, "wb") as f:
        shutil.copyfileobj(response, f)

    print("Extracting...")
    extract_dir = os.path.join(temp_dir, "extracted")
    with tarfile.open(archive_path, mode="r:gz") as tar:
        tar.extractall(extract_dir)

    # Find the databases/ directory inside the extracted archive (under the root dir)
    root_entries = os.listdir(extract_dir)
    extracted_root = os.path.join(extract_dir, root_entries[0])
    source_databases = os.path.join(extracted_root, "databases")

    # Remove Metabase's internal database — not useful for understanding the data model
    internal_db = os.path.join(source_databases, "internal_metabase_database")
    if os.path.exists(internal_db):
        shutil.rmtree(internal_db)

    # Replace the databases folder in the output directory
    target_databases = os.path.join(output_dir, "databases")
    os.makedirs(output_dir, exist_ok=True)
    if os.path.exists(target_databases):
        shutil.rmtree(target_databases)
    shutil.move(source_databases, target_databases)

    print(f"Metadata saved to {target_databases}")
finally:
    shutil.rmtree(temp_dir)
