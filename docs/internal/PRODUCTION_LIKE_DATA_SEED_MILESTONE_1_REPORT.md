# Production-Like Seed Milestone 1 Report

Date: 2026-09-18  
Scope: TEST profile implementation only. SMALL/FULL are not implemented.

## 1. Files added/modified

Added:

- `django_backend/apps/core/management/commands/seed_production_demo.py`
- `django_backend/apps/core/production_demo_seed/__init__.py`
- `django_backend/apps/core/production_demo_seed/profiles.py`
- `django_backend/apps/core/production_demo_seed/ownership.py`
- `django_backend/apps/core/production_demo_seed/safety.py`
- `django_backend/apps/core/production_demo_seed/generators.py`
- `django_backend/apps/core/production_demo_seed/lifecycle.py`
- `django_backend/apps/core/production_demo_seed/validators.py`
- `django_backend/apps/core/production_demo_seed/report.py`
- `django_backend/apps/core/production_demo_seed/ai_eval_cases.py`
- `django_backend/apps/core/tests/test_production_demo_seed.py`

Pre-existing workspace changes preserved and not modified by this milestone:

- `figma_make_frontend/src/App.tsx`
- `figma_make_frontend/src/api/phase6c.test.ts`
- `PROJECT_MASTER_REPORT_FOR_CHATGPT.md`
- `PRODUCTION_LIKE_DATA_SEED_PLAN.md`

## 2. Exact command interface

Implemented management command:

```bash
python manage.py seed_production_demo --profile TEST --dry-run
python manage.py seed_production_demo --profile TEST --apply
```

Behavior:

- `--dry-run` is safe/default behavior.
- `--apply` is mutually exclusive with `--dry-run`.
- Only `--profile TEST` is implemented in Milestone 1.
- Unsupported profiles fail clearly.

## 3. Safety gates

Apply fails closed unless:

- `PRODUCTION_DEMO_SEED_ALLOWED=true` is set.
- The database looks disposable/local.

Disposable/local detection currently allows:

- SQLite databases, including Django test `:memory:`;
- database names containing `test`, `local`, `dev`, or `demo`;
- explicit extra confirmation `PRODUCTION_DEMO_SEED_DATABASE_CONFIRMED=local-disposable`.

Dry-run performs zero writes and does not require the apply gate.

## 4. Ownership implementation

Dataset marker:

```text
production_demo_v1
```

Ownership markers:

- users: `@production-demo.invalid`
- customers: `notes` contains `dataset=production_demo_v1`
- materials: `description` contains `dataset=production_demo_v1`
- parts: `technical_requirements` contains `dataset=production_demo_v1`
- RFQs: `notes` contains `dataset=production_demo_v1`
- quotations/orders: deterministic idempotency keys beginning with `pdv1-`
- knowledge documents: metadata `dataset=production_demo_v1`
- AI eval fixtures: IDs beginning with `pdv1-ai-eval-`

Seed users use `make_password(None)` unusable passwords. No interactive password, token, or secret is hardcoded.

## 5. Actual TEST counts

Validated in focused Django test database:

| Area | Count/result |
| --- | ---: |
| Users | 6 |
| Customers | 12 |
| Materials | 12 |
| Parts | 30 |
| Warehouses | 2 planned/created by seed path |
| RFQs | 35 |
| Quotation revisions | 20 |
| Orders | 7 representative canonical orders |
| Knowledge documents | 12 |
| AI evaluation cases | 20 |

Note: TEST order target was approximately 8. The implemented seed produced 7 canonical orders because the TEST profile preserves all required quotation states, including rejected/revision, superseded, approved, sent, accepted, and declined, without raw status mutation.

## 6. Lifecycle paths used

Canonical services/domain paths used:

- RFQ create
- RFQ add line
- RFQ document upload for drawing-required representative lines
- RFQ submit
- RFQ start technical review
- RFQ request information
- RFQ complete review
- RFQ archive draft
- quotation create
- quotation submit
- quotation reject
- quotation create revision from rejected quotation
- quotation approve
- quotation send
- quotation customer accept/decline
- accepted quotation convert to order
- order progress
- order hold
- order resume
- order complete
- order cancel
- KnowledgeService document create/index

## 7. Omitted unsupported states

Omitted in TEST:

- RFQ `QUOTED`: omitted because no confirmed canonical transition was found in the inspected source. No raw update was used.
- Quotation `EXPIRED`: omitted because no exposed canonical V1 expire command was found. No raw update was used.

## 8. Idempotency result

Focused test confirms running TEST apply twice in the Django test database does not duplicate seed-owned customers, materials, parts, RFQs, quotations, orders, or knowledge documents.

Implementation uses deterministic:

- marker fields;
- generated labels;
- canonical idempotency keys;
- AI evaluation IDs;
- fixed random seed.

Partial rerun behavior is conservative: existing deterministic records are reused where possible. No unrelated records are deleted.

## 9. Knowledge/RAG result

Knowledge TEST path:

- creates 12 documents through `KnowledgeService.create_document`;
- indexes using `DevelopmentHashEmbeddingProvider`;
- does not require live Ollama;
- focused search test returns source results with deterministic fallback embeddings.

## 10. AI evaluation fixture result

Implemented code fixture:

- `load_ai_eval_cases("TEST")`
- 20 deterministic cases
- themes include RAG policy, live pipeline, mixed sales, safety, and no-answer cases
- cases require advisory-only behavior, human approval, and no DB write expectation

No new database model was added for AI evaluation cases.

## 11. Tests/checks

Passed:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py seed_production_demo --profile TEST --dry-run
python -m pytest apps/core/tests/test_production_demo_seed.py -q
```

Focused pytest result:

```text
9 passed
```

TEST apply/rerun validation was performed only inside Django's test database.

## 12. Source gaps/bugs discovered

Source gaps characterized, not fixed in this milestone:

1. RFQ `QUOTED` status exists in models, but no confirmed canonical transition was identified.
2. Quotation `EXPIRED` status exists in models, but no exposed canonical V1 expire command was identified.
3. Knowledge admin role casing behavior is inconsistent with current role naming: `KnowledgeService.list_documents` treats role name `"admin"` as full-access admin, while canonical roles elsewhere use `"Admin"`. Focused test characterizes this behavior; no unrelated production fix was bundled.
4. Historical timestamps remain unresolved for SMALL/FULL because append-only and auto-managed protections were not weakened.

## 13. Git status

Current status after implementation:

```text
 M figma_make_frontend/src/App.tsx
 M figma_make_frontend/src/api/phase6c.test.ts
?? PRODUCTION_LIKE_DATA_SEED_PLAN.md
?? PROJECT_MASTER_REPORT_FOR_CHATGPT.md
?? django_backend/apps/core/management/commands/seed_production_demo.py
?? django_backend/apps/core/production_demo_seed/
?? django_backend/apps/core/tests/test_production_demo_seed.py
```

No files were staged, committed, pushed, merged, tagged, or deployed.

## 14. Recommendation for SMALL/FULL

Recommended next Owner review before scale-up:

1. Decide whether 7 TEST orders is acceptable or whether to adjust TEST distribution to force exactly 8 by reducing current-state quotation diversity.
2. Decide how to implement historical timestamps without weakening append-only protections.
3. Decide whether to add/fix canonical transitions for RFQ `QUOTED` and quotation `EXPIRED`.
4. Decide whether Knowledge admin role casing should be fixed as a separate production bug.
5. After those decisions, scale SMALL first, then FULL.

READY_FOR_PRODUCTION_LIKE_SEED_SCALE_UP
