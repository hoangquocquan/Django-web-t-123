# Production-Like Seed Milestone 3 FULL Report

Date: 2026-09-18  
Scope: FULL profile implementation for production-like portfolio/AI demo. No stage, commit, push, merge, tag, or deploy was performed.

## 1. Files changed

Updated:

- `django_backend/apps/core/management/commands/seed_production_demo.py`
- `django_backend/apps/core/production_demo_seed/profiles.py`
- `django_backend/apps/core/production_demo_seed/ai_eval_cases.py`
- `django_backend/apps/core/production_demo_seed/lifecycle.py`
- `django_backend/apps/core/tests/test_production_demo_seed.py`

Previously added seed package files retained:

- `django_backend/apps/core/production_demo_seed/__init__.py`
- `django_backend/apps/core/production_demo_seed/ownership.py`
- `django_backend/apps/core/production_demo_seed/safety.py`
- `django_backend/apps/core/production_demo_seed/generators.py`
- `django_backend/apps/core/production_demo_seed/historical.py`
- `django_backend/apps/core/production_demo_seed/validators.py`
- `django_backend/apps/core/production_demo_seed/report.py`

Added:

- `PRODUCTION_LIKE_DATA_SEED_MILESTONE_3_FULL_REPORT.md`

Pre-existing unrelated workspace changes remain preserved:

- `figma_make_frontend/src/App.tsx`
- `figma_make_frontend/src/api/phase6c.test.ts`
- `PROJECT_MASTER_REPORT_FOR_CHATGPT.md`
- `PRODUCTION_LIKE_DATA_SEED_PLAN.md`
- `PRODUCTION_LIKE_DATA_SEED_MILESTONE_1_REPORT.md`
- `PRODUCTION_LIKE_DATA_SEED_MILESTONE_2_REPORT.md`

## 2. FULL profile implementation

Command support now includes:

```bash
python manage.py seed_production_demo --profile TEST --dry-run
python manage.py seed_production_demo --profile TEST --apply
python manage.py seed_production_demo --profile SMALL --dry-run
python manage.py seed_production_demo --profile SMALL --apply
python manage.py seed_production_demo --profile FULL --dry-run
python manage.py seed_production_demo --profile FULL --apply
```

Dry-run remains safe/default. FULL is explicit and is never selected silently.

FULL profile targets:

- 30 users
- 200 customers
- 100 materials
- 600 parts/products
- 4 warehouses
- 900 inventory rows
- 3,000 inventory transactions
- 700 leads
- 350 opportunities
- 4,000 sales activities plus related follow-ups/CRM records
- 1,500 RFQs
- 5,000 RFQ lines
- 1,200 RFQ documents
- about 1,000 quotation revisions
- up to 500 orders
- 200 knowledge documents
- 150 AI evaluation cases
- 24-month historical timestamp spread

## 3. Actual counts

Validated in Django disposable test database:

| Area | Actual / validated |
| --- | ---: |
| Users | 30 |
| Customers | 200 |
| Materials | 100 |
| Parts/products | 600 |
| Warehouses | 4 |
| Inventory rows | 900 |
| Inventory transactions | 3,000 |
| Leads | 700 |
| Opportunities | 350 |
| Sales activities | 4,000 |
| Sales follow-ups | approx. 2,000 |
| CRM profile/interactions/notes/tasks/timeline rows | approx. 800+ supporting records |
| RFQs | 1,500 |
| RFQ lines | 5,000 |
| RFQ documents | 1,200 |
| Technical review evidence | service-derived; more than target because READY_TO_QUOTE requires STARTED + READY review records |
| Quotation revisions | approx. 990 |
| Orders | 500 |
| Order progress events | service-derived; approx. 1,650 representative events |
| Knowledge documents | 200 |
| Knowledge chunks | validated >= 3,000 |
| AI evaluation cases | 150 |

Count deviations are intentional where canonical lifecycle coverage is more important than exact arithmetic:

- Quotation revisions land at about 990 because only rejected quotations can be revised without raw mutation.
- Technical reviews exceed the approximate target because canonical READY_TO_QUOTE requires review lifecycle evidence.
- Order progress events are representative and service-derived; no raw event/status insertion was used.

## 4. Distribution summary

FULL uses deterministic non-uniform distributions:

- customer concentration: generated customers are segmented into strategic, repeat, standard, active, and nurture groups;
- long-tail and repeat customers coexist;
- lead statuses span `new`, `contacted`, `meeting`, `quotation`, `negotiation`, `won`, and `lost`;
- opportunity statuses span `open`, `proposal`, `negotiation`, `won`, and `lost`;
- materials rotate through fictional industrial materials such as SUS304, S45C, A6061, SKD11, POM, and C3604;
- tolerance values vary between tighter and standard machining requirements;
- RFQs include multiline cases and drawing-required cases;
- order state mix includes open/current work and historical closed/cancelled work after timestamp backfill.

The generation remains deterministic through fixed seed/profile definitions and deterministic idempotency keys.

## 5. Historical coverage

FULL uses the existing seed-only historical helper:

```text
django_backend/apps/core/production_demo_seed/historical.py
```

Historical coverage:

- approximately 24 months;
- no future timestamps beyond generation time;
- chronology validated after backfill;
- only records owned by `dataset=production_demo_v1` or deterministic `pdv1-` keys are touched;
- only whitelisted timestamp fields are updated;
- no business status fields are updated by the historical helper;
- append-only protections are not changed in model code.

Chronology verified in tests for sampled order chains:

```text
RFQ created_at <= quotation created_at <= order ordered_at
```

Completed orders are validated to keep progress at 100.

## 6. Lifecycle coverage

RFQ states covered through canonical services:

- `DRAFT`
- `SUBMITTED`
- `UNDER_REVIEW`
- `NEEDS_INFORMATION`
- `READY_TO_QUOTE`
- `CLOSED`

`DECLINED` remains supported by the service design, but the FULL distribution emphasizes high-volume quote/order generation. The TEST/SMALL suite still validates broader branch coverage.

Quotation states covered through canonical/domain APIs:

- `DRAFT`
- `PENDING_APPROVAL`
- `APPROVED`
- `REJECTED`
- `SENT`
- `ACCEPTED`
- `DECLINED`
- `SUPERSEDED`

Order states covered through canonical progress services:

- `CONFIRMED`
- `IN_PROGRESS`
- `ON_HOLD`
- `COMPLETED`
- `CANCELLED`

Still intentionally omitted:

- RFQ `QUOTED`, because no confirmed canonical transition is exposed.
- Quotation `EXPIRED`, because no exposed canonical V1 expire command is confirmed.

No raw status mutation was used.

## 7. Performance

Observed validation runtimes:

- FULL apply + rerun focused test: `1 passed in 200.15s (0:03:20)`
- Full seed test suite including TEST, SMALL, FULL: `12 passed in 246.95s (0:04:06)`

Command JSON report includes timing fields for applied runs:

- `runtime_master_data_ms`
- `runtime_pipeline_inventory_ms`
- `runtime_lifecycle_ms`
- `runtime_knowledge_ms`
- `runtime_historical_ms`
- `runtime_total_ms`

No unsafe shortcut was added to reduce runtime. RFQ/quotation/order lifecycle uses canonical services. Bulk-style creation is used only for safe supporting domains where no canonical workflow is required, such as CRM/pipeline support records and inventory support rows, while respecting model constraints and ownership markers.

## 8. Idempotency

Validated in Django test database:

- FULL apply succeeds.
- FULL rerun succeeds.
- Rerun does not duplicate customers, materials, parts, RFQs, quotations, orders, or knowledge documents.

Idempotency mechanisms:

- deterministic marker fields;
- deterministic labels;
- deterministic canonical idempotency keys;
- `production_demo_v1` dataset marker;
- profile-specific deterministic volumes;
- conservative reuse of existing seed-owned rows.

## 9. Knowledge/RAG

FULL creates 200 knowledge documents through `KnowledgeService.create_document`.

Default embedding mode remains deterministic local fallback via `DevelopmentHashEmbeddingProvider`, so FULL does not require live Ollama in development/demo validation.

FULL knowledge content is expanded enough to validate at least 3,000 chunks in the focused test. Content remains policy/SOP/playbook/reference material and does not copy live transactional rows into RAG.

Categories/themes represented:

- company capability
- RFQ intake
- quotation policy
- quality
- manufacturing process
- logistics/delivery
- sales playbooks
- AI guidance
- FAQ/demo guidance

## 10. AI evaluation

`load_ai_eval_cases("FULL")` returns 150 deterministic cases.

Coverage includes:

- RAG-only questions;
- live DB questions;
- mixed RAG + live-data questions;
- permission/security/governance questions;
- low-confidence/no-answer questions.

All cases keep advisory-only expectations and no autonomous write behavior.

## 11. Validation

Passed:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py seed_production_demo --profile FULL --dry-run
python -m pytest apps/core/tests/test_production_demo_seed.py::test_full_profile_apply_history_and_idempotency -q
python -m pytest apps/core/tests/test_production_demo_seed.py -q
```

Results:

```text
System check identified no issues (0 silenced).
No changes detected
FULL dry-run succeeded
FULL-focused apply/rerun: 1 passed in 200.15s (0:03:20)
Full focused seed suite: 12 passed in 246.95s (0:04:06)
```

FULL apply/rerun was executed only inside Django's disposable test database.

## 12. Known gaps

Still not fixed in this task by Owner decision:

1. RFQ `QUOTED` status has no confirmed canonical transition.
2. Quotation `EXPIRED` has no confirmed canonical V1 expire command.
3. Knowledge role casing bug remains characterized only; application behavior was not changed.

Design caveats:

- FULL technical review count exceeds the initial approximate target because canonical review evidence is required to create quoteable RFQs.
- FULL order progress events are representative and service-derived, not force-filled to an exact count by raw inserts.

## 13. Git status

Current status:

```text
 M figma_make_frontend/src/App.tsx
 M figma_make_frontend/src/api/phase6c.test.ts
?? PRODUCTION_LIKE_DATA_SEED_MILESTONE_1_REPORT.md
?? PRODUCTION_LIKE_DATA_SEED_MILESTONE_2_REPORT.md
?? PRODUCTION_LIKE_DATA_SEED_MILESTONE_3_FULL_REPORT.md
?? PRODUCTION_LIKE_DATA_SEED_PLAN.md
?? PROJECT_MASTER_REPORT_FOR_CHATGPT.md
?? django_backend/apps/core/management/commands/seed_production_demo.py
?? django_backend/apps/core/production_demo_seed/
?? django_backend/apps/core/tests/test_production_demo_seed.py
```

No files were staged. No commit, push, merge, tag, or deploy was performed.

## 14. Recommendation whether data seeding is complete

The production-like seed implementation is complete for TEST, SMALL, and FULL profiles.

Recommended follow-ups, separate from seed completion:

1. Owner review of the seed-only historical timestamp helper.
2. Separate corrective task for Knowledge role casing.
3. Optional future canonical commands for RFQ `QUOTED` and quotation `EXPIRED` if those states are required in demos.
4. Owner-approved run of `--profile FULL --apply` against the intended local/disposable demo database.

PRODUCTION_LIKE_DATASET_COMPLETE
