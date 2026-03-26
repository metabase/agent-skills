# Card

A card represents a Question, Model, or a Metric in Metabase. 

Each card holds a `dataset_query`. See [query.md](../common/query.md) for the query specification. 

## Minimal required properties

Card with an MBQL query:

```yaml
name: Products question
entity_id: f1C68pznmrpN1F5xFDj6d  # nanoid
display: table
creator_id: internal@metabase.com
dataset_query:
  database: Sample Database       # Database FK
  type: query
  query:
    source-table:                 # Table FK
    - Sample Database  
    - PUBLIC           
    - PRODUCTS         
visualization_settings: {}
serdes/meta:
- id: f1C68pznmrpN1F5xFDj6d       # nanoid, matches entity_id
  label: products_question
  model: Card
```

Card with a native query:

```yaml
name: Products question
entity_id: f1C68pznmrpN1F5xFDj6d    # nanoid
display: table
creator_id: internal@metabase.com
dataset_query:
  database: Sample Database        # Database FK
  type: native
  native:
    query: SELECT * FROM PRODUCTS
    template-tags: {}
visualization_settings: {}
serdes/meta:
- id: f1C68pznmrpN1F5xFDj6d       # nanoid, matches entity_id
  label: products_question        # lowercased name, spaces converted to underscores
  model: Card                     # always Card
```

## Optional properties

```yaml
description: All products                  # string or nulltype
archived: false                            # boolean
archived_directly: false                   # boolean
collection_preview: true                   # boolean
collection_position: null                  # integer or null
query_type: null                           # null, "query", or "native"
type: question                             # "question", "model", or "metric"
enable_embedding: false                    # boolean
embedding_params: null                     # map or null
embedding_type: null                       # null, "sdk", "standalone"
public_uuid: null                          # UUID string or null
metabase_version: v1.58.0-SNAPSHOT         # string or null
card_schema: 23                            # integer, card schema version, should not be changed manually
created_at: '2024-08-28T09:46:24.692002Z'  # ISO 8601 date
database_id: Sample Database               # Database FK, should match the database in dataset_query
table_id:                                  # Table FK, should match source-table in the most nested query
- Sample Database
- PUBLIC
- PRODUCTS
source_card_id: null                       # Card FK, should match source-card in dataset_query
collection_id: M-Q4pcV0qkiyJ0kiSWECl       # Collection FK, entity_id or null for the root collection
dashboard_id: null                         # Dashboard FK, entity_id or null
document_id: null                          # Document FK, entity_id or null
made_public_by_id: null                    # User FK, email or null
parameters: []                             # Native query parameters
parameter_mappings: []                     # Unused, always empty
result_metadata: null                      # Query result columns
```