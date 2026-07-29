# RAG Usage

## Ingest Text In Python

```python
from apps.knowledge.services.knowledge_service import KnowledgeService

KnowledgeService().ingest_text(
    title="CNC capability",
    content="MecPrecision provides CNC machining and fixture manufacturing.",
    source_type="markdown",
)
```

## Search API

`POST /api/v1/knowledge/search/`

```json
{
  "query": "CNC machining",
  "limit": 5
}
```

## Response

```json
{
  "success": true,
  "data": {
    "query": "CNC machining",
    "results": [
      {
        "score": 0.82,
        "chunk": {
          "id": 1,
          "content": "Matched knowledge text",
          "chunk_index": 0
        },
        "document": {
          "id": 1,
          "title": "CNC capability"
        }
      }
    ]
  }
}
```

