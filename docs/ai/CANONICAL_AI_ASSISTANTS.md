# Canonical AI Assistants

The project exposes three bounded AI experiences on one local Ollama and RAG
foundation. All outputs are advisory and all business mutations remain in the
existing canonical command APIs.

## 1. Sales assistant

- UI route: `#/sales-ai`
- API: `POST /api/v1/canonical/ai/sales-assistant/`
- Roles: `Admin`, `Sales`
- Exact permission: `ai_sales:read`
- Supported actions: lead analysis, follow-up email draft, weekly priorities
- Safety boundary: the endpoint never sends email, changes CRM, approves a
  quotation, or executes another business write.

## 2. Internal knowledge assistant

- UI route: `#/sales-docs`
- API: `POST /api/v1/canonical/ai/knowledge-assistant/`
- Roles: `Admin`, `Sales`, `Manager`
- Exact permission: `knowledge:read`
- Retrieval scope: public/internal documents plus explicitly authorized
  restricted documents
- Response contract: answer, source list, confidence and warning

## 3. Public website assistant

- UI: floating `AI tư vấn` widget on public React pages
- API: `POST /api/v1/public/ai/assistant/`
- Authentication: none
- Retrieval scope: documents marked `public` only
- Business context: active product catalogue only
- Explicitly excluded: customers, orders, inventory, CRM, quotations, internal
  file paths, creator email and document metadata
- Protection: input validation, AI governance policy, per-IP rate limiting and
  prompt hashing. Anonymous question previews are not stored.

## Runtime

The assistants use the existing local Ollama configuration. When Ollama is
unavailable, the internal/public RAG pipeline returns a source-based fallback
instead of inventing an answer. Production must use Redis-backed AI rate limits
and the configured concurrency gate.

Relevant environment settings:

- `OLLAMA_HOST`
- `OLLAMA_MODEL`
- `AI_RATE_LIMIT_PER_USER`
- `AI_PUBLIC_RATE_LIMIT_PER_IP`
- `AI_REDIS_RATE_LIMIT_ENABLED`
- `AI_OLLAMA_CAPACITY_ENABLED`

## Required data preparation

Public chatbot answers require approved `KnowledgeDocument` rows with
`permission_level="public"`. Internal documents should remain `internal` or
`restricted`. Reindex documents after ingestion so semantic search has current
chunks and embeddings.
