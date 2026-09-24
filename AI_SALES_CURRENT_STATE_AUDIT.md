# AI Sales current-state audit

Audit baseline: `main` at `c03d55506ef3ffd38e5e7bb290b981c1a3ccb17f` before work on `feature/ai-sales-assistant`.

## Existing files and services

- `django_backend/apps/ai_agent/services/sales_assistant.py` already provides `SalesAssistantService` with lead analysis, customer summaries, draft email generation, and weekly recommendations.
- `django_backend/apps/ai_agent/services/sales_facts.py` creates a minimized deterministic fact envelope for generation.
- `django_backend/apps/ai_agent/services/sales_synthesis.py` uses the existing Ollama abstraction, validates structured output, rejects autonomous-action claims, and falls back safely.
- `django_backend/apps/ai_agent/views.py` exposes the existing AI Sales controller and runs authentication, permission, and AI-governance checks.
- `django_backend/apps/knowledge/services/search_service.py` is the governed knowledge search used by AI Sales.
- `django_backend/apps/knowledge/services/synthetic_rag_demo.py` provides the isolated internal synthetic component corpus, grounded retrieval, generation-provider abstraction, citations, and explicit unsupported behavior.
- `django_backend/apps/knowledge/services/access_policy.py` controls document and chunk readability.
- `django_backend/apps/ai/services/governance_service.py` records correlation IDs, actors, policy decisions, hashes, and redacted metadata.

## Existing API endpoints

- `POST /api/v1/ai/sales-assistant/` supports `lead_analysis`, `customer_summary`, `email_draft`, and `weekly_recommendation` for users with `ai_sales:read`.
- `POST /api/v1/internal/rag-demo/query/` and `POST /api/v1/internal/rag-chat/` expose the authenticated synthetic technical RAG workflow.
- `POST /api/v1/public/ai-component-demo/` is a separately gated public surface and does not use sales context.

## Existing models

- Sales: `SalesLead`, `SalesOpportunity`, `SalesRfq`, `SalesRfqLine`, `SalesRfqDocument`, `SalesQuotation`, `SalesFollowUp`, and `SalesActivity`.
- Business: `BusinessCustomer`, `BusinessProduct`, and `BusinessMaterial`.
- Transaction domain: canonical orders and order progress/audit records.
- AI audit: `AIGovernanceEvent`, `AgentRun`, and `AgentToolAudit`.

A new Lead model is not justified. The existing sales and RFQ aggregates cover the MVP domain.

## Existing tests

- `tests/test_sales_crm_ai.py` covers authenticated AI Sales RAG use, drafts, and human approval.
- `tests/test_ai_sales_grounded_synthesis.py` covers source validation, deterministic scoring protection, provider failure, unsafe output rejection, and draft-only behavior.
- `tests/test_ai_enterprise_governance.py` and `tests/test_ai_governance_v2.py` cover governance policy and audit behavior.
- Knowledge tests cover internal/public isolation, access policy, synthetic retrieval, citations, and unsupported queries.

## Existing UI

- The Django business UI already has `/business/ai-sales/` with structured lead-analysis and draft cards.
- The React application has a `#/sales-ai` placeholder, but it is static and is not wired to the AI Sales API.
- The React admin area already has working authenticated internal RAG pages that can be reused as the UI integration pattern.

## Existing RAG integration

The legacy AI Sales service already calls `KnowledgeSearchService`; the synthetic component demo uses the same embeddings, vector store, governed knowledge records, RAG generation pipeline, and citation chain. Public access is independently scoped and gated.

## Missing pieces for this MVP

- No single structured contract with `SUPPORTED`, `NEEDS_MORE_INFORMATION`, and `UNAVAILABLE`.
- No RFQ-aware analysis endpoint under `/api/v1/internal/ai-sales/`.
- Existing lead output uses a numeric score/grade rather than the requested explainable `HIGH`, `MEDIUM`, `LOW`, or `NEEDS_REVIEW` priority.
- No grounded component-match list, normalized missing-information list, or constrained next-action enum in one response.
- No React `#/admin-ai-sales` workspace connected to the internal API.
- No deterministic endpoint/security/public-isolation tests for the three required request cases.

## Reuse decisions

- Extend `SalesAssistantService`; do not create a parallel AI Sales subsystem.
- Reuse canonical `SalesRfq` and existing lead/opportunity/customer/product models; add no migration.
- Reuse the internal synthetic RAG service for the controlled MVP component corpus and its existing generation fallback.
- Reuse `FoundationPermissionService` and `AIGovernanceService` for authorization and traceability.
- Preserve the legacy endpoint and Django business UI to avoid breaking existing workflows.

## Code that should remain untouched

- Public AI enablement flags and public endpoint behavior.
- Quotation approval/send, order transitions, pricing, and customer-contact commands.
- Existing lead/opportunity/RFQ/quotation schemas.
- The current knowledge approval, indexing, and public-release governance rules.
