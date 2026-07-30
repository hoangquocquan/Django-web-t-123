# Legacy AI Inventory

## Summary

The old custom Python backend contained a standalone AI implementation. It has been archived so the project has one active AI architecture: the Django AI Platform.

## Components Found

| Component | Location | Purpose | Replacement |
|---|---|---|---|
| Legacy AI service | `backend/services/ai_service.py` | Chatbot, translation, developer AI, contact summary, quote analysis, document reader, smart search, dashboard insight, product SEO generation | `django_backend/apps/ai`, `django_backend/apps/knowledge`, `django_backend/apps/ai_agent` |
| Legacy AI repository | `backend/repositories/ai_repository.py` | Store/read `ai_conversations` rows | Django AI logs and knowledge assistant logs |
| Public AI route | `POST /api/ai/chat` in `backend/app.py` | Public chatbot API | `POST /api/v1/ai/chat/` |
| Admin AI page | `/admin/ai` in `backend/app.py` | Legacy CMS AI operations | Django AI Platform APIs and future Django Admin UI |
| Developer AI form | `/admin/developer/ai-code` in `backend/app.py` | Explain/debug code through legacy AI | `apps.ai_agent` and AI DevOps tools |
| Product AI generate | `/admin/products/ai-generate` in `backend/app.py` | Generate product content and SEO in legacy CMS | AI Sales/Content assistant under Django AI Platform |
| Public HTML auto translation | `backend/services/localization_service.py` | Called legacy Ollama during page render | Manual/cache-only legacy fallback; AI translation belongs to Django |
| Legacy AI settings | `backend/config/settings.py` | `MEC_OLLAMA_*` settings for custom backend | Django AI Platform settings |
| Legacy AI database tables | `backend/database/schema.sql`, `backend/database/migrations.py` | `ai_conversations`, `ai_translation_cache` | Archived for data preservation; no active legacy AI writer |

## Database Tables

The old SQLite tables remain in schema files for historical compatibility and existing database preservation:

- `ai_conversations`
- `ai_translation_cache`

They are not removed in this cleanup because the task requires backup-first cleanup and no data loss.

## Replacement Mapping

| Old Capability | New Django Capability |
|---|---|
| Chatbot | `apps.ai` endpoint `/api/v1/ai/chat/` |
| RAG Q&A | `apps.knowledge` endpoint `/api/v1/knowledge/chat/` |
| AI Sales / CRM help | `apps.ai_agent.services.sales_assistant` endpoint `/api/v1/ai/sales-assistant/` |
| Local Ollama client | `apps.ai.services.ollama_client` |
| Knowledge documents | `apps.knowledge.models.KnowledgeDocument` and chunks/embeddings |
| AI review automation | `ai-review` and `ai-factory` |
