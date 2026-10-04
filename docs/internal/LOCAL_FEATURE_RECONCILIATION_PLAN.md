# Local Feature Reconciliation Plan

Audit date: 2026-09-27  
Mode: read-only. No source file was modified; no add, commit, push, merge, delete, reset, or bulk staging was performed.

## Comparison baseline

- Target base: `origin/main` at `c6d77e9afbbe40e33239cfd1ba0a1d7e2beae4bf`.
- Relevant refs checked: `origin/codex/demo-database-validation`, `origin/feature/ai-sales-assistant`, `origin/integration/platform-current`, and `origin/main`.
- Local feature worktree: `C:\Users\hoang\Documents\ChatGPT\WEB Ô TÔ DJANGO`, branch `codex/demo-database-validation`, HEAD `8458ab7be25a3efd1c553b10d9875fdc484c5816`.
- Status remains mixed staged/unstaged/untracked; this report itself is untracked.

## Feature-by-feature matrix

| Feature | Local-only files | Already on main | Divergent files | Migration issues | Tests | Recommended action | Suggested branch | Suggested commits |
|---|---|---|---|---|---|---|---|---|
| AIMachiningEstimate | `business_core/models.py` addition; `business_core/migrations/0003_aimachiningestimate.py` | Existing business_core migrations 0001–0005, but no AIMachiningEstimate model | `models.py` is local-newer than all checked refs | **Conflict**: local 0003 collides with remote 0003; regenerate after current head, do not rename blindly | No focused local test found | `REGENERATE_MIGRATION` then `MANUAL_REVIEW` | `feat/ai-machining-estimate` | `feat(business-core): add estimate model`; `test(business-core): cover estimate persistence` |
| Capability / public-product | capability/publication modules, API views/serializers, migrations 0006–0007, permission migrations 0011–0012, security tests | Not found at these paths on checked target refs | Local-only feature set | business_core migration must depend on remote 0005; foundation permissions must follow existing foundation head | Dedicated API/security/migration tests present | `KEEP_LOCAL` as isolated feature, after dependency graph review | `feat/public-capability-contracts` | `feat(public-catalog): add capability/public product models`; `feat(api): add publication contracts`; `test(public-catalog): add RBAC and exposure tests` |
| Knowledge / RAG | local staged/unstaged services, commands, tests, migrations 0004–0010 | Migrations 0004–0010 and core synthetic RAG files are byte-identical on `origin/main`/`origin/integration/platform-current`; several frontend RAG files also identical | Mixed files such as `knowledge/views.py`, `public_assistant_service.py`, `rag_pipeline.py`, `search_service.py` have staged and unstaged revisions | Do not recommit identical migrations; verify migration head and only retain genuinely newer content | Broad governance, pilot, adapter, synthetic, web, and public-assistant tests present | `USE_REMOTE` for identical files; `MERGE_CONTENT` for divergent files; `DROP_DUPLICATE` for exact copies | `reconcile/knowledge-rag-main` | `chore(knowledge): drop files already on main`; `feat(knowledge): reconcile newer service changes`; `test(knowledge): retain only new regressions` |
| AI Sales / CRM | modified sales assistant/view/serializer/API files, `sales_access.py`, `tests/test_sales_crm_ai.py` | Existing AI Sales baseline is on current remotes | Divergent shared API and service files; exact intent cannot be inferred from mixed staged/unstaged state | No new migration identified in this group | Existing `tests/test_sales_crm_ai.py` modified | `MANUAL_REVIEW`, then `MERGE_CONTENT` against current main | `reconcile/ai-sales-crm` | `fix(ai-sales): reconcile access and API changes`; `test(ai-sales): update contract coverage` |
| Production-demo seed | `seed_production_demo.py`, `production_demo_seed/`, `ensure_local_ai_demo_user.py`, tests | Not found on checked refs | Local-only | No schema migration directly identified; depends on existing Foundation/business models | Focused seed tests present | `KEEP_BUT_SEPARATE_COMMIT`; repository inclusion only after safety review | `feat/local-demo-seed` | `feat(demo): add TEST-only synthetic seed`; `test(demo): verify idempotency and safety` |
| Frontend RAG/public chatbot | components, hooks/services/types, API tests, App/package changes | `RagDemoPage.tsx` and several RAG frontend equivalents are byte-identical on main; other files are mixed | `App.tsx`, `aiDemo.ts`, package files and public widget files are divergent/staged+unstaged | No frontend migration; API contracts depend on backend public/capability endpoints | API and component tests present | `USE_REMOTE` for identical files; `MERGE_CONTENT` for contract changes; avoid unrelated package churn | `reconcile/frontend-rag-chatbot` | `feat(frontend): add public RAG surfaces`; `test(frontend): cover API contracts` |
| Canonical reports | 24+ handoff/audit/milestone reports across ChatGPT checkout, plus n8n reports | Some evidence exists in merged history | Content/date/provenance varies; duplicates likely | none | none | `DROP_DUPLICATE` then `REPORT_OPTIONAL` for one canonical report per milestone | `docs/reconcile-reports` | `docs: consolidate canonical handoff evidence` |

## Detailed findings

### 1. AIMachiningEstimate

Remote `origin/main` business_core migration graph ends at `0005_phase3b_master_constraints.py`; remote already uses `0003_businessmaterial_businessnumbersequence_and_more.py`. The local untracked migration also declares dependency on `0002`, so applying it as-is would fork the graph and collide on the migration number.

Safe resolution:

1. Decide whether the model belongs in the target product scope.
2. Rebase the model change onto current `origin/main` model state.
3. Run Django migration autodetection from that reconciled state so Django generates the next valid migration (likely `0006`, but confirm the current graph rather than assuming).
4. Inspect whether existing data requires backfill; the proposed model has only defaults/nullable text fields and no explicit data migration, but this must be confirmed against the intended API.
5. Add a focused model/API test and run `makemigrations --check`/migration tests before commit.

Recommendation: `REGENERATE_MIGRATION`; never manually rename the untracked file.

### 2. Capability/public-product

The local group is genuinely absent at the inspected paths on all four relevant remote refs. It introduces model/publication logic, API contracts, exact permission migrations, serializers, views, and negative security tests. Dependencies are existing business_core/foundation models and permission conventions. Keep it isolated from RAG and demo seed work.

### 3. Knowledge/RAG

`knowledge/migrations/0004_governance_access.py` and `knowledge/services/synthetic_rag_demo.py` were byte-identical to `origin/main`; the same pattern applies to the checked RAG frontend page. These should use the remote version, not be recommitted. The staged/unstaged service files require a three-way diff against `origin/main`; preserve only local additions that are demonstrably newer and tested.

### 4. AI Sales/CRM

The group modifies shared API/service code and an existing regression test. Because the worktree contains staged and unstaged versions of several files, intent is ambiguous. Reconcile from `origin/main`, review endpoint contracts and permissions, then update tests in a separate branch.

### 5. Production-demo seed

The command explicitly describes fictional `TEST/SMALL/FULL` profiles and imports safety/profile/orchestrator modules. This is promising but not sufficient proof of production isolation. Before inclusion, verify profile guards reject production settings, data is synthetic, operations are idempotent, and no superuser/wildcard permission is granted. Keep separate from runtime application changes.

### 6. Frontend

Several RAG pages already match main byte-for-byte. The remaining App/API/package changes are contract-sensitive and should be reconciled with the backend public/capability endpoints. Review `package.json` changes for unrelated dependency churn; do not commit lockfile/dependency changes unless required by the feature.

## Exact ordered execution plan

### STEP 1 — Freeze and snapshot references

Record `origin/main`, current local HEADs, and status. Do not stage or modify. Preserve the current worktrees as evidence until decisions are complete.

### STEP 2 — Resolve AIMachiningEstimate first

Create a fresh branch from current `origin/main`; port only the model; run Django migration detection; generate the next valid migration; inspect data/backfill implications; add focused tests; stop if migration graph is not linear.

### STEP 3 — Reconcile capability/public-product

Create a separate branch from the same current main. Port models, publication workflow, API serializers/views, permission migrations, and security tests as one dependency-ordered feature. Run migration graph and API tests.

### STEP 4 — Reconcile Knowledge/RAG

Start from main. Drop files proven byte-identical to main. Three-way review staged versus unstaged service changes. Keep only newer code with matching migrations/tests; run the full knowledge regression set.

### STEP 5 — Reconcile AI Sales/CRM

Diff each modified shared service/API file against main. Choose local or remote hunks deliberately; update the existing sales/CRM tests. Keep this branch independent from RAG and frontend.

### STEP 6 — Validate production-demo seed

Review safety/profile/orchestrator code and tests. Confirm synthetic-only, TEST-only, idempotent behavior and minimum permissions. Keep it separate and do not enable it by default.

### STEP 7 — Reconcile frontend

Use remote copies for identical RAG pages. Merge only required App/API/components/hooks/services/types. Verify backend endpoint contracts and package changes; avoid unrelated dependency churn.

### STEP 8 — Curate reports

Select one canonical report per milestone. Mark older duplicates as optional; do not bundle all handoff reports with runtime features.

### STEP 9 — Final pre-commit gate

Run secret scan, migration checks, Django checks, relevant tests, frontend tests, and `git diff --check` on each proposed branch. Only then seek explicit approval to commit; this task ends before any commit.

## Final recommendation

Do not bulk commit or discard the current worktrees. The correct next action is **MANUAL_REVIEW**, beginning with migration regeneration for AIMachiningEstimate, followed by isolated feature branches in the order above.
