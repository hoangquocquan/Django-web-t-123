# CHATGPT RAG Chatbot Demo Report

## 1. Summary

**Result: DONE for a controlled internal technical demo; not a public automotive chatbot.** The existing frontend now has a conversational `AI Car Assistant` page that sends messages to Django, calls the existing synthetic RAG service, displays the generated grounded answer and source citations, and keeps conversation turns in browser memory. The API rejects missing permission and invalid input. Questions unsupported by the corpus return `UNAVAILABLE` with no fabricated value or source.

The repository's verified RAG corpus is fictional **precision-component** data, not automotive inventory. The service and documents are internal-only. Consequently this implementation does not present the data as real cars, and it does not enable the existing public chatbot (`PUBLIC_AI_ENABLED=False`).

## 2. Architecture

```text
Browser (#/admin-ai-chat; in-memory Foundation Bearer session)
  -> POST /api/v1/internal/rag-chat/
  -> authentication + knowledge:read + internal role + AI governance + input validation
  -> SyntheticRagWebDemoService (same service as #/admin-rag-demo)
  -> KnowledgeSearchService / existing vector store + lexical reranking
  -> indexed KnowledgeChunk / DocumentVersion / KnowledgeDocument
  -> synthetic BusinessProduct (rag_synthetic_demo_v1 only)
  -> RagGenerationPipeline / local Ollama with synthetic-grounding prompt
  -> answer + SUPPORTED/UNAVAILABLE + traceable citations
  -> React chat history in memory
```

No second retrieval engine, new frontend framework, or persistent conversation store was introduced.

## 3. Files changed

This task changed the following files on branch `codex/demo-database-validation`. The worktree already contained extensive unrelated staged, unstaged, and untracked work; none of that work was reset or merged.

| File | Change in this task |
|---|---|
| `django_backend/apps/knowledge/services/rag_pipeline.py` | Allows a caller-supplied prompt template while preserving the existing default. |
| `django_backend/apps/knowledge/services/synthetic_rag_demo.py` | Supplies a prompt that accurately treats synthetic records as test facts, reuses scoped retrieval/generation, and records bounded runtime diagnostics without logging raw question text. |
| `django_backend/apps/knowledge/views.py` | Adds validated, governance-protected internal chat view. |
| `django_backend/apps/api/urls.py` | Adds the internal chat endpoint. |
| `django_backend/apps/knowledge/tests/test_synthetic_rag_web_demo.py` | Adds chat authorization, validation, reuse, and prompt tests. |
| `figma_make_frontend/src/api/aiDemo.ts` | Adds typed chat API request/response. |
| `figma_make_frontend/src/components/RagChatPage.tsx` | Adds conversational UI, loading/error states, session history, citation display, sample questions, and input bound. |
| `figma_make_frontend/src/App.tsx` | Adds the internal admin route/navigation and mounts the chat page with the existing memory-only session. |
| `figma_make_frontend/src/api/ragChat.test.ts` | Adds frontend API and page-contract tests. |
| `figma_make_frontend/package.json` | Includes the chat tests in the full frontend suite. |
| `CHATGPT_RAG_CHATBOT_DEMO_REPORT.md` | This implementation and verification report. |

## 4. Database

The chatbot reads `BusinessProduct`, `KnowledgeDocument`, `DocumentVersion`, `KnowledgeChunk`, and `KnowledgeEmbedding` through the existing services. Foundation user/role/token and AI governance are reused for authorization. The existing AI request audit may receive metadata-only events during queries. No chatbot table, schema migration, Product import, document import, or reindex was performed.

Post-run read-only counts: **626** BusinessProducts total; **25** synthetic Products (IDs 602–626); **601** other Products; **25** synthetic KnowledgeDocuments; **48** chunks; **48** embeddings; **0** PublicProductProjection records. The public AI feature flag remains disabled.

## 5. RAG integration

The chat view calls `SyntheticRagWebDemoService.query(message, user=user, limit=3)`, exactly the service used by the earlier technical RAG web demo. It limits documents to indexed, active, internal `SYNTHETIC_PRODUCT` records with `dataset_id=rag_synthetic_demo_v1`, `synthetic=true`, `production_eligible=false`, `authoritative=false`, and both public/pilot approval flags false. It does not supply Sales/RFQ/Customer business context. Retrieval uses the existing `KnowledgeSearchService` embedding/vector search plus lexical reranking; generation uses `RagGenerationPipeline` and local Ollama. Supported answers include source title, product code, document version/revision, chunk ID, and `synthetic://` locator.

Current provider: `development-hash-fallback` with `development-hash-plus-lexical` reranking. This is **not semantic embedding**. A paraphrase smoke test worked, but that one result is not proof of broad semantic retrieval quality.

## 6. API

- Endpoint: `POST /api/v1/internal/rag-chat/`
- Authentication: `Authorization: Bearer <memory-only Foundation token>`
- Authorization: `knowledge:read` and role `Admin`, `Manager`, `Sales`, or `editor` (case-insensitive). Anonymous and viewer denied.
- Request: `{"message":"Which synthetic product uses SUS316 with an electropolished finish?"}`
- Validation: nonblank, trimmed, at most 1,200 characters; malformed input returns HTTP 400.
- Success envelope: `{"success":true,"data":{"question":"...","answer":"...","status":"SUPPORTED","sources":[{"title":"...","product_code":"SYN-RAG-0011","citation":"synthetic://...","document_id":216,"version":1,"revision":"1","chunk_id":17893,"relevance_score":0.78}],"retrieval":{"dataset_id":"rag_synthetic_demo_v1","provider":"development-hash-fallback","provider_mode":"development-hash-plus-lexical","result_count":3,"latency_ms":0,"llm_success":true,"fallback_used":false}}}`. Numeric values shown here are illustrative except for the observed source IDs and corpus/provider labels; runtime values vary.
- Unavailable response: `status=UNAVAILABLE`, no sources, and the existing fixed unavailable sentence.

No secret, raw internal exception, or system prompt is returned by this endpoint.

## 7. UI

Open `http://127.0.0.1:8443/#/admin-ai-chat` with Django at `http://127.0.0.1:8000/` and Vite at `http://127.0.0.1:8443/`. Log in through the internal Foundation form, then choose **AI Chat Demo** in the admin navigation. The form sends to the Django API, shows loading and sanitized errors, and displays user/AI turns and citations. The page explicitly warns that its 25 records are synthetic precision-component data, not company or car facts. React renders model output as text, not raw HTML. History exists only while the page/session remains mounted.

The existing `#/admin-rag-demo` page and its `POST /api/v1/internal/rag-demo/query/` endpoint remain unchanged in behavior. The public `#/chatbot` route remains governed by the disabled public AI flag and does not use this internal synthetic corpus.

## 8. Environment variables

- `VITE_API_BASE_URL=/` for same-origin `/api/v1/` requests through the existing Vite proxy.
- `VITE_DJANGO_ORIGIN=http://127.0.0.1:8000` if overriding the Vite proxy target; loopback only in development.
- Existing `OLLAMA_HOST`, `OLLAMA_MODEL`, and related Ollama settings control local LLM generation through the project's model-config service.
- Existing `KNOWLEDGE_EMBEDDING_PROVIDER` controls query embedding; the local corpus currently uses the hash fallback provider.
- Existing Django `DATABASE_URL` may select a database. This run used the existing local development database.

No API key or secret value is committed. Public AI remains explicitly disabled in settings.

## 9. Testing

| Check | Result |
|---|---|
| Django starts and database connects | PASS |
| Vite starts and browser loads `#/admin-ai-chat` | PASS |
| Internal login and form submission | PASS |
| Loading state, multiple-turn history, answer/citations on real Chrome UI | PASS |
| Local Ollama generated a grounded answer for supported questions | PASS |
| Price and unrelated weather questions do not hallucinate | PASS |
| Empty/overlength input | PASS — HTTP 400 |
| Anonymous, viewer, internal user without `knowledge:read` | PASS — denied |
| Existing corpus isolation and prior RAG page tests | PASS |
| Django `check` | PASS — no issues |
| `makemigrations --check --dry-run` | PASS — no changes detected |
| Backend related regression suite | PASS — 70 passed, 2 skipped; focused chat/RAG suite 8 passed |
| Frontend `npm run typecheck` | PASS |
| Frontend `npm test` | PASS — 165 passed |
| Frontend `npm run build` | PASS |
| Chrome console error/warning check | PASS — none observed |
| `git diff --check` on task files | PASS — only line-ending notices |

## 10. Example conversations

All five examples below were sent from the real chat UI in Chrome, and the displayed output was inspected.

| Question | Observed result | Primary source |
|---|---|---|
| Which synthetic product uses SUS316 with an electropolished finish? | `SUPPORTED`; Housing 0011 | `SYN-RAG-0011` |
| Which bushing is made from oil-impregnated bronze? | `SUPPORTED`; Bushing 0015 | `SYN-RAG-0015` |
| Which red anodized block has G1/8 pneumatic ports? | `SUPPORTED`; Mounting Block 0018 | `SYN-RAG-0018` |
| What is the sales price of SYN-RAG-0001? | `UNAVAILABLE`; no price and no sources | none |
| Thời tiết Tokyo hôm nay thế nào? | `UNAVAILABLE`; no weather claim and no sources | none |

## 11. Known limitations

- The corpus is small and wholly fictional. It cannot answer real car, stock, price, or company-policy questions.
- Current embeddings are deterministic hash fallback plus lexical reranking, not a verified semantic model. Multilingual/paraphrase coverage is limited.
- The generation model is local Ollama; provider outages use the existing source-based fallback for supported retrieval.
- The UI history is in browser memory only and is lost on refresh.
- Grounding includes deterministic evidence checks but is not a formal guarantee against every possible model hallucination. Human review remains required before expanding scope.
- This is a development server and controlled internal demo, not a production release.

## 12. Next recommended phase (not implemented)

1. Phase 2: improve retrieval evaluation, especially Vietnamese paraphrases, and install/test a compatible semantic embedding model.
2. Phase 3: review and approve genuine automotive product knowledge with provenance and publication controls before any customer exposure.
3. Phase 4: only after separate authorization, consider lead capture or Sales AI; keep customer/private data behind distinct permission boundaries.

No merge, push to main, public chatbot enablement, or production deployment was performed.
