# Production-Like Seed Milestone 2 Report

Date: 2026-09-18  
Scope: SMALL profile implementation + seed-only historical timestamp strategy. FULL is not implemented.

## 1. Files changed

Added/updated seed implementation:

- `django_backend/apps/core/management/commands/seed_production_demo.py`
- `django_backend/apps/core/production_demo_seed/__init__.py`
- `django_backend/apps/core/production_demo_seed/profiles.py`
- `django_backend/apps/core/production_demo_seed/ownership.py`
- `django_backend/apps/core/production_demo_seed/safety.py`
- `django_backend/apps/core/production_demo_seed/generators.py`
- `django_backend/apps/core/production_demo_seed/lifecycle.py`
- `django_backend/apps/core/production_demo_seed/historical.py`
- `django_backend/apps/core/production_demo_seed/validators.py`
- `django_backend/apps/core/production_demo_seed/report.py`
- `django_backend/apps/core/production_demo_seed/ai_eval_cases.py`
- `django_backend/apps/core/tests/test_production_demo_seed.py`

Added this report:

- `PRODUCTION_LIKE_DATA_SEED_MILESTONE_2_REPORT.md`

Preserved pre-existing unrelated workspace changes:

- `figma_make_frontend/src/App.tsx`
- `figma_make_frontend/src/api/phase6c.test.ts`
- `PROJECT_MASTER_REPORT_FOR_CHATGPT.md`
- `PRODUCTION_LIKE_DATA_SEED_PLAN.md`
- `PRODUCTION_LIKE_DATA_SEED_MILESTONE_1_REPORT.md`

## 2. SMALL profile implementation

Command support now includes:

```bash
python manage.py seed_production_demo --profile TEST --dry-run
python manage.py seed_production_demo --profile TEST --apply
python manage.py seed_production_demo --profile SMALL --dry-run
python manage.py seed_production_demo --profile SMALL --apply
```

FULL remains unsupported.

SMALL extends TEST with:

- 12 seed users;
- larger master data;
- inventory across 3 warehouses;
- CRM profiles/interactions/notes/tasks/timeline events;
- sales leads, opportunities, activities, and follow-ups;
- 300 canonical RFQs;
- multiline RFQs;
- drawing/document-required examples;
- approximately 220 quotation revisions;
- approximately 96 orders generated through accepted quotations;
- historical timestamp backfill for seed-owned rows only;
- 60 knowledge documents;
- 60 AI evaluation cases.

## 3. Actual generated counts

Validated in Django disposable test database:

| Area | Actual / validated |
| --- | ---: |
| Users | 12 |
| Customers | 60 |
| Materials | 35 |
| Parts/products | 150 |
| Warehouses | 3 |
| Inventory rows | 250 target path |
| Inventory transactions | 750 target path |
| Leads | 180 |
| Opportunities | 100 |
| CRM/sales activity/follow-up records | approx. 800 sales activities + related CRM rows/follow-ups |
| RFQs | 300 |
| RFQ lines | approx. 900 |
| RFQ documents | approx. 700, because SMALL creates drawing packets plus supplemental fictional evidence |
| Quotation revisions | approx. 220 |
| Orders | approx. 96; accepted because Owner approved count flexibility where lifecycle coverage wins |
| Knowledge documents | 60 |
| AI evaluation cases | 60 |

## 4. Distribution summary

SMALL uses non-uniform distributions:

- repeat/high-activity customers are concentrated at the beginning of the generated customer set;
- customer segment/lifecycle stage varies across strategic, repeat, standard, active, and nurture profiles;
- lead statuses vary across `new`, `contacted`, `meeting`, `quotation`, `negotiation`, `won`, and `lost`;
- opportunity statuses vary across `open`, `proposal`, `negotiation`, `won`, and `lost`;
- quotation states cover draft, pending approval, approved, sent, rejected, superseded, accepted, and declined;
- order states cover confirmed, in progress, on hold, completed, and cancelled;
- current/open records coexist with historical completed/lost records after timestamp backfill.

## 5. Historical timestamp strategy

Implemented internal seed-only helper:

```text
django_backend/apps/core/production_demo_seed/historical.py
```

Strategy:

1. Create records through canonical services/domain APIs first.
2. For `SMALL`, run `HistoricalTimestampBackfiller` after creation.
3. The backfiller only selects records with production-demo ownership markers or deterministic `pdv1-` keys.
4. It only updates approved timestamp fields.
5. It runs inside `transaction.atomic()`.
6. It validates chronology after update.
7. It is not exposed as an admin/runtime API or management command.

For append-only models, the helper does not change business state. It uses PKs selected from ownership-filtered querysets and updates only whitelisted timestamp columns through the model base manager because append-only default managers correctly block generic `.update()`.

## 6. Exact timestamp fields altered by seed-only helper

Approved fields:

- `BusinessCustomer`: `created_at`, `updated_at`
- `BusinessMaterial`: `created_at`, `updated_at`
- `BusinessProduct`: `created_at`, `updated_at`
- `InventoryTransaction`: `created_at`
- `CrmCustomerProfile`: `created_at`, `updated_at`
- `CrmInteraction`: `created_at`
- `CrmNote`: `created_at`
- `CrmTask`: `created_at`
- `CrmTimelineEvent`: `created_at`
- `SalesLead`: `created_at`, `updated_at`
- `SalesOpportunity`: `created_at`, `updated_at`
- `SalesFollowUp`: `created_at`
- `SalesActivity`: `created_at`
- `SalesRfq`: `created_at`, `updated_at`
- `SalesRfqDocument`: `uploaded_at`
- `SalesTechnicalReview`: `created_at`
- `SalesQuotation`: `created_at`, `updated_at`, `sent_at`
- `SalesQuotationApprovalDecision`: `decided_at`
- `SalesQuotationCustomerDecision`: `decided_at`
- `TransactionOrder`: `created_at`, `updated_at`, `ordered_at`, `source_quotation_sent_at`, `completed_at_v1`
- `OrderProgressEvent`: `created_at`
- `AuditEvent`: `created_at`
- `KnowledgeDocument`: `created_at`, `updated_at`
- `DocumentVersion`: `created_at`
- `KnowledgeChunk`: `created_at`
- `KnowledgeEmbedding`: `created_at`, `indexed_at`

No business status fields are altered by the historical helper.

## 7. Lifecycle coverage

Covered through canonical services/domain APIs:

- RFQ create
- RFQ add line
- RFQ document upload
- RFQ submit
- RFQ start review
- RFQ request information
- RFQ complete review
- RFQ archive
- quotation create
- quotation submit
- quotation approve
- quotation reject
- quotation revision from rejected quotation
- quotation send
- quotation customer accept
- quotation customer decline
- accepted quotation conversion to order
- order progress
- order hold
- order resume
- order complete
- order cancel

Still intentionally omitted:

- RFQ `QUOTED`
- quotation `EXPIRED`

No raw status mutation was used for either unsupported state.

## 8. Idempotency result

Validated in Django test database:

- SMALL apply succeeds.
- SMALL rerun succeeds.
- Rerun does not duplicate customers, materials, parts, RFQs, quotations, orders, or knowledge documents.
- TEST idempotency remains green.

## 9. Performance timings

Observed test runtime:

- SMALL apply + rerun test: approximately 43 seconds for the dedicated SMALL test.
- Full focused seed test file including TEST and SMALL coverage: approximately 50 seconds.

The command also records timing fields in its JSON report:

- `runtime_master_data_ms`
- `runtime_pipeline_inventory_ms`
- `runtime_lifecycle_ms`
- `runtime_knowledge_ms`
- `runtime_historical_ms`
- `runtime_total_ms`

No unsafe bulk shortcut was introduced for RFQ/quotation/order lifecycle.

## 10. Knowledge/RAG result

SMALL creates 60 knowledge documents through `KnowledgeService.create_document`.

SMALL uses `DevelopmentHashEmbeddingProvider` by default, so it does not require live Ollama.

Knowledge document content is expanded for SMALL so chunk volume is suitable for RAG demo/search. The content references the same fictional RFQ, CNC, materials, quotation, quality, logistics, sales, AI-guidance, and demo FAQ concepts used by the transactional dataset.

## 11. AI evaluation result

`load_ai_eval_cases("SMALL")` now returns 60 deterministic cases.

Coverage includes:

- RAG-only questions;
- live DB questions;
- mixed live + RAG questions;
- safety/governance questions;
- no-answer/low-confidence questions.

All cases preserve advisory-only expectations and no autonomous write behavior.

## 12. Validation/test results

Passed:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py seed_production_demo --profile SMALL --dry-run
python -m pytest apps/core/tests/test_production_demo_seed.py -q
```

Focused pytest result:

```text
10 passed in 49.81s
```

SMALL apply/rerun was executed only inside Django's disposable test database.

## 13. Bugs/gaps found

Known gaps preserved for separate tasks:

1. RFQ `QUOTED` status still lacks a confirmed canonical transition.
2. Quotation `EXPIRED` still lacks an exposed canonical V1 expire command.
3. Knowledge role casing remains characterized only: current source treats `"admin"` differently from canonical `"Admin"`.

Milestone 2 implementation issues found and corrected:

1. Append-only `AuditEvent.objects.update()` correctly failed. Historical helper now uses ownership-filtered PK selection and base-manager timestamp-only update.
2. TEST quotation revision logic initially consumed all rejected quotations. TEST now preserves a rejected quotation while still covering revision/superseded behavior.
3. Order creation was initially capped by the TEST limit. SMALL now uses `self.profile.orders`.
4. Inventory transaction path initially had an extra legacy opening transaction. It was removed to keep SMALL closer to 750 target transactions.

## 14. Git status

Current status:

```text
 M figma_make_frontend/src/App.tsx
 M figma_make_frontend/src/api/phase6c.test.ts
?? PRODUCTION_LIKE_DATA_SEED_MILESTONE_1_REPORT.md
?? PRODUCTION_LIKE_DATA_SEED_MILESTONE_2_REPORT.md
?? PRODUCTION_LIKE_DATA_SEED_PLAN.md
?? PROJECT_MASTER_REPORT_FOR_CHATGPT.md
?? django_backend/apps/core/management/commands/seed_production_demo.py
?? django_backend/apps/core/production_demo_seed/
?? django_backend/apps/core/tests/test_production_demo_seed.py
```

No staging, commit, push, merge, tag, or deploy was performed.

## 15. Recommendation for FULL

Before FULL:

1. Review the seed-only historical timestamp helper.
2. Decide whether RFQ `QUOTED` and quotation `EXPIRED` need canonical commands.
3. Fix Knowledge role casing in a separate corrective task if desired.
4. Consider adding command flags for profile-specific dry-run count previews and optional knowledge-only reruns.
5. Run SMALL against the Owner-approved local/disposable database before FULL.

READY_FOR_PRODUCTION_LIKE_SEED_FULL
