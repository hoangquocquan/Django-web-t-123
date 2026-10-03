# Production-Like FULL Local Apply Verification Report

Date: 2026-09-19  
Project root: `C:\Users\hoang\Documents\ChatGPT\WEB O TO DJANGO`  
Scope: Apply and verify `python manage.py seed_production_demo --profile FULL --apply` against the owner-approved local demo database only.

## 1. Target DB identity, sanitized

- Django settings module: `config.settings.development`
- Database engine: `django.db.backends.sqlite3`
- Database name/path: `C:\Users\hoang\Documents\ChatGPT\WEB O TO DJANGO\django_backend\db.sqlite3`
- Host/port: not applicable
- `.env` override: absent
- Database file: existed before apply, ignored by git, project-local
- Safety conclusion before apply: local disposable SQLite demo database

No credentials, passwords, or secrets were printed.

## 2. Preflight result

- Branch: `codex/demo-database-validation`
- HEAD: `8458ab7be25a3efd1c553b10d9875fdc484c5816`
- Staged files before apply: none
- Dirty worktree before apply was preserved:
  - `figma_make_frontend/src/App.tsx`
  - `figma_make_frontend/src/api/phase6c.test.ts`
  - production-like seed/report files already present as untracked files
- `python manage.py check`: passed
- `python manage.py makemigrations --check --dry-run`: passed, no changes detected
- `python manage.py migrate --check`: passed

## 3. Baseline counts

Read-only baseline before FULL apply:

| Area | Total before | production_demo_v1 before |
| --- | ---: | ---: |
| FoundationUser | 3 | 0 |
| BusinessCustomer | 1 | 0 |
| BusinessMaterial | 1 | 0 |
| BusinessProduct | 1 | 0 |
| SalesRfq | 0 | 0 |
| SalesQuotation | 0 | 0 |
| TransactionOrder | 0 | 0 |
| KnowledgeDocument | 0 | 0 |

Additional baseline:

- Phase 6B users: 3
- Phase 6B customer/material/part records: not present before apply
- older `demo_data.py` records detectable by known markers: 0

## 4. FULL dry-run result

Command:

```powershell
python manage.py seed_production_demo --profile FULL --dry-run
```

Result:

- Exit code: 0
- Profile resolved to `FULL`
- Planned targets displayed:
  - 30 users
  - 200 customers
  - 100 materials
  - 600 parts
  - 4 warehouses
  - 900 inventory items
  - 3,000 inventory transactions
  - 700 leads
  - 350 opportunities
  - 4,000 CRM/sales activities
  - 1,500 RFQs
  - 1,000 planned quotation revisions
  - 500 planned orders
  - 200 knowledge documents
  - 150 AI eval cases
- SQLite SHA-256 before and after dry-run was unchanged.
- Baseline counts after dry-run were unchanged.

## 5. FULL apply result

Process-local gates used only for the apply process:

```powershell
PRODUCTION_DEMO_SEED_ALLOWED=true
PRODUCTION_DEMO_SEED_DATABASE_CONFIRMED=local-disposable
```

First apply:

- Exit code: 0
- Wall runtime: 178,673 ms
- `runtime_master_data_ms`: 3,057
- `runtime_pipeline_inventory_ms`: 6,347
- `runtime_lifecycle_ms`: 147,314
- `runtime_knowledge_ms`: 7,109
- `runtime_historical_ms`: 13,320
- `runtime_total_ms`: 177,357

Created counts reported by command:

- users: 30
- customers: 200
- materials: 100
- parts: 600
- warehouses: 4
- inventory items: 900
- inventory transactions: 3,000
- leads: 700
- opportunities: 350
- sales activities: 4,000
- sales follow-ups: 2,000
- RFQs: 1,500
- RFQ lines: 5,000
- RFQ documents: 1,585
- quotations: 990
- orders: 450
- order progress events historically touched: 1,935
- knowledge documents: 200
- knowledge chunks/embeddings historically touched: 7,266

Notable command/report inconsistency:

- `ai_eval_cases`: 150
- `actual_ai_eval_cases`: 20
- Direct code check `len(load_ai_eval_cases("FULL"))`: 150

## 6. Actual production_demo_v1 counts

Actual marker-owned counts after apply and rerun:

| Area | Count |
| --- | ---: |
| users | 30 |
| customers | 200 |
| materials | 100 |
| parts/products | 600 |
| warehouses | 4 |
| inventory items | 900 |
| inventory transactions | 3,000 |
| leads | 700 |
| opportunities | 350 |
| sales activities | 4,000 |
| follow-ups | 2,000 |
| RFQs | 1,500 |
| RFQ lines | 5,000 |
| RFQ documents | 1,585 |
| technical reviews | 2,979 |
| quotations | 990 |
| orders | 450 |
| progress events | 1,935 |
| knowledge documents | 200 |
| knowledge chunks | 7,266 |
| knowledge embeddings | 7,266 |
| FULL AI eval cases from code | 150 |

Orders are below the stated FULL target of 500. This appears related to canonical conversion capacity from accepted quotations, not duplicate growth.

## 7. Ownership isolation

Post-apply isolation checks:

- Phase 6B users still present: 3
- Phase 6B customer/material/part present after apply: 1 each
- older `demo_data.py` records remained 0
- unrelated non-seed counts remained bounded to the pre-existing local demo rows:
  - users: 3
  - customers: 1
  - materials: 1
  - parts: 1
  - warehouses: 1
- production-demo ownership markers were present on seed-owned records.
- No cross-ownership deletion was detected.

## 8. Lifecycle validation

RFQ status distribution:

- `CLOSED`: 453
- `DRAFT`: 3
- `NEEDS_INFORMATION`: 3
- `READY_TO_QUOTE`: 1,035
- `SUBMITTED`: 3
- `UNDER_REVIEW`: 3

Quotation workflow distribution:

- `ACCEPTED`: 450
- `APPROVED`: 90
- `DECLINED`: 90
- `DRAFT`: 90
- `PENDING_APPROVAL`: 90
- `SENT`: 90
- `SUPERSEDED`: 90

Order workflow distribution:

- `CANCELLED`: 135
- `COMPLETED`: 90
- `CONFIRMED`: 45
- `IN_PROGRESS`: 135
- `ON_HOLD`: 45

Integrity checks found 0 for:

- RFQs without customer
- RFQ lines crossing into unowned parts/materials
- quotations without owned RFQ
- orders without source quotation
- orders without source RFQ
- orders sourced from non-accepted quotation
- orders without accepted customer decision
- completed orders with progress other than 100
- completed orders without completion timestamp
- on-hold orders without reason
- cancelled orders without reason
- progress events without owned order

Intentionally omitted states remain omitted:

- RFQ `QUOTED`
- Quotation `EXPIRED`

## 9. Chronology validation

Passing chronology checks:

- RFQ future timestamps: 0
- order future timestamps: 0
- technical review before RFQ creation: 0
- quotation before RFQ creation: 0
- customer decision before quotation creation: 0
- order before quotation creation: 0
- order before sent quotation: 0
- progress before order: 0
- completion before order: 0

Blocking chronology finding:

- Seed-owned quotations with `created_at` beyond verification time: 2

This violates the requested "no future timestamps beyond seed execution time" check.

## 10. Second-run idempotency

Second apply:

- Exit code: 0
- Wall runtime: 23,571 ms
- `runtime_total_ms`: 22,216

Rerun behavior:

- customers reused: 200
- materials reused: 100
- parts reused: 600
- warehouses reused: 4
- inventory items reused: 900
- leads reused: 700
- opportunities reused: 350
- sales activities reused: 4,000
- follow-ups reused: 2,000
- RFQs reused: 1,500
- quotations reused: 900 base rows
- orders reused: 450
- knowledge documents reused: 200

Stable post-rerun counts:

- customers: 200
- materials: 100
- parts: 600
- RFQs: 1,500
- quotations: 990
- orders: 450
- knowledge documents: 200

No significant duplicate growth was detected.

## 11. Knowledge/RAG validation

Knowledge rows:

- documents: 200
- chunks: 7,266
- embeddings: 7,266
- stored embedding provider: `development-hash-fallback`
- stored model: `local-hash-embedding`

Active runtime configuration:

- `KNOWLEDGE_EMBEDDING_PROVIDER`: `ollama`
- runtime provider class: `OllamaEmbeddingProvider`
- runtime dimensions: 768

Blocking RAG findings:

1. Active runtime provider does not match stored seed embeddings.
2. Required searches returned 0 results at the current configured relevance threshold, even when using the deterministic development hash provider.

Required search result counts at normal threshold:

- `CNC first article inspection`: 0
- `SUS304 quotation requirements`: 0
- `RFQ drawing requirement`: 0
- `quotation approval policy`: 0
- `order delivery procedure`: 0

Read-only threshold characterization with temporary `KNOWLEDGE_MIN_RELEVANCE_SCORE=0.0` did return owned sources, with top scores below 0.5:

- `CNC first article inspection`: 0.4019
- `SUS304 quotation requirements`: 0.3558
- `RFQ drawing requirement`: 0.3354
- `quotation approval policy`: 0.4990
- `order delivery procedure`: 0.4349

Therefore the knowledge records and embeddings exist, but current RAG/search behavior is not demo-ready.

## 12. AI/Sales validation

Read-only tool checks returned live seeded data:

- customer summary: populated customer, CRM segment, interactions, tasks, opportunities
- lead summary: populated lead, status, owner, opportunities, follow-ups
- sales pipeline summary: 700 leads, 210 open opportunities, non-empty open pipeline value
- inventory summary: 900 items, non-empty quantity totals

AI sales assistant checks were run with in-memory deterministic fallback configuration only:

- lead analysis: non-empty, advisory, `human_approval_required=true`, `autonomous_action=false`
- customer summary: non-empty, advisory, `human_approval_required=true`, `autonomous_action=false`
- email draft: draft only, not sent, `human_approval_required=true`, `autonomous_action=false`
- weekly recommendation: non-empty, advisory, `human_approval_required=true`, `autonomous_action=false`

Database hash before and after these AI read checks was unchanged.

## 13. API/UI smoke

Docker/Phase 6 runtime was not started because the task required avoiding disruption to unrelated Docker resources and preserving the existing stack.

Local read/serializer smoke was performed instead:

- customer list populated: true
- RFQ list populated: true
- quotation serializer returned expected API-shaped keys
- order serializer returned expected API-shaped keys
- sales lead serializer returned a seeded lead
- sales opportunity serializer returned a seeded opportunity
- knowledge document sample returned `metadata.dataset=production_demo_v1`

Open/current rows available for UI filters:

- `READY_TO_QUOTE` RFQs: 1,035
- open leads: 500
- open opportunities: 210
- open orders (`CONFIRMED`, `IN_PROGRESS`, `ON_HOLD`): 225

## 14. Security/data hygiene

Checks:

- seed email values checked: 1,130
- non-`.invalid` seed emails: 0
- secret-like source pattern scan in seed package: no matches
- generated database/dump inventory: only ignored local `django_backend\db.sqlite3`
- tracked database/dump files: none

No real personal emails, credentials, auth tokens, production customer export, or tracked dump files were detected in the seed artifacts checked.

## 15. Tests

Final regression:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python -m pytest apps/core/tests/test_production_demo_seed.py -q
```

Results:

- `System check identified no issues (0 silenced).`
- `No changes detected`
- `12 passed in 281.65s (0:04:41)`

Focused AI/knowledge behavior was verified through read-only shell checks because no dedicated focused AI/knowledge pytest file was present in the inspected app tree.

## 16. Git status

No staging, commit, push, merge, tag, deploy, reset, restore, clean, or stash was performed.

Final status includes pre-existing dirty/untracked work plus this report:

```text
 M figma_make_frontend/src/App.tsx
 M figma_make_frontend/src/api/phase6c.test.ts
?? PRODUCTION_LIKE_DATA_SEED_MILESTONE_1_REPORT.md
?? PRODUCTION_LIKE_DATA_SEED_MILESTONE_2_REPORT.md
?? PRODUCTION_LIKE_DATA_SEED_MILESTONE_3_FULL_REPORT.md
?? PRODUCTION_LIKE_DATA_SEED_PLAN.md
?? PROJECT_MASTER_REPORT_FOR_CHATGPT.md
?? PRODUCTION_LIKE_FULL_LOCAL_APPLY_VERIFICATION_REPORT.md
?? django_backend/apps/core/management/commands/seed_production_demo.py
?? django_backend/apps/core/production_demo_seed/
?? django_backend/apps/core/tests/test_production_demo_seed.py
```

`django_backend\db.sqlite3` is ignored and was not tracked.

## 17. Known gaps

Known intentional gaps preserved:

- RFQ `QUOTED` omitted because no confirmed canonical transition is exposed.
- Quotation `EXPIRED` omitted because no confirmed canonical V1 transition is exposed.
- Knowledge role casing bug was not fixed.

Role casing characterization:

- production-demo seeded users use title-case roles: `Admin`, `Manager`, `Sales`
- a lowercase `admin` role also exists
- `KnowledgeService.list_documents()` checks exact role name `admin`, so title-case Admin does not take the explicit admin branch
- current internal-document behavior still allows the inspected seeded users to see 200 documents

New verification gaps found:

- actual canonical orders are 450, not 500
- 2 seed-owned quotations have future `created_at` relative to verification time
- active RAG runtime configuration does not match stored seed embeddings
- required RAG searches are empty at the active relevance threshold
- command report says `actual_ai_eval_cases=20` while FULL fixture/code count is 150

## 18. Demo readiness

The FULL dataset was applied to the owner-approved local disposable SQLite demo database and is broadly populated, isolated, idempotent, and useful for business/API/AI read-only demonstrations.

However, the verification criteria were stricter than "data exists." The local demo DB is not fully ready for interview/demo use until the blocking findings are resolved or explicitly accepted:

- fix/confirm the two future quotation timestamps;
- align active RAG provider/threshold with seeded embeddings or reindex for the active provider;
- explain or correct the 450 actual orders versus 500 target;
- correct the command's `actual_ai_eval_cases` reporting if it is stale/test-profile based.

FINAL VERDICT: BLOCKED_LOCAL_PRODUCTION_LIKE_DEMO_DATA_APPLY
