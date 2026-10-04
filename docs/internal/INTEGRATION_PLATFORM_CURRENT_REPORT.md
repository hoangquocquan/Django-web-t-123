# Integration Platform Current Report

## 1. Branch created

- Branch: `integration/platform-current`
- Base: `8458ab7be25a3efd1c553b10d9875fdc484c5816`
- Integration worktree: `C:\Users\hoang\Documents\Codex\mecprecision-platform-current`
- Source dirty worktree preserved: yes
- `origin/main`, remote HEAD, default branch, and protection rules changed: no
- Force push, rebase, merge from main, reset-hard, and clean operations used: no

## 2. Commit structure

| Commit | Message | Purpose | Files |
|---|---|---|---:|
| `40dd163` | `feat(knowledge): add knowledge governance foundation` | Knowledge lifecycle, approval, access policy, indexing gates, pilot governance, migrations, and protected governance APIs | 26 |
| `98f318d` | `feat(rag): add synthetic component RAG pipeline` | Isolated `rag_synthetic_demo_v1` ingestion/retrieval pipeline, internal technical-demo API, and RAG demo UI | 7 |
| `727f5d4` | `feat(ai): add internal RAG chatbot` | Authenticated, permission-checked `/api/v1/internal/rag-chat/` endpoint and admin chat page | 5 |
| `1743074` | `feat(ai): add public component assistant` | Anonymous public-safe serializers/services, public endpoints, public chatbot page, and homepage widget | 12 |
| `9011162` | `test(ai): add chatbot and rag verification tests` | Backend/frontend verification suites and migration dependency isolation from excluded Capability CMS work | 18 |

Total integration delta: 54 files, 6,932 insertions, 104 deletions.

## 3. File classification and exclusions

| Source file/group | Category | Action |
|---|---|---|
| `django_backend/apps/knowledge/models.py`, migrations, access/governance/pilot services | Knowledge governance | Committed |
| `synthetic_rag_demo.py`, demo command, RAG page/API | Synthetic RAG | Committed |
| Internal RAG chat view, route, client, admin page | Internal chatbot | Committed |
| Public assistant services/commands, public routes, page, homepage widget | Public AI | Committed |
| Knowledge/RAG/chatbot backend and frontend tests | Tests | Committed in the test commit |
| `business_core` public-product/capability changes and production-demo seed | Unrelated platform work | Excluded |
| `reports/**` and root handoff/audit reports | Reports/local evidence | Excluded |
| Screenshots and `*.png` | Generated evidence | Excluded |
| `*.xlsx` and local import artifacts | Local/generated data | Excluded |
| Local SQLite databases, `.env`, logs, coverage, `node_modules`, `__pycache__`, build artifacts | Local/generated artifacts | Excluded |
| Customer, RFQ, order, employee, and other real/private datasets | Sensitive/non-synthetic data | Excluded |

The controlled synthetic corpus identifier remains `rag_synthetic_demo_v1`. No customer, RFQ, order, or employee dataset was added.

## 4. Dependency graph

```text
Platform baseline (8458ab7)
  ↓
Knowledge governance foundation
  ↓
Synthetic RAG (rag_synthetic_demo_v1)
  ↓
Internal authenticated RAG chatbot
  ↓
Public-safe component assistant
  ↓
Verification tests
```

## 5. Test results

### Backend

- `python manage.py check`: **PASS** — 0 issues.
- Scoped knowledge/RAG/chatbot suite: **PASS** — 76 passed.
- Full repository `pytest -q`: **FAIL** — 511 passed, 38 failed, 5 errors.

### Frontend

- `npm run typecheck`: **PASS**.
- `npm test`: **PASS** — 150 passed.
- `npm run build`: **PASS**.

## 6. Remaining issues

1. The full backend suite is not green. Several legacy tests expect immediate indexing of newly created knowledge documents, while the new governance flow intentionally requires draft → review → approval → indexing.
2. Five full-suite errors require an ignored local legacy SQLite database that is absent from the clean `8458ab7` tree.
3. Additional legacy/backend baseline tests expect untracked legacy `backend/` compatibility files or seeded data not present in the clean base.
4. The migration dependency chain was corrected to use the clean base's latest tracked foundation migration (`0010_phase4c_role_activity_and_quotation_archive`) instead of excluded Capability CMS migration `0012`.
5. Reviewers must decide whether to update the legacy AI tests to the governed lifecycle or add an explicit compatibility layer. Until that decision and a green full backend suite, this branch should not be merged.

## 7. Merge readiness

**NOT READY**

The requested commit split, isolation, internal/public security boundaries, scoped AI tests, frontend tests, and frontend build are complete. Merge readiness remains blocked by the failing full backend suite described above.

## Safety verification

- The original dirty worktree remains on `codex/demo-database-validation`.
- `PRE_INTEGRATION_SNAPSHOT.md` and this report are intentionally not committed.
- No report, screenshot, XLSX, local database, environment file, log, coverage output, dependency directory, cache, or generated build artifact was included.
- The integration worktree is clean after tests.

