# REPOSITORY BASELINE AUDIT REPORT

Audit date: 2026-09-23 (Asia/Tokyo)

## 1. Executive summary

### Current repository state

The repository has two different meanings of "mainline":

- `origin/main` is the documented production branch, but it is still the one-commit migration skeleton at `5a015e8` from 2026-07-25.
- `origin/codex/demo-database-validation` is the server-reported default branch, contains the complete current platform lineage, and is 262 commits ahead of `origin/main`.

The active working platform is newer still: the worktree on `codex/demo-database-validation` contains substantial staged, unstaged, and untracked Phase 8/RAG/admin/public changes on top of committed HEAD `8458ab7`.

### De facto baseline

`codex/demo-database-validation` is acting as the **de facto development mainline: YES for development, NO for a clean release baseline**.

Evidence:

- the hosting provider reports it as the remote HEAD/default branch;
- all current Django, canonical API/auth, React, migration, deployment, and test foundations are on its lineage;
- the other active branch, `codex/ai-assistant-update`, is a direct one-commit child of it;
- current verified RAG/chatbot work was developed against it;
- however, the active worktree is heavily dirty and the branch name/policy do not match the repository's documented release model.

### Recommended strategy

**CREATE CLEAN INTEGRATION BASELINE FIRST**

Create and validate a future `integration/platform-current` branch from committed cut point `8458ab7`, then explicitly review whether to add `af309f1` and the categorized dirty-worktree features. Only after this integration branch is clean, reproducible, CI-green, and approved should `main` be fast-forwarded or merged through a protected PR. Do not promote the current dirty worktree directly.

## 2. Branch topology

Remote refs were refreshed before the audit. Only three remote branches exist: `main`, `codex/demo-database-validation`, and `codex/ai-assistant-update`. There is no remote `develop`, `development`, `integration`, `staging`, `release/*`, `platform/*`, or `feature/*` branch.

| Branch | HEAD | Date | Relative to current committed HEAD | Purpose inferred from evidence | Status |
|---|---|---|---:|---|---|
| `origin/main` | `5a015e8` | 2026-07-25 | 0 ahead / 262 behind | Initial migration skeleton; documented production branch | Obsolete as an application baseline |
| `backup/phase6-pre-remote-merge` | `eca707a` | 2026-09-17 | 0 ahead / 3 behind | Phase 6 release-candidate checkpoint before legacy-backend removal/B2B UI merge | Useful rollback/cut reference; not remote |
| `origin/codex/demo-database-validation` | `8458ab7` | 2026-09-18 | current committed HEAD | Complete Phase 6 platform plus merged legacy cleanup and B2B UI work | Remote default; best committed platform cut point |
| `origin/codex/ai-assistant-update` | `af309f1` | 2026-09-18 | 1 ahead / 0 behind current | Canonical AI assistant workspace extension | Candidate follow-on commit; separate dirty worktree |

Commit counts:

```text
origin/main                              1 commit
backup/phase6-pre-remote-merge         260 commits
origin/codex/demo-database-validation  263 commits
origin/codex/ai-assistant-update       264 commits
```

The merge base of all current-lineage candidates with `codex/demo-database-validation` is on the expected ancestry. `origin/main` is an ancestor, not a diverged line.

### Worktrees

| Worktree | Branch | HEAD | State |
|---|---|---|---|
| `WEB Ô TÔ DJANGO` | `codex/demo-database-validation` | `8458ab7` | Dirty: staged, unstaged, and many untracked files |
| `ai-assistant-update` | `codex/ai-assistant-update` | `af309f1` | Dirty: three modified React AI workspace components |

No detached worktree was found.

## 3. Remote/default branch state

```text
origin/main = 5a015e8
origin/HEAD -> origin/codex/demo-database-validation
```

Both the local symbolic ref and a live `git remote show origin` query agree:

```text
HEAD branch: codex/demo-database-validation
```

Therefore this is **not merely a stale local `origin/HEAD` cache**. It is the current server-reported default branch configuration. Whether a human intentionally selected it as a permanent default or it was temporarily changed during migration cannot be proven from Git history alone; hosting-provider audit history was not available.

Tracking relationships:

- local `codex/demo-database-validation` tracks the same remote branch and is up to date at the committed level;
- local `codex/ai-assistant-update` points to its matching remote branch and is checked out in the second worktree;
- no local `main` exists;
- no branch tracks `origin/main`.

This topology explains why normal development continued on the codex branch while `main` remained at the initialization commit. The exact administrative event that changed the default branch is **NOT VERIFIED**.

## 4. Platform capability matrix

Legend: **Yes** = present in committed tree; **Partial** = foundation exists but current hardened feature is only in the dirty worktree; **No** = absent.

| Capability | `origin/main` | Phase 6 backup `eca707a` | Current committed `8458ab7` | AI branch `af309f1` | Current dirty worktree |
|---|---:|---:|---:|---:|---:|
| Current Django application | No | Yes | Yes | Yes | Yes |
| Foundation/auth models | No | Yes | Yes | Yes | Yes |
| Canonical API/auth/permissions | No | Yes | Yes | Yes | Yes |
| Knowledge/RAG foundation | No | Yes | Yes | Yes | Yes |
| Hardened knowledge access policy | No | No | No | No | Yes |
| Governance migrations `0004`–`0010` | No | No | No | No | Yes |
| React `figma_make_frontend` | No | Yes | Yes | Yes | Yes |
| In-memory authenticated frontend session | No | Yes | Yes | Yes | Yes |
| Canonical AI assistant workspaces | No | No | No | Yes | Mixed/overlapping local work |
| Production-demo seed package | No | No | No | No | Yes, untracked |
| Synthetic RAG service/dataset scope | No | No | No | No | Yes, untracked |
| Internal RAG/chat pages | No | No | No | No | Yes, untracked |
| Public synthetic homepage widget | No | No | No | No | Yes, untracked |
| Public website foundation | Legacy only | Yes | Yes | Yes | Yes |
| Phase 6 CI/full-stack scripts | No | Yes | Yes | Yes | Yes |
| Current RAG regression results | No | No | No | No | Yes: 379 backend pass; 167 frontend pass |

The matrix shows that `8458ab7` is the last committed platform foundation before the current RAG/chatbot work. `af309f1` is a valid candidate extension, but it is not part of the current branch and overlaps conceptually and textually with dirty AI/frontend files.

## 5. Commit history analysis

`origin/main..origin/codex/demo-database-validation` contains 262 commits between 2026-07-25 and 2026-09-18.

An exclusive, commit-subject heuristic produced this summary:

| Category | Count | Examples |
|---|---:|---|
| Documentation/reports/evidence | 73 | production evidence, handovers, roadmaps, review reports |
| Tests/validation | 15 | staging UAT, database validation, release checks |
| Knowledge/AI/RAG/review engine | 44 | knowledge assistant, Ollama, vector retrieval, AI governance |
| Frontend/UI | 9 | canonical frontend foundation, quotation/order UI, B2B design |
| Auth/API | 22 | canonical read/command APIs, authentication hardening, legacy API work |
| Database/business domain | 40 | Django ownership, RFQ, quotation, order, CRM and business models |
| Infrastructure/platform/operations | 23 | Docker, PostgreSQL, Redis, monitoring, backup, deployment readiness |
| Cleanup/archive/legacy reduction | 24 | legacy shutdown, archival checkpoints, backend removal |
| Other/checkpoints/performance/data | 12 | performance baseline, demo dataset and checkpoints |
| **Total** | **262** | |

These counts are a repeatable subject-based classification, not a claim that every cross-cutting commit belongs to only one semantic concern. File-history review confirms the central conclusion: the 262 commits represent the entire platform migration, not one feature branch that can be safely merged as “RAG only.”

Important history landmarks:

- `5a015e8` — initial migration workflow (`origin/main`).
- Django ownership waves and current app foundations follow on the same lineage.
- AI/RAG foundation, production hardening, API decommission, domain/API/frontend phases, and Phase 6 release work accumulate on that lineage.
- `eca707a` — Phase 6 production-demo release candidate.
- `13af7f6` — removes the legacy `/backend` and adds the Django home API.
- `2ebcb30` — B2B website/UI upgrade.
- `8458ab7` — merges those remote changes into the Phase 6 line.
- `af309f1` — one subsequent canonical AI assistant commit on its own branch.

## 6. Platform baseline candidate

### Primary cut point

```text
PLATFORM_BASELINE_CANDIDATE = 8458ab7be25a3efd1c553b10d9875fdc484c5816
Date: 2026-09-18 00:00:16 +0900
Message: Merge remote-tracking branch 'origin/codex/demo-database-validation' into codex/demo-database-validation
```

Why this is the best cut point:

- it contains the complete Phase 6 backend, canonical domain/API/auth foundation, React frontend, migrations, CI, and full-stack scripts;
- it includes the intentional legacy `/backend` removal and latest B2B/public website merge;
- it is the remote default branch HEAD and the direct parent of the only newer remote feature branch;
- the hardened Phase 8 governance, production-demo seed, synthetic RAG, internal chat, and public synthetic widget are not committed at this point, so it is a clean conceptual boundary before the current dirty feature set.

Tests at exactly `8458ab7` were **not rerun during this read-only audit**. Commit history and Phase 6 evidence describe a release-candidate baseline, but that evidence must be revalidated in a clean worktree before promotion.

### Secondary checkpoint

`eca707a` is a valuable rollback reference because its message explicitly identifies a Phase 6 release candidate. It is three commits behind `8458ab7`; the subsequent diff includes 99 files, primarily legacy backend deletion and website/UI replacement. It should be preserved, but using it as the new baseline would reintroduce architecture already superseded by `8458ab7`.

### AI extension candidate

`af309f1` adds 22 files/changes and 1,438 insertions for canonical AI assistant workspaces. It is a direct child of `8458ab7`, but should be reviewed and tested as a separate optional commit because:

- it includes public AI behavior separate from the new synthetic public RAG widget;
- its second worktree has three additional unstaged component modifications;
- the current main worktree has overlapping AI/API/App changes.

## 7. CI/deployment impact

### CI triggers

`.github/workflows/ci.yml` runs on every push and pull request and covers Django checks/full tests, React tests/build, PostgreSQL migration smoke, and Phase 6 static/Compose checks.

Two other workflows are branch-filtered:

- `aws-lab-ci.yml`: push to `main`, `develop`, or `feature/**`; all pull requests.
- `test_pipeline.yml`: push to `main`, `develop`, `feature/**`, or `migration/**`; all pull requests.

Implication: direct pushes to `codex/*` receive the generic CI workflow, but do **not** receive the two branch-filtered workflows unless exercised through a pull request. A baseline promotion must ensure all required workflows are run explicitly before changing the default branch.

### Deployment references

No active deployment script was found that checks out or deploys specifically from `codex/demo-database-validation`. No executable deployment rule was found that automatically deploys `main` solely by branch name in the reviewed files.

Repository policy in `docs/cicd/BRANCHING_STRATEGY.md` says:

- `main` is production-stable;
- `develop` is the reviewed integration branch;
- releases/hotfixes are the path to `main`;
- direct pushes to `main`/`develop` should be blocked and required checks/reviews enabled.

The actual refs do not implement that document: `develop` and release branches do not exist, and the server default is a `codex/*` branch.

### Branch protection

**NOT VERIFIED.** GitHub CLI is installed, but the configured GitHub token is invalid. Required checks, protection rules, PR requirements, force-push restrictions, and hosting audit history could not be read. They must be verified by an authenticated repository administrator before promotion.

## 8. Risk analysis

| Risk | Severity | Evidence and consequence |
|---|---|---|
| `main` history gap | HIGH | `main` is 262 commits behind; a naive feature merge appears as a complete platform replacement. |
| Dirty primary worktree | HIGH | Staged, unstaged, and untracked changes from multiple phases overlap in core files such as `App.tsx`, `urls.py`, `views.py`, settings, and RAG services. |
| Dirty secondary worktree | MEDIUM | Three AI workspace components are modified beyond `af309f1`. |
| Dependency coupling | HIGH | Current RAG/chatbot depends on governance, migrations, auth, API, React, and seed changes absent from `main`. |
| CI coverage mismatch | HIGH | `codex/*` pushes skip two branch-filtered workflows; protection status is unknown. |
| Production/default-branch confusion | HIGH | Remote default is the development branch while policy calls `main` production-stable. |
| Release traceability | HIGH | No Git tags exist; release intent is represented only by commits and reports. |
| History preservation | LOW if fast-forwarded; HIGH if rewritten | `origin/main` is an ancestor, so a future no-rewrite promotion can preserve all history. Force-push/rebase would create unnecessary risk. |
| Secrets/local artefacts | MEDIUM | Large untracked report/data sets require classification; no promotion should stage them wholesale. |
| Developer workflow | MEDIUM | Introducing `main-v2` without clear default-branch and CI updates would create competing mainlines. |

## 9. Options considered

### Option A — Promote current lineage directly to `main`

Path: `codex/demo-database-validation` → reviewed `main`.

Advantages:

- preserves the entire 262-commit ancestry because `origin/main` is already an ancestor;
- aligns `main` with the platform developers actually use;
- removes the misleading gap between the documented and actual default branch.

Risks:

- current worktree is not a commit and cannot be promoted safely;
- committed HEAD has not been revalidated in isolation during this audit;
- branch protection and required checks are unknown;
- `af309f1` and dirty RAG/admin work need explicit disposition first.

Prerequisites: freeze changes, create backup refs/tags, test a clean checkout of `8458ab7`, verify CI/protection, and obtain architecture/security/operations approval.

Rollback: preserve legacy main at `5a015e8`; revert the promotion commit or temporarily restore the default branch without rewriting history.

### Option B — Create `integration/platform-current` first

Path: `8458ab7` → `integration/platform-current` → reviewed feature commits → release candidate → `main`.

Advantages:

- matches the documented concept of a reviewed integration branch;
- separates baseline validation from the dirty RAG/chatbot, admin/public catalog, and AI assistant work;
- allows `af309f1` to be accepted or rejected independently;
- gives CI and reviewers a stable PR target before changing production semantics.

Risks:

- introduces another temporary branch and requires clear ownership;
- branch filters must be updated or checks triggered via PR/manual dispatch;
- requires disciplined splitting of the current dirty worktree.

Rollback: delete the future integration branch only after review if rejected; existing refs remain untouched. No force push is required.

### Option C — Create `main-v2` / `platform-v2`

Path: current lineage → `main-v2`, while legacy `main` remains.

Advantages:

- avoids immediately changing the semantic meaning of `main`;
- makes the platform generation boundary explicit.

Risks:

- creates two “main” branches and long-term developer/automation confusion;
- every CI, deployment, documentation, clone default, protection rule, and release process must understand both;
- legacy `main` is not an actively maintained production application, so retaining it as primary offers little operational value.

Rollback is simple, but the migration and communication burden is higher than Option B.

### Option D — Keep legacy `main` and migrate 262 commits in phases

Advantages: each domain could theoretically receive a focused review.

Risks: the historical commits are tightly cumulative; later Django, API, React, and RAG work depends on earlier platform phases. Replaying them into a parallel history would duplicate testing, increase conflict risk, and obscure the already coherent ancestry.

This option is not recommended unless governance requires a commit-by-commit re-approval of the entire platform.

## 10. Recommended strategy

**CREATE CLEAN INTEGRATION BASELINE FIRST** (Option B), then promote that reviewed lineage to `main` without rewriting history.

This is safer than direct promotion because it establishes one immutable, testable boundary between:

1. the committed Phase 6 platform (`8458ab7`);
2. the optional canonical AI extension (`af309f1`);
3. the current uncommitted governance/RAG/chatbot work;
4. unrelated admin/public catalog/report artefacts.

The review set should include:

- full diff `origin/main..8458ab7`, with emphasis on migrations, legacy deletion, production settings, CI and deployment;
- the single `af309f1` diff separately;
- the dirty worktree categorized into logical feature commits;
- both worktree statuses;
- all active CI workflows and hosting protection settings;
- production/staging ownership and rollback runbooks.

Avoid `main-v2` unless organizational policy explicitly requires permanent coexistence. The existing ancestry permits a normal promotion of `main`; a second permanent mainline is unnecessary.

## 11. Safe execution plan

No step below was executed during this audit.

1. **Freeze both active worktrees.** Stop new changes on `codex/demo-database-validation` and `codex/ai-assistant-update`; record exact status and owners.
2. **Authenticate repository administration.** Verify GitHub default-branch history, branch protection, required checks, PR rules, and force-push restrictions.
3. **Create immutable recovery refs.** Plan annotated tags such as `legacy-main-before-platform-promotion` at `5a015e8`, `phase6-platform-cut` at `eca707a`, and `platform-baseline-candidate` at `8458ab7`. Use names approved by project policy.
4. **Create `integration/platform-current` from `8458ab7`.** Do this in a new clean worktree; do not copy the dirty index.
5. **Validate the committed cut point.** Run Django check, migration drift and clean PostgreSQL migration, full backend tests, frontend typecheck/tests/build, Compose validation, and browser smoke.
6. **Review `af309f1` independently.** Cherry-pick or merge it only after resolving its three local component modifications and verifying it does not conflict with the planned synthetic public RAG design.
7. **Inventory the primary dirty worktree.** Export staged and unstaged patch manifests; assign each hunk to admin/public catalog, governance, seed, internal RAG, public chatbot, tests, reports, or local artefacts.
8. **Create clean feature commits.** Use explicit paths/selective hunks only; never `git add .`. Prefer isolated worktrees/branches per logical feature.
9. **Keep generated and narrative artefacts out of the baseline by default.** Include only policy-approved docs and the minimal runtime synthetic CSV; archive the remainder outside the production branch if retention is required.
10. **Integrate features one by one.** Apply approved commits to `integration/platform-current`, running focused tests after each and full regression at defined gates.
11. **Run all CI workflows.** Ensure the generic CI, AWS lab, test pipeline, security, migration, frontend, and browser checks run despite current branch filters.
12. **Create a release candidate.** Obtain development, architecture, security, operations, and human production approvals described by repository policy.
13. **Promote through a protected PR.** Since old `main` is an ancestor, use a normal fast-forward-compatible or reviewed merge strategy; do not rebase or force-push the platform history.
14. **Change the remote default branch only after promotion.** Point default HEAD to `main` after checks and access rules are confirmed, not before.
15. **Post-promotion validation.** Re-clone using the default branch, run full tests/build/migrations/browser smoke, verify deployment references, and confirm rollback refs are reachable.
16. **Retire temporary branches later.** Only after an agreed retention period and explicit approval; do not delete the old codex/default branches during the promotion itself.

### Dirty worktree disposition

- **Commit selectively:** runtime code, migrations, tests, controlled dataset CSV, settings gates, and approved frontend components belonging to one reviewed feature.
- **Separate branches/commits:** public catalog/admin CMS, governance, production-demo seed, internal RAG, public synthetic chatbot, and canonical AI assistant.
- **Archive or exclude:** root handoff reports, phase report collections, screenshots, `.xlsx` derivatives, generated patches/results, local evidence, and personal documents unless repository policy explicitly requires them.
- **Ignore locally generated content:** databases, logs, caches, build output, coverage, `node_modules`, `__pycache__`, `.env`, credentials, editor state, and local runtime artefacts.
- **Possible future `.gitignore` review:** generated report/evidence directories and spreadsheet derivatives, but only after confirming which existing tracked evidence is intentionally retained.

### Clean baseline criteria

The integration branch is eligible for promotion only when:

```text
[ ] clean worktree and index
[ ] complete backend and frontend committed
[ ] migration graph consistent from an empty database
[ ] full backend suite passes
[ ] frontend tests and typecheck pass
[ ] production build passes
[ ] browser public/internal smoke passes
[ ] no secrets, local accounts, databases, logs, caches or temp artefacts
[ ] CI workflow matrix runs on the candidate
[ ] branch protection and required checks verified
[ ] deployment branch references understood
[ ] release/rollback refs created and tested
[ ] architecture, security, operations and production approvals recorded
```

## 12. Rollback plan

No rollback refs were created in this audit; the following is the recommended future plan.

1. Preserve `5a015e8` with an annotated `legacy-main-before-platform-promotion` tag and optionally a read-only `legacy/main-2026-07-25` branch.
2. Preserve `eca707a` as the Phase 6 pre-merge checkpoint.
3. Tag the fully tested integration commit as `platform-baseline-candidate` before promotion.
4. Record old/new default-branch settings and protection rules outside the repository.
5. Promote without force push so every old commit and parent relation remains reachable.
6. If application validation fails after promotion, stop deployment and create a normal revert commit for the promotion or redeploy the last known-good image/commit.
7. If repository navigation itself is the issue, temporarily switch the hosting default branch back to the preserved legacy or integration branch; do not rewrite `main`.
8. Keep the previous default branch and tags for an agreed retention window before any deletion is considered.
9. Verify rollback by clean clone, database restore/migration rehearsal, backend/frontend tests, and browser smoke.

## 13. RAG/chatbot impact

The new governance/RAG/chatbot implementation is **not part of committed platform baseline `8458ab7`**. It currently exists as mixed staged, unstaged, and untracked work.

After baseline resolution it should:

1. remain on the current worktree until an immutable patch manifest exists;
2. be split into logical commits: governance/schema, seed compatibility, shared synthetic RAG, internal endpoints/UI, public safe wrapper/widget, and tests;
3. exclude older/general public assistant code unless separately approved;
4. merge into `integration/platform-current` only after the baseline and optional `af309f1` decision;
5. rerun the previously successful 379-test backend suite, 167-test frontend suite, builds, authorization checks, and real browser smoke on the integration branch;
6. keep production public AI disabled and the synthetic public demo development/loopback gated.

Treating the dirty RAG work as already part of the platform baseline would destroy the useful cut point and make rollback/review much harder.

## 14. Actions NOT performed

This audit performed read-only Git and repository inspection plus creation of this report only.

Confirmed not performed:

```text
no merge
no rebase
no reset
no force push
no normal push
no branch deletion
no branch creation
no checkout/switch
no stash
no clean
no tag creation
no default-branch change
no branch-protection change
no staging/index modification
```

## 15. Final recommendation

**CREATE CLEAN INTEGRATION BASELINE FIRST**

Use `8458ab7` as the initial platform baseline candidate, preserve `5a015e8` and `eca707a` as rollback references, review `af309f1` separately, split the dirty worktrees into explicit feature commits, and promote the resulting verified integration lineage to `main` through protected review. After promotion, restore `main` as the remote default branch.

This path preserves all commit ancestry and release evidence, avoids a second permanent mainline, contains the dirty-worktree risk, and gives CI/security/operations a stable object to approve.
