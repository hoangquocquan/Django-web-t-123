# Legacy AI Archive

## Archive Location

Legacy AI code has been moved to:

`archive/legacy_ai/`

## Archived Files

| Archived file | Original location | Reason |
|---|---|---|
| `archive/legacy_ai/backend/services/ai_service.py` | `backend/services/ai_service.py` | Old custom backend AI service |
| `archive/legacy_ai/backend/repositories/ai_repository.py` | `backend/repositories/ai_repository.py` | Old custom backend AI storage layer |
| `archive/legacy_ai/backend/config/legacy_ai_settings.md` | `backend/config/settings.py` notes | Records removed `MEC_OLLAMA_*` settings |

## Runtime Cleanup

The legacy backend no longer imports or calls `services.ai_service`.

Removed runtime routes:

- `/api/ai/chat`
- `/admin/ai`
- `/admin/developer/ai-code`
- `/admin/products/ai-generate`

## Active AI Architecture

The active AI architecture is now:

- `django_backend/apps/ai`
- `django_backend/apps/knowledge`
- `django_backend/apps/ai_agent`
- AI Sales Assistant
- Local Ollama integration in Django
- RAG Knowledge System

## Restore Note

The archive is for learning and historical reference only. Do not copy archived legacy AI files back into `backend/` unless a separate rollback phase explicitly approves it.
