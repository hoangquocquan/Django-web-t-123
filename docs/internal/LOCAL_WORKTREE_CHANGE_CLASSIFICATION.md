# Local Worktree Change Classification

Audit date: 2026-09-27  
Scope: read-only classification of uncommitted and untracked changes in the three requested worktrees. No add, commit, push, merge, reset, checkout, clean, delete, or overwrite was performed.

## Rechecked state

| Worktree | Branch | HEAD | Status |
|---|---|---|---|
| `C:\Users\hoang\Documents\Django-web-t-123` | `codex/demo-database-validation` | `2ebcb30cbe28749c5a610a42e3a4bc899faf7b47` | 4 tracked edits, 2 untracked files (including this audit's prior report) |
| `C:\Users\hoang\Documents\ChatGPT\WEB Ô TÔ DJANGO` | `codex/demo-database-validation` | `8458ab7be25a3efd1c553b10d9875fdc484c5816` | 120 changes: 7 unstaged tracked, 10 staged additions, 84 untracked |
| `C:\Users\hoang\Documents\Codex\n8n-line-uat-demo` | `feature/n8n-line-uat-demo` | `1702ee75e8c507904467fa89b205f350d4bb7974` | 2 untracked reports |

Permission warnings for `.pytest_cache` were observed; caches were not touched.

## File/group inventory and classification

| Worktree | File/Group | Type | Feature | Status | Recommendation | Risk |
|---|---|---|---|---|---|---|
| Primary | `business_core/models.py` + `migrations/0003_aimachiningestimate.py` | backend source + migration | AI machining estimate | local model change and untracked migration | **UNKNOWN_REVIEW_REQUIRED**; likely keep only after migration renumber/rebase | **HIGH**: local migration is numbered `0003`, while remote already has `business_core/0003_businessmaterial_businessnumbersequence_and_more.py`; direct migration fork/conflict |
| Primary | three `docs/reviews/business_simulation_automation/*.json` | fixture/data or review evidence | n8n automation review | timestamp-only edits | **STALE_OR_DUPLICATE** unless timestamp evidence is intentionally needed | low runtime risk; no functional change |
| Primary | `REPOSITORY_GITHUB_SYNC_AUDIT.md` | docs/report | repository audit | untracked report | **REPORT_OPTIONAL** | none |
| ChatGPT | `apps/knowledge/migrations/0004–0010` and related governance/pilot services/tests/commands | backend source, migrations, tests, management commands | RAG / Knowledge governance | mixed staged, modified, untracked | **KEEP_BUT_SEPARATE_COMMIT** by migration chain and feature phase | high integration risk; many files form a coupled feature. Exact equivalents for several are already on `origin/main`/`origin/integration/platform-current`, so deduplicate before commit |
| ChatGPT | `apps/knowledge/services/public_assistant_service.py`, `rag_pipeline.py`, `search_service.py`, `views.py`, public assistant tests/commands | backend source/tests/commands | public RAG chatbot | staged + unstaged + untracked | **KEEP_BUT_SEPARATE_COMMIT** after diffing against `origin/main` | large mixed diff; duplicate/newer local versions possible |
| ChatGPT | `apps/business_core/capabilities.py`, `publication.py`, `migrations/0006–0007`, API serializers/views/tests | backend source, migrations, tests | capability/public-product | untracked | **KEEP_AND_COMMIT** as an isolated feature only after review | not present on inspected remote refs; requires dependency/order review |
| ChatGPT | `apps/core/management/commands/seed_production_demo.py`, `production_demo_seed/`, `ensure_local_ai_demo_user.py`, tests | management command, fixture/data, tests | synthetic/demo database | untracked | **KEEP_BUT_SEPARATE_COMMIT**; keep explicitly TEST/local-only | risk of accidental production-like data or broad permissions; verify guards and no real data |
| ChatGPT | `apps/ai_agent/services/sales_access.py`, admin query/API contract changes, `tests/test_sales_crm_ai.py` | backend source/tests | AI Sales / CRM | mixed staged/unstaged | **KEEP_BUT_SEPARATE_COMMIT** | touches existing shared APIs; regression review required |
| ChatGPT | `figma_make_frontend/src/components/*Rag*`, `PublicComponentChatWidget`, hooks/services/types, API tests, `App.tsx`, package files | frontend source/tests/config | RAG/public chatbot UI | mixed staged/unstaged/untracked | **KEEP_BUT_SEPARATE_COMMIT** | large UI/API coupling; do not commit without backend contract verification |
| ChatGPT | `BAO_CAO_*`, `CHATGPT_*`, `PHASE*`, `*_REPORT.md`, `reports/`, handoff/audit docs | docs/report | project evidence | untracked | **REPORT_OPTIONAL**; commit only selected canonical reports | duplication and stale evidence risk |
| n8n | `N8N_LINE_UAT_MERGE_READINESS.md`, `N8N_LINE_UAT_POST_MERGE_REPORT.md` | docs/report | LINE UAT | untracked | **REPORT_OPTIONAL** | no runtime impact; may duplicate merged evidence |

## KEEP_AND_COMMIT

- Capability/public-product source, migrations, and tests, but only as a coherent isolated change after dependency review.
- Any RAG/knowledge files proven to be the newer intended version and not already present on `origin/main`; split by schema, service, tests, and docs.
- Production-demo seed helpers only if their TEST/local-only guards and synthetic-data boundaries are verified.

## KEEP_BUT_SEPARATE_COMMIT

- Knowledge governance/RAG migrations and services.
- AI Sales/CRM API changes.
- Production-like demo seed and local demo-user tooling.
- Frontend RAG/public-chatbot additions.

## REPORT_OPTIONAL

- Primary `REPOSITORY_GITHUB_SYNC_AUDIT.md`.
- n8n merge-readiness/post-merge reports.
- ChatGPT handoff, milestone, merge-readiness, audit, and project reports. Select one canonical report per milestone; do not bulk-commit all 24 report files.

## DISCARD_GENERATED

- No requested changed file was proven to be disposable generated output. Normal ignored `__pycache__`/`.pytest_cache` entries were observed but were not part of the tracked/untracked inventory and were not modified.

## SENSITIVE_DO_NOT_COMMIT

No confirmed credential value, bearer token, private key, or production customer identifier was found in the reviewed change inventory. Several files contain configuration names, password/secret terminology, or documentation examples; these require a final secret scanner before any commit. Do not commit local `.env`/runtime files if discovered later.

## STALE_OR_DUPLICATE

- Primary automation JSON files: only `created_at` changed.
- Reports/handoff documents with overlapping names and milestones: consolidate before commit.
- RAG/knowledge files that already exist on `origin/main` or `origin/integration/platform-current`: compare content and retain only the intended newer version.

## UNKNOWN_REVIEW_REQUIRED

- Primary `AIMachiningEstimate` model/migration: migration number conflict is unresolved.
- Mixed staged/unstaged versions of `apps/api/urls.py`, `knowledge/views.py`, `public_assistant_service.py`, `rag_pipeline.py`, `search_service.py`, frontend `App.tsx`, and package files: staged and unstaged content may represent different feature revisions.
- `seed_production_demo.py` and its fixture package: verify synthetic-only behavior, idempotency, and permission scope.
- Any report claiming production readiness: evidence date and branch must be checked before publication.

## Migration conflicts

**YES — high priority.** The primary untracked `django_backend/apps/business_core/migrations/0003_aimachiningestimate.py` depends on `0002_seed_business_core_from_legacy`, but remote already contains a different `business_core/0003_businessmaterial_businessnumbersequence_and_more.py`. It cannot be committed as-is; rebase/renumber and regenerate migration after reconciling model state. The ChatGPT `knowledge` migration chain 0004–0010 appears coherent and is already present on `origin/main`, but must still be checked against the target branch before reuse.

## Secret findings

Pattern scans found only names/examples such as `password`, `token`, `LINE_UAT_`, or API terminology in code/tests/docs; no secret value is reported here. Action: run a repository secret scanner on the final selected commit set, and keep runtime credentials outside Git.

## Remote comparison

- `origin/main` contains the knowledge migration chain 0004–0010 and several RAG/frontend equivalents.
- Capability/public-product modules, production-demo seed files, and several API modules were not found at the inspected paths on `origin/main`, `origin/codex/demo-database-validation`, `origin/integration/platform-current`, or `origin/feature/ai-sales-assistant`.
- The n8n branch HEAD matches its remote branch; its two reports are local-only untracked files.
- This classification does not imply that a local file is safe to discard merely because an equivalent path exists remotely; compare content and provenance first.

## Suggested commit plan (proposal only)

1. `fix(business-core): reconcile AI machining estimate migration` — after resolving the `0003` conflict.
2. `feat(knowledge): add governed RAG schema and services` — only files not already on target remote.
3. `test(knowledge): add governance and synthetic RAG regression coverage`.
4. `feat(public-catalog): add capability and public-product publication contracts`.
5. `feat(demo): add isolated synthetic production-like seed tooling`.
6. `feat(frontend): add RAG/public chatbot UI and contract tests`.
7. `docs: add one canonical handoff/audit report per milestone`.

## Suggested branch strategy

Use separate short-lived branches per feature group, branch from the intended current `origin/main`, and cherry-pick only reviewed files. Do not bulk-add the ChatGPT worktree. Keep reports separate from runtime feature commits. Resolve migrations before any commit.

## Final verdict

IMPORTANT LOCAL SOURCE WORK EXISTS: YES  
SAFE TO DISCARD ALL LOCAL CHANGES: NO  
SAFE TO BULK COMMIT: NO  
NUMBER OF KEEP_AND_COMMIT FILES: group-level, not safely countable until duplicate comparison (at least capability/public-product source/tests)  
NUMBER OF KEEP_BUT_SEPARATE_COMMIT FILES: group-level, includes knowledge/RAG, AI Sales/CRM, demo seed, and frontend changes  
NUMBER OF OPTIONAL REPORT FILES: 27 observed report/audit/handoff files across the requested worktrees  
NUMBER OF GENERATED/SAFE-DISCARD FILES: 0 changed files confirmed; ignored caches were not included  
NUMBER OF SENSITIVE FILES: 0 confirmed secret-bearing files; scanner follow-up required  
NUMBER OF UNKNOWN FILES: multiple, led by the migration conflict and mixed staged/unstaged revisions  
MIGRATION CONFLICTS FOUND: YES  
NEXT ACTION: MANUAL DECISION REQUIRED
