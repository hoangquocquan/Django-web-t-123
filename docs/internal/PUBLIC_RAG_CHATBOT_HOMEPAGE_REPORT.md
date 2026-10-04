# Public RAG Chatbot on Homepage — Development Demo Report

> Correct deliverable: `PUBLIC_RAG_CHATBOT_HOMEPAGE_REPORT.md`  
> Re-verified: 2026-09-23 (Asia/Tokyo)  
> Worktree: `C:\Users\hoang\Documents\ChatGPT\WEB Ô TÔ DJANGO`  
> Branch: `codex/demo-database-validation`  
> Git action: no merge to `main`, no push

## 1. Summary

Added an anonymous floating **AI Component Assistant** to the MecPrecision homepage (`#/`). It runs only in local development, asks the existing synthetic RAG pipeline, displays a short answer and simplified source titles/product codes, and keeps chat history only in browser memory. The existing `#/admin-ai-chat` and `#/admin-rag-demo` routes remain present and login-gated. No merge, push, production publication, or synthetic-data rewrite was performed.

## 2. Architecture

```text
Homepage -> PublicComponentChatWidget -> GET/POST /api/v1/public/ai-component-demo/
         -> PublicSyntheticRagDemoService -> SyntheticRagWebDemoService
         -> KnowledgeSearchService -> RagGenerationPipeline / local Ollama
         -> rag_synthetic_demo_v1 -> short public response

Admin AI Chat -> POST /api/v1/internal/rag-chat/
              -> SyntheticRagWebDemoService -> same search/generation pipeline
```

There is no second retrieval engine and no hard-coded product answer in the widget.

## 3. Admin vs Public

| Area | Internal AI chat / technical RAG | Homepage assistant |
| --- | --- | --- |
| Audience | Authenticated, permission-checked staff | Anonymous local-development visitor |
| Route | `#/admin-ai-chat`, `#/admin-rag-demo` | `#/` floating widget |
| API | `/api/v1/internal/rag-chat/`, `/api/v1/internal/rag-demo/query/` | `/api/v1/public/ai-component-demo/` |
| Dataset | Synthetic demo corpus | Same corpus, explicitly scoped |
| Response | Technical citations and retrieval diagnostics | Short answer; source title and product code only |
| Session | Internal auth | No login or saved conversation |

## 4. Files changed for this task

Created: `django_backend/apps/knowledge/services/public_synthetic_rag_demo.py`, `django_backend/apps/knowledge/tests/test_public_synthetic_rag_demo.py`, `figma_make_frontend/src/components/PublicComponentChatWidget.tsx`, `figma_make_frontend/src/api/publicComponentDemo.test.ts`, and this report.

Modified: `django_backend/config/settings/base.py`, `django_backend/config/settings/development.py`, `django_backend/apps/knowledge/views.py`, `django_backend/apps/api/urls.py`, `figma_make_frontend/src/api/aiDemo.ts`, `figma_make_frontend/src/App.tsx`, `figma_make_frontend/src/components/RagChatPage.tsx`, `figma_make_frontend/src/api/ragChat.test.ts`, `figma_make_frontend/package.json`.

The working tree also contains numerous pre-existing changes outside this task; they were not reset or merged.

## 5. Public endpoint

- `GET /api/v1/public/ai-component-demo/` returns `{"success":true,"data":{"enabled":true}}` only when the local demo gate is open.
- `POST /api/v1/public/ai-component-demo/` accepts `{"message":"Which component uses SUS316?"}` (nonblank, at most 1200 characters) and returns an envelope whose `data` has only `answer`, `status` (`SUPPORTED` or `UNAVAILABLE`), and `sources` (`title`, `product_code`).
- The frontend sends neither bearer token nor Admin credentials. It does not call `/api/v1/internal/rag-chat/`.

## 6. Shared RAG proof

`PublicSyntheticRagDemoService.answer()` calls `SyntheticRagWebDemoService.query(message, user=None, limit=3)`. The internal chat view calls the same `SyntheticRagWebDemoService.query()` with its authenticated user. Backend tests assert the public call path and internal endpoint behavior.

## 7. Data scope

The shared service retrieves only indexed `KnowledgeDocument` records with `source_type=SYNTHETIC_PRODUCT`, `metadata.dataset_id=rag_synthetic_demo_v1`, `metadata.synthetic=true`, `metadata.production_eligible=false`, `permission_level=internal`, and `ai_public_approved=false`, through its explicit demo scope. The public wrapper further requires a synthetic-demo title, `SYN-RAG-...` product code, and matching `synthetic://rag_synthetic_demo_v1/...` citation. It returns no results from customer, RFQ, order, employee, general BusinessProduct, or unrelated knowledge records.

Local database check: **25** documents, **48** chunks; **0** public-approved and **0** production-eligible documents in this corpus. Existing governance fields were not changed.

## 8. Security and release gate

- `PUBLIC_SYNTHETIC_RAG_DEMO_ENABLED` is false in base settings, true by default only in development settings. Endpoint additionally requires `DEBUG=true` and loopback `REMOTE_ADDR`; production public AI flag `PUBLIC_AI_ENABLED` remains untouched/off.
- Anonymous POST is validated server-side and uses existing `AIGovernanceService` per-IP rate limiting. The development cache fallback is not suitable for a multi-worker public release.
- The public response omits internal IDs, chunk/revision metadata, retrieval provider, latency, and raw citations. Since model text can repeat source chunks, the public wrapper keeps only a bounded first answer paragraph, removes known score syntax, and fails closed if internal metadata remains. React renders answer as text, not raw HTML.
- Existing same-origin Vite `/api` proxy is used locally; no cross-origin credential flow was added. No public production deployment is authorized by this demo gate.

## 9. UI

Open `http://127.0.0.1:8444/#/` in this local session and click the bottom-right **💬 AI Assistant** button. The popup contains a synthetic-data notice, four sample questions, loading state, answer/source display, friendly unavailable state, and close button. On a 390×844 viewport, the popup and input remain visible and usable. Refresh clears its in-memory history.

Port **8444** is the verified current demo instance, proxied to Django on **8011**. An older local process occupied 8443 and served a stale API route; do not use 8443 to judge this change.

## 10. Testing

| Check | Result |
| --- | --- |
| `python manage.py check` | PASS, no issues |
| `python manage.py makemigrations --check --dry-run` | PASS, no changes |
| Focused backend tests (public, internal synthetic RAG, existing public assistant) | PASS, 37 tests |
| 2026-09-23 focused public/internal RAG re-run | PASS, 20 tests |
| `npm run typecheck` | PASS |
| `npm test` | PASS, 167 tests |
| `npm run build` | PASS |
| Chrome homepage and widget open/close | PASS |
| Chrome supported SUS316, paraphrase, bushing, weather, price, empty input | PASS as detailed below |
| 2026-09-23 Chrome re-verification | PASS: homepage widget; SUS316 `SUPPORTED` + `SYN-RAG-0011`; weather `UNAVAILABLE`; no console errors |
| Chrome mobile 390×844 and console errors | PASS; no console errors observed |
| Admin route browser smoke | PASS: both routes load and demand internal login |
| Authenticated Admin chat/browser E2E | LIMITATION: not run in this session; internal API regression tests passed |
| Entire backend `pytest -q` | FAIL outside this change: `apps/core/tests/test_production_demo_seed.py::test_seed_rerun_is_idempotent` raises `PermissionDenied` while reindexing a production-demo knowledge document. Stopped after first failure (`1 failed, 113 passed`) to avoid lengthy unrelated seed tests. No fix to that separate seed/indexing workflow was made here. |

## 11. Example conversations (observed in Chrome)

1. **Q:** Which synthetic product uses SUS316 with an electropolished finish? **A:** `SUPPORTED`; Housing 0011 / `SYN-RAG-0011`, with source shown.
2. **Q:** Do you have a SUS316 component with electropolished surface? **A:** `SUPPORTED`; Housing 0011, with no raw provenance or relevance score after the public-output fix.
3. **Q:** Which bushing uses oil-impregnated bronze? **A:** `SUPPORTED`; Bushing 0015 / `SYN-RAG-0015`, with source shown.
4. **Q:** What is today's weather in Tokyo? **A:** `UNAVAILABLE`; no source and no invented weather.
5. **Q:** What is the sales price of SYN-RAG-0001? **A:** `UNAVAILABLE`; no invented price.

Empty input shows `Vui lòng nhập câu hỏi.` in the widget. Server-side tests reject empty and over-1200-character input with HTTP 400.

## 12. Known limitations

- Corpus is synthetic, not approved company product knowledge. This is a local development demo only.
- Development hash embedding plus lexical reranking is not full semantic retrieval; paraphrase quality can vary. Local Ollama answer wording is nondeterministic.
- The public output boundary is intentionally conservative: if generated text contains forbidden technical metadata or is too long, it returns `UNAVAILABLE` rather than risk exposure.
- Browser history is memory-only; there is no long-term memory, account, lead capture, RFQ, CRM, sales AI, or production-grade distributed rate limit.
- The wider repository's production-demo seed test failure and an authenticated Admin browser E2E remain unresolved verification items.

## 13. Merge readiness

**NOT READY** for merge or public production release. The scoped public RAG demo is functional and its focused tests pass, but the full backend suite has a separate seed/indexing failure, authenticated Admin browser E2E was not completed, and the synthetic corpus has no production/public approval. Review and resolve those points before any merge decision. No merge or push was performed.
