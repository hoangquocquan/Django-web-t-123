# Production-Like Data Discovery + Seed Design for WEB Ô TÔ DJANGO

Date: 2026-09-18  
Scope: discovery and seed design only. This document does not implement seed code, does not mutate PostgreSQL, and does not change application behavior.

## 1. Executive summary

CURRENT_SOURCE_FACT: The current project is a Django + React/Vite business system with canonical backend domains for foundation auth/roles, master data, RFQ, quotation, order, audit, knowledge/RAG, and AI assistants. The current release posture is portfolio production-demo readiness, not public production certification.

CURRENT_SOURCE_FACT: The backend already contains a canonical command-service path for the important RFQ -> technical review -> quotation -> approval -> sent -> customer decision -> order conversion lifecycle. It also contains local AI governance, Knowledge/RAG indexing, a read-only AI agent tool registry, and an AI Sales Assistant that makes advisory recommendations without executing business changes.

PROPOSED_DATA_DESIGN: Implement a future production-like fictional seed as a separate, explicit, idempotent management command that creates safe demo-owned records through canonical services wherever lifecycle invariants exist. The seed should not reuse the existing `demo_data.py` generator as the canonical source, because that command is broad, legacy-compatible, direct-ORM-heavy, and not designed around the current canonical RFQ/quotation/order lifecycle.

PROPOSED_DATA_DESIGN: The seed should create coherent business data, knowledge documents, and AI evaluation questions that let a reviewer test:

- normal website/admin UI flows;
- search, filter, pagination, status chips, dashboards, and timelines;
- canonical RFQ -> quotation -> order conversion;
- RAG document search and source-grounded answers;
- AI Sales Assistant live-data questions from CRM/sales/inventory/order facts;
- clear separation between stable company knowledge and live transactional database data.

OPEN_QUESTION: The source currently uses `auto_now_add`, append-only models, and service-level `timezone.now()` calls. If the Owner wants a realistic 18-24 month historical event timeline, implementation should either add a small approved clock-injection seam or use an explicitly reviewed seed-only timestamp strategy. The design below is still ready, but this detail must be decided before coding historical timestamps.

## 2. Source-code inventory

CURRENT_SOURCE_FACT: Primary backend path is `django_backend/`. Primary frontend path is `figma_make_frontend/`. Legacy paths are retained but should not be the seed target.

CURRENT_SOURCE_FACT: Important backend apps inspected for this seed design:

| Area | Source files / modules | Seed relevance |
| --- | --- | --- |
| Settings/runtime | `django_backend/config/settings/base.py`, `production.py` | Environment safety, Redis/Ollama/AI settings, PostgreSQL requirement in production. |
| Foundation | `apps/foundation/models.py` | Users, roles, permissions, profiles, auth tokens, login attempts, 2FA challenges. |
| Business core | `apps/business_core/models.py`, business-number services | Customers, parts/products, materials, warehouses, inventory, number allocation. |
| Sales canonical | `apps/sales/models.py`, `apps/sales/quotation_domain.py` | RFQ, RFQ lines, documents, technical review, quotations, quotation lines, approval/customer decisions. |
| API command services | `apps/api/services/canonical_command_service.py` | Preferred lifecycle creation/update path and permission enforcement. |
| Canonical URLs | `apps/api/canonical_urls.py` | Confirms callable canonical API surface for customers, parts, materials, RFQ, quotation, order, timelines, audit. |
| Transaction domain | `apps/transaction_domain/models.py` | Orders, order items, order progress, append-only audit events, conversion invariants. |
| Knowledge/RAG | `apps/knowledge/models.py`, `services/knowledge_service.py`, `knowledge_indexer.py`, `embedding_service.py`, `text_processing.py`, `search_service.py` | Source documents, chunks, embeddings, access levels, RAG search. |
| AI foundation | `apps/ai/models.py`, `services/governance_service.py`, `ollama_client.py`, `rate_limit_service.py`, `policy_service.py` | AI governance, local Ollama, rate limits, redaction, policy audit. |
| AI agent | `apps/ai_agent/models.py`, `services/tools.py`, `services/sales_assistant.py`, `services/sales_facts.py` | Read-only tool registry and advisory AI sales actions. |
| Existing fixtures | `apps/core/management/commands/phase6b_e2e_fixture.py` | Safe E2E fixture to preserve. |
| Existing demo generator | `apps/core/management/commands/demo_data.py` | Useful reference, but not canonical enough for production-like seed. |
| Frontend | `figma_make_frontend/src/App.tsx`, `components/AdminLayout.tsx`, frontend tests | Existing dashboard/AI navigation surface and UI expectations. |

CURRENT_SOURCE_FACT: `phase6b_e2e_fixture.py` creates a small, idempotent E2E set with markers such as `CUS-PHASE6B-E2E`, `MAT-PHASE6B-E2E`, and `PART-PHASE6B-E2E`. Production-like seed must not delete, overwrite, or assume ownership of those records.

CURRENT_SOURCE_FACT: `demo_data.py` currently creates large broad demo data using direct ORM and bulk operations. Its marker strategy includes `demo_data=true`, `DEMO-`, `@demo.mecprecision.local`, and `[DEMO]`. It should remain separate from the proposed production-like canonical seed.

## 3. Exact model/data dependency map

CURRENT_SOURCE_FACT: The core dependency order is:

1. `FoundationPermission`
2. `FoundationRole`
3. `FoundationRolePermission`
4. `FoundationUser`
5. `FoundationUserProfile`
6. `BusinessMaterial`
7. `BusinessProduct`
8. `BusinessCustomer`
9. `InventoryWarehouse`
10. `InventoryItem`
11. `InventoryTransaction`
12. CRM/sales pipeline records such as `SalesLead`, `SalesOpportunity`, `SalesFollowUp`, `SalesActivity`
13. `SalesRfq`
14. `SalesRfqLine`
15. `SalesRfqDocument`
16. `SalesTechnicalReview`
17. `SalesQuotation`
18. `SalesQuotationLine`
19. `SalesQuotationApprovalDecision`
20. `SalesQuotationCustomerDecision`
21. `TransactionOrder`
22. `TransactionOrderItem`
23. `OrderProgressEvent`
24. `AuditEvent`
25. `DocumentCategory`
26. `KnowledgeDocument`
27. `DocumentPermission`
28. `DocumentVersion`
29. `KnowledgeChunk`
30. `KnowledgeEmbedding`
31. `KnowledgeAssistantLog`
32. `AIGovernanceEvent`, `AgentRun`, `AgentToolAudit`

CURRENT_SOURCE_FACT: The canonical RFQ lifecycle depends on active MVP_V1 customers, canonical parts/materials, users with permissions, valid dates, required line evidence, and drawing documents when `drawing_required=True`.

CURRENT_SOURCE_FACT: The canonical quotation lifecycle depends on a `READY_TO_QUOTE` RFQ, unique quotation family/revision rules, immutable commercial snapshots after draft, maker-checker approval, send evidence, customer decision evidence, and idempotency keys.

CURRENT_SOURCE_FACT: The canonical order lifecycle depends on an accepted quotation and conversion authorization. MVP_V1 orders and order items should not be bulk-created directly.

PROPOSED_DATA_DESIGN: Seed dependencies should be generated in this order:

1. Reuse or create only seed-owned demo actors under existing real roles/permissions.
2. Create customers, materials, parts/products.
3. Create warehouses and inventory rows.
4. Create CRM/pipeline records for AI Sales Assistant and dashboard realism.
5. Create RFQ headers, lines, documents, and reviews using canonical services.
6. Create quotation revisions and decisions using canonical services/domain functions.
7. Convert accepted quotations to orders using canonical conversion.
8. Advance a subset of orders with progress services.
9. Create knowledge documents through `KnowledgeService` so chunking/indexing is exercised.
10. Create or store AI evaluation fixtures separately from production records unless a database model already exists for that exact purpose.

## 4. Supported lifecycle map

CURRENT_SOURCE_FACT: RFQ statuses are `DRAFT`, `SUBMITTED`, `UNDER_REVIEW`, `NEEDS_INFORMATION`, `READY_TO_QUOTE`, `QUOTED`, `DECLINED`, and `CLOSED`.

CURRENT_SOURCE_FACT: Canonical command services support these RFQ paths:

- create RFQ as `DRAFT`;
- add/update/remove draft or requested-info lines;
- submit `DRAFT -> SUBMITTED`;
- start technical review `SUBMITTED -> UNDER_REVIEW`;
- request information `UNDER_REVIEW -> NEEDS_INFORMATION`;
- resubmit `NEEDS_INFORMATION -> SUBMITTED`;
- complete review `UNDER_REVIEW -> READY_TO_QUOTE`;
- decline review `UNDER_REVIEW -> DECLINED`;
- acknowledge declined `DECLINED -> CLOSED`;
- archive draft `DRAFT -> CLOSED`.

CURRENT_SOURCE_FACT: Quotation statuses are `DRAFT`, `PENDING_APPROVAL`, `APPROVED`, `REJECTED`, `SENT`, `ACCEPTED`, `DECLINED`, `EXPIRED`, and `SUPERSEDED`.

CURRENT_SOURCE_FACT: Canonical/domain services support these quotation paths:

- create first quotation revision from `READY_TO_QUOTE` RFQ as `DRAFT`;
- update draft pricing;
- submit `DRAFT -> PENDING_APPROVAL`;
- approve or reject `PENDING_APPROVAL -> APPROVED/REJECTED`;
- send `APPROVED -> SENT`;
- record customer decision `SENT -> ACCEPTED/DECLINED`;
- create a new revision only when latest revision is `REJECTED`;
- supersede eligible effective revisions when a new revision becomes approved;
- archive eligible draft as `SUPERSEDED`.

CURRENT_SOURCE_FACT: The model declares `SENT -> EXPIRED`, but the inspected canonical URL/command path does not expose a dedicated expire action. This should be confirmed before seeding expired quotations.

CURRENT_SOURCE_FACT: Order statuses are `CONFIRMED`, `IN_PROGRESS`, `ON_HOLD`, `COMPLETED`, and `CANCELLED`.

CURRENT_SOURCE_FACT: Canonical order progress services support progression, hold, resume, complete, and cancel while writing append-only progress/audit evidence.

PROPOSED_DATA_DESIGN: Future seed should create real lifecycle diversity by walking records through services, not by assigning final statuses directly. Records should stop naturally at target statuses to preserve audit/timeline realism.

## 5. Proposed data volumes

PROPOSED_DATA_DESIGN: Use three explicit profiles. All counts below are targets, not hard requirements.

| Domain | TEST | SMALL | FULL |
| --- | ---: | ---: | ---: |
| Demo users | 6 | 12 | 30 |
| Customers | 12 | 60 | 200 |
| Materials | 12 | 35 | 100 |
| Parts/products | 30 | 150 | 600 |
| Warehouses | 2 | 3 | 4 |
| Inventory items | 40 | 250 | 900 |
| Inventory transactions | 80 | 750 | 3,000 |
| Sales leads | 25 | 180 | 700 |
| Opportunities | 15 | 100 | 350 |
| CRM activities/follow-ups | 80 | 800 | 4,000 |
| RFQs | 35 | 300 | 1,500 |
| RFQ lines | 80 | 900 | 5,000 |
| RFQ documents | 30 | 300 | 1,200 |
| Technical reviews | 25 | 250 | 1,250 |
| Quotation revisions | 20 | 220 | 1,000 |
| Quotation lines | 50 | 650 | 3,200 |
| Approval/customer decisions | 20 | 200 | 900 |
| Orders | 8 | 100 | 500 |
| Order items | 20 | 300 | 1,600 |
| Order progress events | 18 | 300 | 2,000 |
| Audit events | service-derived | service-derived | service-derived, expected 8,000-25,000 |
| Knowledge documents | 12 | 60 | 200 |
| Knowledge chunks | approx. 80-250 | approx. 800-2,000 | approx. 3,000-8,000 |
| AI evaluation cases | 20 | 60 | 150 |

PROPOSED_DATA_DESIGN: FULL is intended for a portfolio production-demo environment. SMALL is intended for local UI review. TEST is intended for CI-style quick validation and deterministic behavior.

## 6. Status distributions

PROPOSED_DATA_DESIGN: RFQ target distribution for FULL:

| RFQ status | Share | Purpose |
| --- | ---: | --- |
| DRAFT | 8% | Shows editable intake and unfinished customer requests. |
| SUBMITTED | 8% | Shows review queue before technical assignment. |
| UNDER_REVIEW | 10% | Shows active engineering review. |
| NEEDS_INFORMATION | 8% | Shows missing-document/customer follow-up path. |
| READY_TO_QUOTE | 10% | Shows quote creation queue. |
| QUOTED | 35% | Shows completed commercial handling where source supports it. |
| DECLINED | 8% | Shows technical rejection. |
| CLOSED | 13% | Shows archived/acknowledged outcomes. |

OPEN_QUESTION: Before implementation, confirm the exact canonical source behavior that moves RFQ to `QUOTED`, because inspected quotation creation code creates quotations from `READY_TO_QUOTE` but the RFQ status update path needs final source confirmation.

PROPOSED_DATA_DESIGN: Quotation target distribution for FULL:

| Quotation status | Share | Purpose |
| --- | ---: | --- |
| DRAFT | 8% | Editable quotation workbench. |
| PENDING_APPROVAL | 8% | Manager approval queue. |
| APPROVED | 7% | Ready-to-send work queue. |
| REJECTED | 7% | Revision workflow and maker-checker evidence. |
| SENT | 12% | Customer-response queue. |
| ACCEPTED | 40% | Feeds canonical order conversion. |
| DECLINED | 10% | Lost business analysis. |
| SUPERSEDED | 8% | Revision history realism. |
| EXPIRED | 0-5% optional | Only if an approved canonical expire path is confirmed. |

PROPOSED_DATA_DESIGN: Order target distribution for FULL:

| Order status | Share | Purpose |
| --- | ---: | --- |
| CONFIRMED | 18% | Newly converted work. |
| IN_PROGRESS | 38% | Main operations dashboard. |
| ON_HOLD | 8% | Issue escalation and AI recommendations. |
| COMPLETED | 28% | Historical delivery and revenue patterns. |
| CANCELLED | 8% | Exception handling. |

PROPOSED_DATA_DESIGN: Sales lead target distribution should align to AI Sales Assistant scoring: `new` 20%, `contacted` 18%, `meeting` 16%, `quotation` 15%, `negotiation` 12%, `won` 11%, `lost` 8%.

## 7. Correlation rules

PROPOSED_DATA_DESIGN: Data should be correlated instead of random:

- Customer industry influences part family, material, tolerances, order cadence, and typical value.
- Japanese/Korean/industrial-equipment customers should more often request tighter tolerances, more drawing revisions, and more formal document evidence.
- Automotive customers should have repeat RFQs, larger batch sizes, more PPAP/FAI/inspection knowledge queries, and stronger seasonality.
- CNC fixture and jig demand should correlate with SKD11/S45C/A6061 and with urgent quote due dates.
- High-priority leads should correlate with later-stage pipeline statuses and more frequent AI recommendations.
- Customers with recent `NEEDS_INFORMATION` RFQs should have follow-up activities and AI email-draft opportunities.
- Accepted quotations should mostly convert to orders; declined quotations should not.
- ON_HOLD orders should correlate with material delay, drawing revision, customer approval, or capacity constraint reasons.
- Inventory reorder risk should correlate with active orders for the same part/material family.

PROPOSED_DATA_DESIGN: Avoid fake data that looks personally sensitive. Use fictional company names, safe `.invalid` or clearly non-deliverable domains, and fictional phone formats.

## 8. Time distribution

PROPOSED_DATA_DESIGN: Generate a rolling 24-month data window ending near the seed execution date. With the current project date context, a representative FULL demo window is October 2024 through September 2026.

PROPOSED_DATA_DESIGN: Suggested seasonality:

| Time band | Relative volume | Notes |
| --- | ---: | --- |
| Months 1-6 | 18% | Early history, lower volume, fewer active records. |
| Months 7-12 | 24% | Growth period, more repeat customers. |
| Months 13-18 | 28% | Mature operations, more orders and knowledge usage. |
| Months 19-24 | 30% | Most visible current dashboard activity. |

PROPOSED_DATA_DESIGN: Date realism rules:

- RFQ created date < quote due date <= required delivery date.
- Technical review occurs after RFQ submission.
- Quotation valid window starts near approval/send date and ends after send date.
- Customer decision occurs after sent date.
- Order date occurs after accepted quotation.
- Order progress events occur in chronological order.
- Completed orders end with progress 100.
- ON_HOLD and CANCELLED orders require reasons.

OPEN_QUESTION: Historical timestamps require a safe implementation method because many current fields are auto-managed and some evidence tables are append-only.

## 9. Knowledge/RAG dataset design

CURRENT_SOURCE_FACT: Knowledge documents support categories, permission levels (`public`, `internal`, `restricted`), versions, chunks, embeddings, and assistant logs. `KnowledgeService.create_document` indexes content through `KnowledgeIndexer`.

PROPOSED_DATA_DESIGN: FULL should create approximately 200 fictional internal documents:

| Category | Count | Example document themes |
| --- | ---: | --- |
| Company capability | 20 | CNC milling/turning capability, machine envelope, materials handled. |
| RFQ intake SOP | 20 | Required drawings, tolerance clarification, quote due triage, customer communication scripts. |
| Quotation policy | 20 | Pricing assumptions, revision policy, approval matrix, validity windows. |
| Quality/inspection | 35 | FAI, CMM inspection, material certificates, nonconformance handling. |
| Manufacturing process | 35 | Process planning, jig/fixture notes, heat treatment, surface treatment. |
| Logistics/delivery | 20 | Lead time bands, partial shipment, urgent order handling. |
| Sales playbooks | 25 | Lead scoring, follow-up cadence, email templates, objection handling. |
| AI assistant guidance | 15 | What AI may answer, source citation expectations, human approval rules. |
| Demo FAQs | 10 | Portfolio-demo caveats and sample-data disclaimers. |

PROPOSED_DATA_DESIGN: Knowledge content should deliberately mention the same fictional product families, materials, tolerances, and workflow terms used in transactional data so RAG can retrieve useful source context for sales and engineering questions.

PROPOSED_DATA_DESIGN: Do not put live RFQ/order rows into RAG as copied documents. RAG should contain stable policies, SOPs, catalog-like facts, templates, and reference explanations.

## 10. RAG indexing implications

CURRENT_SOURCE_FACT: `TextProcessor.chunk_text` defaults to chunk size 800 with overlap 120. `KnowledgeIndexer.reindex` deletes old chunks for a document and recreates chunks plus embeddings in a transaction after embedding generation.

CURRENT_SOURCE_FACT: Default embedding provider is local Ollama unless settings select `development-hash`, `local-fallback`, or `test`, which use deterministic 32-dimensional local hash embeddings.

PROPOSED_DATA_DESIGN: TEST and SMALL profiles should support a deterministic local embedding mode so development and CI do not depend on Ollama availability.

PROPOSED_DATA_DESIGN: FULL should prefer the configured real local embedding provider only when the runtime health check passes. If the embedding provider is unavailable, implementation should stop with a clear error or run in a documented `--skip-index` mode that leaves documents created but reports that RAG validation is incomplete.

PROPOSED_DATA_DESIGN: FULL document sizes should target 12,000-30,000 characters per long SOP/capability document and 2,000-6,000 characters per FAQ/playbook item. Expected result is roughly 3,000-8,000 chunks, which is enough to exercise vector search latency, document permissions, and source citation UI.

## 11. AI live-data vs RAG boundary

CURRENT_SOURCE_FACT: The AI agent tool registry is read-only. It exposes knowledge search, customer summary, lead summary, sales pipeline summary, inventory summary, system health, database summary, report skeleton, and system information tools.

CURRENT_SOURCE_FACT: `SalesAssistantService` supports `lead_analysis`, `customer_summary`, `email_draft`, and `weekly_recommendation`. It returns `human_approval_required=True` and `autonomous_action=False`.

CURRENT_SOURCE_FACT: `BusinessKnowledgeConnector` can provide small read-only samples of products, customers, inventory, and orders to the knowledge assistant.

PROPOSED_DATA_DESIGN: Use this boundary:

| Question type | Best source | Example |
| --- | --- | --- |
| Policy, SOP, capability, quality requirement | RAG documents | “Khi khách thiếu bản vẽ STEP thì quy trình RFQ là gì?” |
| Current counts, statuses, pipeline value, reorder risk | Live DB/API/read-only tools | “Có bao nhiêu RFQ đang NEEDS_INFORMATION?” |
| Customer/order-specific summary | Live DB/API/read-only tools plus optional RAG | “Tóm tắt khách hàng ABC và gợi ý bước tiếp theo.” |
| Email draft based on customer interest | Live lead/customer facts + RAG playbook | “Soạn email follow-up cho lead ngành automotive.” |
| Action execution | Human workflow only | AI may suggest; it must not approve quote, send email, mutate CRM, or create order. |

PROPOSED_DATA_DESIGN: The seed should create enough live data for AI tools to answer operational questions and enough RAG data for source-grounded explanation. It should not blur those into one duplicated data source.

## 12. AI evaluation dataset

PROPOSED_DATA_DESIGN: Store AI evaluation cases as versioned fixture files first, not as business production rows unless a dedicated model is introduced later.

PROPOSED_DATA_DESIGN: Suggested structure:

```json
{
  "id": "pdv1-ai-eval-001",
  "profile": "FULL",
  "question": "Lead nào nên ưu tiên gọi lại tuần này?",
  "expected_sources": ["live:sales_pipeline", "rag:sales_playbook"],
  "expected_behavior": ["advisory_only", "human_approval_required", "no_database_write"],
  "must_not_include": ["secret", "raw token", "autonomous approval"],
  "answer_checks": ["mentions lead status", "mentions reason", "mentions next human step"]
}
```

PROPOSED_DATA_DESIGN: FULL should include about 150 cases:

- 35 RAG-only policy/SOP questions;
- 35 live DB aggregate questions;
- 30 mixed RAG + live-data sales-assistant questions;
- 20 safety/governance questions that should be blocked or redacted;
- 20 no-answer/low-confidence questions;
- 10 Vietnamese UI phrasing/regression cases.

## 13. Seed ownership strategy

PROPOSED_DATA_DESIGN: Use a unique dataset marker: `production_demo_v1`.

PROPOSED_DATA_DESIGN: Ownership markers should use safe, non-secret fields:

| Domain | Marker strategy |
| --- | --- |
| Users | email domain such as `@production-demo.invalid`; full name suffix `[Production Demo]`. |
| Customers | `notes` contains `dataset=production_demo_v1`; generated customer codes remain canonical allocator-owned. |
| Materials | `description` contains `dataset=production_demo_v1`. |
| Parts/products | `sku` or technical requirements contain `PDV1` / `dataset=production_demo_v1`; part codes remain allocator-owned. |
| RFQs | `project_name` prefix `[PDV1]`; `notes` contains safe dataset marker. |
| Quotation/order commands | deterministic `idempotency_key` prefix `pdv1-...`; terms/messages include safe marker when writable through service. |
| Audit metadata | safe keys only, e.g. `dataset`, `profile`, `seed_run`; avoid banned key fragments such as email, phone, password, token. |
| Knowledge documents | title prefix `[PDV1]`; metadata contains `dataset=production_demo_v1`. |
| Evaluation fixtures | file path/name includes `production_demo_v1`. |

CURRENT_SOURCE_FACT: `AuditEvent` rejects unsafe metadata keys containing sensitive fragments. Seed metadata must therefore avoid keys like `email`, `phone`, `password`, `token`, or similar.

PROPOSED_DATA_DESIGN: The future clear/update command must only target records with the production-demo marker and must explicitly avoid Phase 6B E2E fixture markers and older `DEMO` markers unless the Owner requests a separate migration/cleanup.

## 14. Idempotency strategy

PROPOSED_DATA_DESIGN: The seed should be repeatable:

- Use deterministic random seeds per profile.
- Use deterministic external identities and idempotency keys.
- Read existing demo-owned records before creating new ones.
- Route canonical objects through idempotent command services when they expose `idempotency_key`.
- Keep a seed manifest in code describing dataset version, profile, expected counts, and marker.
- On rerun, either reconcile missing demo-owned records or stop with a clear “partial run detected” report.

PROPOSED_DATA_DESIGN: Destructive cleanup should be separate from creation, disabled by default, and require an explicit flag such as `--replace-owned` plus an environment gate. It must delete in reverse dependency order and only for records proven to be production-demo-owned.

PROPOSED_DATA_DESIGN: Command output should include a count summary and a validation summary so the Owner can paste it into future release notes.

## 15. Environment safety

CURRENT_SOURCE_FACT: Production settings fail closed around secret key, PostgreSQL `DATABASE_URL`, Redis URL, allowed hosts, metrics token, AI Redis rate limiting, and AI Ollama capacity.

PROPOSED_DATA_DESIGN: Future seed command should refuse to run unless all of these are true:

- an explicit environment variable such as `PRODUCTION_DEMO_SEED_ALLOWED=true` is present;
- the requested profile is one of `TEST`, `SMALL`, `FULL`;
- database connection is not an unknown public production database;
- `--dry-run` is the default display mode unless `--apply` is passed;
- command prints target database identity before applying;
- command refuses if unapplied migrations exist;
- command refuses if required canonical permissions/roles are missing;
- command refuses if existing non-demo data would be deleted or overwritten.

PROPOSED_DATA_DESIGN: The command must not create auth tokens, login attempts, 2FA challenges, real secrets, real credentials, real customer PII, or deliverable email addresses.

## 16. Performance/batching strategy

PROPOSED_DATA_DESIGN: Use lifecycle services for RFQ, quotation, order, progress, and audit-producing actions even if slower. These are correctness-critical.

PROPOSED_DATA_DESIGN: Direct ORM and `bulk_create` are acceptable only for low-risk supporting records without canonical lifecycle guards, such as warehouses, inventory snapshots, CRM activities, or purely seed-owned evaluation rows, after model constraints are respected.

PROPOSED_DATA_DESIGN: Suggested batching:

- Precompute deterministic customer/material/part catalogs in memory.
- Create master data in batches of 100-500 where canonical services are not required.
- Process RFQ/quotation/order chains in small transactions per business case, not one huge transaction.
- Index knowledge documents in batches with progress output every 10 documents.
- For FULL, allow `--skip-rag-index` and `--rag-only` operational modes for recovery.
- Print progress checkpoints with elapsed time and created/reused/skipped counts.

PROPOSED_DATA_DESIGN: Expected runtime depends heavily on embedding provider. TEST should be seconds to a few minutes; SMALL should be several minutes; FULL may be tens of minutes if local Ollama embeddings are generated.

## 17. SMALL/FULL/TEST profiles

PROPOSED_DATA_DESIGN: TEST profile:

- deterministic tiny dataset;
- hash/local fallback embeddings;
- enough records to verify every lifecycle branch once;
- intended for automated tests and quick local sanity checks.

PROPOSED_DATA_DESIGN: SMALL profile:

- realistic visual dataset for local browser review;
- enough rows for pagination, filtering, dashboard cards, and AI assistant examples;
- can run on developer machines without large embedding cost.

PROPOSED_DATA_DESIGN: FULL profile:

- portfolio-demo dataset with dense history, realistic correlations, and broad AI evaluation coverage;
- enough records to expose performance issues;
- intended for the production-demo branch/environment only after Owner approval.

PROPOSED_DATA_DESIGN: Profile selection must be explicit. There should be no hidden default that silently seeds FULL.

## 18. Proposed implementation file structure

PROPOSED_DATA_DESIGN: Recommended future implementation structure:

```text
django_backend/
  apps/
    core/
      management/
        commands/
          seed_production_demo.py
      production_demo_seed/
        __init__.py
        profiles.py
        ownership.py
        safety.py
        generators.py
        distributions.py
        lifecycle.py
        knowledge_templates.py
        ai_eval_cases.py
        validators.py
        report.py
      tests/
        test_seed_production_demo_safety.py
        test_seed_production_demo_idempotency.py
        test_seed_production_demo_lifecycle.py
        test_seed_production_demo_knowledge.py
```

PROPOSED_DATA_DESIGN: `seed_production_demo.py` should be thin: parse flags, run safety checks, call orchestrator, print summary.

PROPOSED_DATA_DESIGN: `lifecycle.py` should wrap existing canonical services and keep all workflow transitions in one place. `generators.py` should only generate fictional inputs; it should not save business records directly where canonical services exist.

PROPOSED_DATA_DESIGN: `validators.py` should check counts, status distributions, ownership markers, forbidden artifacts/secrets, and AI/RAG readiness.

## 19. Validation plan

PROPOSED_DATA_DESIGN: Required validation after future implementation:

1. `python manage.py check`
2. `python manage.py makemigrations --check --dry-run`
3. seed dry run for TEST, SMALL, FULL
4. apply TEST seed to disposable database
5. rerun TEST seed and verify idempotency
6. verify no Phase 6B E2E records were modified
7. verify count and status distribution summary
8. verify RFQ lifecycle evidence and audit timeline
9. verify quotation maker-checker decisions
10. verify accepted quotations converted to orders
11. verify order progress events and final statuses
12. verify knowledge documents were chunked and searchable
13. verify AI Sales Assistant can answer lead analysis/customer summary/email draft/weekly recommendation on seed data
14. verify AI actions remain advisory only and produce no autonomous business mutation
15. verify frontend dashboard/search/filter/pagination routes render with the new volume
16. verify no real secrets or deliverable PII-like records are present
17. verify clear/replace-owned behavior in a disposable database only

PROPOSED_DATA_DESIGN: Suggested focused tests:

- seed safety refuses without environment gate;
- seed dry-run performs no writes;
- seed apply creates expected markers;
- rerun does not duplicate records;
- partial run recovery is deterministic;
- RFQ missing-document branches are represented;
- quotation rejection/revision branch is represented;
- order hold/resume/complete/cancel branches are represented;
- RAG search returns seeded source titles;
- AI Sales Assistant returns `human_approval_required=True`.

## 20. Risks/open questions

OPEN_QUESTION: Historical timestamps require an Owner-approved implementation approach because append-only and auto-managed fields prevent simple post-creation timestamp rewrites.

OPEN_QUESTION: Confirm the exact supported path for RFQ `QUOTED` status before seeding that status at scale.

OPEN_QUESTION: Confirm whether `EXPIRED` quotations should be seeded now. The model supports the status transition, but the inspected canonical API path does not expose a dedicated expire action.

OPEN_QUESTION: `KnowledgeService.list_documents` appears to check `role.name == "admin"` while existing canonical role names may be capitalized such as `Admin`, `Sales`, `Manager`. Confirm or fix before relying on admin-only document visibility in demos.

OPEN_QUESTION: Confirm whether production-demo users should have a known shared demo password, disabled login accounts, or password creation only through a secure Owner-provided stdin flow. The seed should not hardcode a real credential.

OPEN_QUESTION: Confirm whether the AI UI branch `codex/ai-assistant-update` should be merged before final frontend validation, because seed data can support both current route-level AI surfaces and the newer AI interface.

OPEN_QUESTION: Confirm whether inventory should remain supporting data created by ORM or should receive its own canonical command service before FULL seeding.

CURRENT_SOURCE_FACT: Existing `demo_data.py` deletes records matching its own demo markers. If both old demo data and new production-demo seed data coexist, the marker strategies must stay separate.

PROPOSED_DATA_DESIGN: None of the above open questions block the design. They are implementation decisions to resolve before coding or running FULL.

## 21. Implementation recommendation

PROPOSED_DATA_DESIGN: Proceed with a new production-demo seed implementation only after Owner approval, using this plan as the contract. Start with TEST profile and safety/idempotency tests, then implement SMALL, then FULL.

PROPOSED_DATA_DESIGN: Do not modify or replace `demo_data.py` initially. Keep the new seed isolated so rollback and review are easy.

PROPOSED_DATA_DESIGN: The first implementation milestone should be:

1. create file structure and profile definitions;
2. implement safety gates and dry-run report;
3. implement seed-owned users/master data;
4. implement a small canonical RFQ -> quotation -> order chain;
5. implement knowledge documents with deterministic embedding fallback;
6. add validation tests;
7. run TEST profile on a disposable local database;
8. only then scale to SMALL/FULL.

READY_TO_IMPLEMENT_PRODUCTION_LIKE_SEED
