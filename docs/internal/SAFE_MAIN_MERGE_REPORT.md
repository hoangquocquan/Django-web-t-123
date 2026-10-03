# SAFE MAIN MERGE REPORT

## 1. Result

**NOT MERGED**

The requested RAG/chatbot changes are verified in the current development worktree, but they cannot be safely isolated and merged into the repository's current `origin/main` without also importing a very large, unrelated platform migration.

No commit, merge, checkout of `main`, reset, clean, stash, or push was performed. The pre-existing staged, unstaged, and untracked state was preserved.

## 2. Source branch

```text
codex/demo-database-validation
HEAD: 8458ab7
Remote tracking: origin/codex/demo-database-validation
Merge base with origin/main: 5a015e8
origin/main: 5a015e8
```

There is no local `main` branch. The remote default ref is also unusual: `origin/HEAD` currently points to `origin/codex/demo-database-validation`, not `origin/main`.

Remote refs were refreshed with `git fetch --prune origin` before the merge assessment.

## 3. Scope review

### Repository topology blocker

The source branch is **262 commits ahead** of `origin/main`, while `origin/main` has no commits not already in the source branch.

```text
git rev-list --count origin/main..HEAD = 262
git rev-list --count HEAD..origin/main = 0
git diff --shortstat origin/main...HEAD
  2005 files changed, 226747 insertions(+), 11868 deletions(-)
```

`origin/main` contains only the initial migration skeleton. It does not contain:

- the current `apps.knowledge` implementation;
- the governance models/migrations required by the RAG services;
- the current canonical API/auth/permission layers;
- the production-demo seed package;
- the React application under `figma_make_frontend`;
- the Phase 5/6 authenticated frontend/session foundation.

Therefore:

- merging the source branch would import all 262 commits and more than 2,000 changed files, including many unrelated phases, reports, infrastructure changes, legacy removals, screenshots, and automation assets;
- cherry-picking only the local RAG/chatbot files onto `origin/main` would not compile or migrate because their framework, models, API, auth, frontend, and migration dependencies do not exist there;
- manufacturing a replacement platform migration inside this task would exceed the authorized RAG/chatbot scope and could not be reviewed as a clean feature merge.

### Relevant file classification

| File / group | Working status | Classification | Reason |
|---|---:|---|---|
| `django_backend/apps/knowledge/services/synthetic_rag_demo.py` | untracked | IN_SCOPE | Shared synthetic dataset ingestion/retrieval and `SyntheticRagWebDemoService`. |
| `django_backend/apps/knowledge/services/public_synthetic_rag_demo.py` | untracked | IN_SCOPE | Public-safe wrapper over the shared RAG service. |
| `django_backend/apps/knowledge/views.py` | staged + unstaged | UNCERTAIN / MIXED | Contains the required public/internal synthetic endpoints, but also hundreds of lines from other AI/pilot/public-assistant phases. Whole-file staging is unsafe. |
| `django_backend/apps/api/urls.py` | staged + unstaged | UNCERTAIN / MIXED | Required three RAG routes are mixed with unrelated public products, capability CMS, admin queries, and other API routes. |
| `django_backend/apps/knowledge/services/rag_pipeline.py` | staged + unstaged | IN_SCOPE but mixed | RAG pipeline changes are relevant; staged and unstaged generations must not be blindly combined. |
| `django_backend/apps/knowledge/services/search_service.py` | staged + unstaged | IN_SCOPE but mixed | Retrieval/governance changes are relevant; index contains an older staged generation. |
| `django_backend/apps/knowledge/models.py` | unstaged | IN_SCOPE dependency | Governance fields required by current RAG policy, but depends on migrations `0004`–`0010`. |
| `django_backend/apps/knowledge/migrations/0004_governance_access.py` through `0010_onboarding_and_confidentiality_evidence.py` | untracked | IN_SCOPE dependency | Required schema history for current governance and pilot controls. Cannot be applied to initial `main` without all intermediate platform migrations/apps. |
| `django_backend/apps/knowledge/services/access_policy.py` | untracked | IN_SCOPE | Enforces document, department, pilot, approval, and indexing policy. |
| `django_backend/apps/knowledge/services/governance.py` | untracked | IN_SCOPE | Review/approval lifecycle used by the seed compatibility fix. |
| `django_backend/apps/knowledge/services/pilot_*.py` | untracked | UNCERTAIN dependency | Required by current knowledge views/tests but broader than the chatbot merge. Indicates dependency expansion beyond the requested feature. |
| `django_backend/apps/knowledge/services/knowledge_indexer.py` | unstaged | IN_SCOPE dependency | Enforces `can_index`; needed by synthetic RAG and seed fix. |
| `django_backend/apps/knowledge/services/knowledge_service.py` | unstaged | IN_SCOPE dependency | Creates immutable versions and normalized knowledge content. |
| `django_backend/apps/knowledge/services/assistant_service.py` | unstaged | UNCERTAIN | Broader internal knowledge assistant behavior, not limited to the synthetic chatbot. |
| `django_backend/apps/knowledge/services/public_assistant_service.py` | staged + unstaged | OUT_OF_SCOPE for current endpoint | Older/general public AI service gated by `PUBLIC_AI_ENABLED`; current homepage demo uses `PublicSyntheticRagDemoService`. |
| `django_backend/apps/knowledge/management/commands/import_public_chatbot_draft.py` | staged | OUT_OF_SCOPE | Older public-assistant draft workflow, not required by `/public/ai-component-demo/`. |
| `django_backend/apps/knowledge/management/commands/prepare_public_chatbot_demo.py` | staged | OUT_OF_SCOPE | Separate general public chatbot preparation flow. |
| `django_backend/apps/knowledge/management/commands/verify_public_chatbot_demo.py` | staged | OUT_OF_SCOPE | Separate general public chatbot verification flow. |
| `django_backend/apps/knowledge/management/commands/verify_public_chatbot_draft.py` | staged | OUT_OF_SCOPE | Separate draft workflow. |
| `django_backend/apps/knowledge/management/commands/run_synthetic_rag_demo.py` | untracked | IN_SCOPE | Controlled synthetic dataset runner. |
| `django_backend/apps/knowledge/management/commands/sync_database_knowledge_candidates.py` | untracked | OUT_OF_SCOPE | Real database knowledge extraction is not required for the synthetic chatbot merge. |
| `django_backend/apps/knowledge/tests/test_synthetic_rag_demo.py` | untracked | IN_SCOPE | Synthetic corpus validation/import tests. |
| `django_backend/apps/knowledge/tests/test_synthetic_rag_web_demo.py` | untracked | IN_SCOPE | Internal RAG API/service tests. |
| `django_backend/apps/knowledge/tests/test_public_synthetic_rag_demo.py` | untracked | IN_SCOPE | Public response projection, gate, scope, and metadata-leak tests. |
| `django_backend/apps/knowledge/tests/test_governance_access.py` | untracked | IN_SCOPE dependency | Verifies approval/index/access constraints used by the seed fix. |
| Other `test_controlled_pilot_*`, `test_pilot_*`, and database adapter tests | untracked | UNCERTAIN dependency | Pass in the current platform but represent broader Phase 8 governance/pilot scope. |
| `django_backend/config/settings/base.py` | unstaged | IN_SCOPE hunk only | Safely defaults `PUBLIC_AI_ENABLED=False` and `PUBLIC_SYNTHETIC_RAG_DEMO_ENABLED=False`; file also contains unrelated settings evolution relative to `main`. |
| `django_backend/config/settings/development.py` | staged + unstaged | IN_SCOPE hunk only | Enables the localhost development demo; staged content also belongs to the older public chatbot configuration. |
| `django_backend/config/settings/public_chatbot_demo.py` | staged | OUT_OF_SCOPE | Settings module for the older/general public assistant, not the synthetic homepage endpoint. |
| `django_backend/apps/core/production_demo_seed/generators.py` | untracked | IN_SCOPE fix | Adds governed owner/department/effective-date data. |
| `django_backend/apps/core/production_demo_seed/lifecycle.py` | untracked | IN_SCOPE fix | Normalized comparison, immutable revision, owner review, independent approval, `can_index`, and indexing. |
| Remaining `production_demo_seed/` package and `seed_production_demo.py` | untracked | UNCERTAIN dependency | The fix cannot exist without the package, but most of the package is a broader production-like data feature absent from `main`. |
| `django_backend/apps/core/tests/test_production_demo_seed.py` | untracked | IN_SCOPE fix test plus broader seed suite | Contains the required regression test but also the full seed feature suite. |
| `figma_make_frontend/src/api/aiDemo.ts` | staged + unstaged | IN_SCOPE but mixed | Contains internal RAG, internal chat, and public component API clients plus older public chatbot code. |
| `figma_make_frontend/src/components/RagDemoPage.tsx` | untracked | IN_SCOPE | Existing internal technical RAG UI. |
| `figma_make_frontend/src/components/RagChatPage.tsx` | untracked | IN_SCOPE | Authenticated internal AI chat UI. |
| `figma_make_frontend/src/components/PublicComponentChatWidget.tsx` | untracked | IN_SCOPE | Homepage public synthetic chatbot. |
| `figma_make_frontend/src/App.tsx` | staged + unstaged | UNCERTAIN / MIXED | Required route/widget mount hunks are mixed with roughly 1,000 lines of unrelated admin/public UI integration. Whole-file staging is unsafe. |
| `figma_make_frontend/src/api/ragDemo.test.ts` | untracked | IN_SCOPE | Internal technical RAG client/UI regression. |
| `figma_make_frontend/src/api/ragChat.test.ts` | untracked | IN_SCOPE | Internal chat authorization/client regression. |
| `figma_make_frontend/src/api/publicComponentDemo.test.ts` | untracked | IN_SCOPE | Public endpoint no-auth/no-metadata contract. |
| `figma_make_frontend/src/api/publicChatbot.test.ts` | staged | OUT_OF_SCOPE | Older/general public chatbot API contract. |
| `figma_make_frontend/package.json` | staged + unstaged | IN_SCOPE hunk only | Test script includes new RAG tests, but staged/unstaged versions also include unrelated frontend tests. |
| `figma_make_frontend/src/hooks/`, `src/services/`, `src/types/` | untracked | OUT_OF_SCOPE | Admin table/public catalog integration unrelated to RAG chatbot. |
| `reports/rag_data_phase3/RAG_SYNTHETIC_PRODUCT_DATASET.csv` | untracked | IN_SCOPE data | Controlled 25-record source dataset used for demo preparation. |
| `reports/rag_data_phase3/*.xlsx` and phase reports | untracked | OUT_OF_SCOPE artefacts | Human report/spreadsheet artefacts are not runtime requirements. |
| `CHATGPT_RAG_CHATBOT_DEMO_REPORT.md`, `PUBLIC_RAG_CHATBOT_HOMEPAGE_REPORT.md`, `MERGE_READINESS_RAG_CHATBOT_REPORT.md` | untracked | OUT_OF_SCOPE for main | Development/handoff reports; no repository policy was found requiring them in `main`. |
| Other root reports and `reports/phase2`–`phase8c0` | untracked | OUT_OF_SCOPE | Historical planning/evidence unrelated to a minimal RAG/chatbot merge. |
| `django_backend/apps/ai_agent/**`, business/admin serializers/models/services, public product/capability files, foundation migrations, frontend admin services/hooks/types | modified/untracked | OUT_OF_SCOPE | Sales AI, admin CMS/query, public catalog, and business-domain work unrelated to the requested RAG/chatbot merge. |

### Security and code review findings

- No plaintext local E2E password, API key, or committed credential was found in the reviewed RAG/chatbot files.
- No temporary `console.log` or `console.debug` was found in the reviewed frontend RAG components/API.
- The only synthetic owner address is the non-deliverable marker `synthetic-rag-demo@localhost.invalid`.
- Public response projection strips technical metadata and allowlists synthetic source titles/codes.
- The current worktree has line-ending warnings, but no reason to touch or normalize unrelated files during this task.

## 4. Commit list

No commit was created or approved for merge.

The existing source branch commit range is not an acceptable merge unit:

```text
origin/main..codex/demo-database-validation = 262 commits
```

Those commits include the complete platform evolution from the initial migration skeleton through canonical domains, APIs, frontend phases, infrastructure, reports, and other unrelated work. They cannot be represented as a RAG/chatbot-only commit list.

## 5. Merge method

No merge method was executed.

The two allowed strategies were evaluated:

1. `git merge --no-ff codex/demo-database-validation` — rejected because it would merge 262 commits and 2,005 changed files outside scope.
2. Clean integration branch from `origin/main` plus selective cherry-pick — rejected because `origin/main` lacks the platform dependencies required to import or test the RAG/chatbot implementation independently.

The safe next repository-level action is to establish an approved platform baseline branch (likely the current feature/default branch lineage) as the new `main` through a separate migration review, or to identify a newer integration base that already contains the Phase 6 platform. Only after that baseline decision can the RAG/chatbot working-tree changes be split into clean commits and merged.

## 6. Security/governance verification

The current verified worktree has the intended boundaries:

- `PUBLIC_AI_ENABLED = False` in base settings and is not environment-overridable there.
- `PUBLIC_SYNTHETIC_RAG_DEMO_ENABLED = False` in base settings.
- Development settings explicitly enable the synthetic demo for local testing only.
- The public endpoint additionally requires `DEBUG`, the development demo gate, and a loopback client address.
- `/api/v1/public/ai-component-demo/` uses `PublicSyntheticRagDemoService` over `SyntheticRagWebDemoService` and filters to `rag_synthetic_demo_v1`.
- Public responses omit chunk IDs, document IDs, embeddings, internal citations/URIs, approval flags, and retrieval/debug metadata.
- `/api/v1/internal/rag-chat/` remains protected by bearer authentication, `knowledge:read`, and allowed internal roles.
- The production-demo seed fix uses normalized comparison, immutable `DocumentVersion`, named-owner review, independent approval, `can_index`, and normal indexing. It does not catch or bypass `PermissionDenied`.

These verified boundaries were **not transferred to `main`**, because doing so safely requires an approved base-platform migration first.

## 7. Test results

The most recent completed feature-worktree verification before this merge assessment was:

```text
Backend full suite:       379 passed, 151 skipped, 0 failed
Frontend tests:           167 passed, 0 failed
Django system check:      PASS, 0 issues
Migration drift check:    PASS, no changes detected
TypeScript typecheck:     PASS
Vite production build:    PASS
Authenticated browser:    PASS
Public browser smoke:     PASS
Admin RAG browser smoke:  PASS
Browser console:          no warnings/errors
```

No post-merge tests were run because no merge occurred. Running the RAG tests directly on `origin/main` would not be meaningful: the required applications, migrations, API/auth layers, and React project do not exist on that base.

## 8. Git cleanliness

The source worktree was already dirty before this task and remains intentionally dirty. It contains pre-existing staged, unstaged, and untracked changes from many project phases.

No unrelated file was added to `main`, because `main` was not checked out or modified. No existing staged entry was removed or restaged. `git add .`, `git add -A`, and `git commit -am` were never used.

This report itself is untracked and is not proposed for `main`.

## 9. Push status

**not pushed**

No branch or commit was pushed. `origin/main` remains at `5a015e8`.

## 10. Final status

**MAIN NOT READY**

Concrete blocker: the only available `main` is an initial migration baseline that is 262 commits and 2,005 changed files behind the current application. A RAG/chatbot-only merge cannot be built, tested, or reviewed against that base without first resolving the repository's platform-baseline/main-branch strategy.
