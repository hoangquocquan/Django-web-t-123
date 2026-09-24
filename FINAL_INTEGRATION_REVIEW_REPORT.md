# Final Integration Review Report

## 1. Final status

**READY FOR PROMOTION REVIEW**

`integration/platform-current` is safe to enter a protected promotion review for `main`. This is not an authorization to merge. Promotion remains conditional on all required pull-request checks passing and repository branch-protection rules being confirmed before merge.

Review date: 2026-09-24 (Asia/Tokyo)

## 2. Branch state

| Field | Value |
|---|---|
| Branch | `integration/platform-current` |
| Reviewed code HEAD | `a2feb5c635db3d5a045db08dd8f4bbbcee4e6a39` |
| Integration base | `8458ab7` |
| Legacy `origin/main` | `5a015e8` |
| Relationship | `origin/main` is an ancestor; the integration lineage is fast-forward compatible |
| Worktree at review start | Clean |
| Worktree after code review/fix | Clean before creation of this report; this report is the final documentation-only change |

The reviewed product-code range is `8458ab7..a2feb5c`. No history was rewritten.

## 3. Commit inventory

| SHA | Message | Purpose | Files | Dependency |
|---|---|---|---:|---|
| `40dd163` | `feat(knowledge): add knowledge governance foundation` | Adds governed knowledge lifecycle, access policy, migrations, services, and supporting UI/API work. | 26 | Platform baseline `8458ab7` |
| `98f318d` | `feat(rag): add synthetic component RAG pipeline` | Adds the isolated synthetic component corpus and RAG retrieval pipeline. | 7 | Governance foundation |
| `727f5d4` | `feat(ai): add internal RAG chatbot` | Adds authenticated internal RAG chat API and frontend. | 5 | Synthetic RAG pipeline and access controls |
| `1743074` | `feat(ai): add public component assistant` | Adds separately gated public component assistant and widget. | 12 | Synthetic RAG pipeline; public-safe projection |
| `9011162` | `test(ai): add chatbot and rag verification tests` | Adds internal/public chatbot, RAG, security, and frontend verification. | 18 | Internal and public assistant implementations |
| `eef1d13` | `fix(tests): align legacy knowledge tests with governed lifecycle` | Updates legacy tests to respect governed state transitions. | 11 | Governance implementation and new test suite |
| `a54cd91` | `fix(tests): remove local database dependency from backend suite` | Makes tests independent of a developer-local database. | 7 | Existing backend suite |
| `76d0a39` | `fix(tests): make backend seed fixtures deterministic` | Stabilizes seed fixtures and repeatability. | 3 | Database-independent test setup |
| `bb3a9ff` | `fix(tests): align legacy assertions with Django cutover` | Aligns older assertions with the current Django platform behavior. | 4 | Django cutover compatibility |
| `e0ba4fe` | `fix(api): route private knowledge downloads correctly` | Places the private download route correctly and prevents generic transition-route shadowing. | 2 | Knowledge API routing |
| `f094c19` | `fix(tests): update runtime doubles and dependency audit` | Updates test doubles and dependency assertions. | 2 | Compatibility test matrix |
| `a642741` | `docs(integration): record backend compatibility verification` | Records backend failure classification and compatibility evidence. | 2 | Completed compatibility fixes |
| `a2feb5c` | `chore(integration): normalize trailing blank lines` | Removes only redundant trailing blank lines found by `git diff --check`. | 51 | Full-diff hygiene review |

The sequence is coherent: platform baseline → knowledge governance → synthetic RAG → internal chatbot → public chatbot → tests → compatibility fixes → integration evidence/hygiene.

## 4. Scope audit

### Included

- Knowledge governance models, migrations, services, policies, commands, and tests.
- Controlled synthetic RAG dataset identifier `rag_synthetic_demo_v1` and its retrieval pipeline.
- Authenticated internal RAG chatbot and admin frontend.
- Separately gated public component assistant and homepage widget.
- Regression, security, route-ordering, backend compatibility, and frontend tests.
- Integration evidence and the final trailing-whitespace hygiene commit.

### Excluded and confirmed absent from the integration diff

- Screenshots, spreadsheets, local SQLite databases, `.env` files, `node_modules`, coverage output, `__pycache__`, personal files, temporary credentials, and binary artifacts.
- The excluded Capability CMS migrations (`business_core/0006_public_product_projection.py` and `business_core/0007_capability.py`) are not present and are not migration dependencies.
- No customer, RFQ, order, employee, or private-knowledge dataset was added to the public RAG corpus.

### Unexpected findings

- `git diff --check` initially identified redundant blank lines at EOF in 51 files. They were removed mechanically in `a2feb5c`; `git diff --ignore-blank-lines` confirmed there was no logic change. The full verification matrix was then rerun successfully.
- The two integration reports are intentional review evidence, not accidental artifacts.
- No debug logging, real secrets/API keys, hard-coded production credentials, test-only production bypass, commented-out production implementation, or stale “AI Car Assistant” naming was found.

## 5. Migration/database review

- `showmigrations --plan`: complete migration graph loaded successfully.
- Migration loader conflict detection: `{}` (no conflicting leaves).
- `makemigrations --check --dry-run --settings=config.settings.test`: `No changes detected`.
- `migrate --noinput` on a newly created isolated SQLite database: all migrations applied successfully.
- `migrate --check`: passed.
- Clean bootstrap assertions passed: required `admin`, `editor`, and `viewer` roles existed; wildcard permission existed; WSGI application imported successfully.
- Bootstrap evidence: `BOOTSTRAP_OK conflicts={} roles=3 wildcard_permission=1 wsgi=imported`.
- The temporary database was removed; no developer-local database was used.
- A local PostgreSQL smoke run was not possible because neither a local PostgreSQL service nor a running Docker daemon was available. PostgreSQL 16 migration verification remains a required CI check.

Result: no missing migration, no conflicting leaf, no migration drift, no dependency on the excluded Capability CMS migrations, and a clean install path exists.

## 6. Security/governance review

### Internal authorization

- `/api/v1/internal/rag-chat/` requires authentication, `knowledge:read`, and an allowed role (`admin`, `manager`, `sales`, or `editor`).
- Anonymous requests and an unauthorized `viewer` are denied by the tested access policy.

### Public boundary and metadata isolation

- `/api/v1/public/ai-component-demo/` is separate from the internal endpoint and does not send or require an admin bearer token.
- Public retrieval requires `source_type=SYNTHETIC_PRODUCT`, `metadata.dataset_id=rag_synthetic_demo_v1`, `synthetic=true`, `production_eligible=false`, `authoritative=false`, internal visibility, public/pilot approval flags false, and active/indexed state.
- Business context attachment is disabled for this corpus. Tests confirm customer, RFQ, order, commercial, and non-synthetic content is excluded.
- Public citations are allowlisted to public-safe fields such as title and product code; internal metadata and storage locators are not exposed.

### Feature flags

- Base/production defaults: `PUBLIC_AI_ENABLED=False` and `PUBLIC_SYNTHETIC_RAG_DEMO_ENABLED=False`.
- The synthetic public demo is enabled only through development settings and is additionally restricted to `DEBUG` plus loopback client addresses.
- Promotion to `main` does not implicitly enable public AI in production.

### Governance

- Draft content cannot be indexed.
- Review and independent approval are required.
- Indexing requires the approved, current, immutable revision hash; stale approval hashes are rejected.
- Owner review, quality controls, pilot scope, and access scope remain enforced.
- No test-only production bypass was found.

### Routes and frontend

- The specific private download route precedes the generic transition route; route regression tests pass and no shadowing was found.
- Frontend review found no `console.log`/debug output, hard-coded development credentials, exposed bearer token, or raw model HTML rendering (`dangerouslySetInnerHTML` is not used).
- Public naming is `AI Component Assistant`.

## 7. Test matrix

All commands below were run against the reviewed code HEAD after the hygiene fix.

| Area | Command/check | Exact result |
|---|---|---|
| Targeted security/RAG/routes | Governance, pilot security, synthetic internal/public RAG, and upload hardening pytest set | **44 passed in 15.20s** |
| Backend | `pytest -q` | **554 passed in 50.98s**; 0 failed, 0 errors |
| Django system check | `python manage.py check --settings=config.settings.test` | **PASS**, no issues |
| Migration drift | `python manage.py makemigrations --check --dry-run --settings=config.settings.test` | **PASS**, no changes detected |
| Clean DB migration/bootstrap | Isolated SQLite migrate, conflict, role/permission, and WSGI assertions | **PASS** |
| Frontend typecheck | `npm run typecheck` | **PASS** |
| Frontend unit tests | `npm test` | **150 passed**, 0 failed/cancelled/skipped |
| Frontend build | `npm run build` | **PASS**, 29 modules, built in 433 ms |
| Authenticated browser | Login → `#/admin-ai-chat` → SUS316 supported with source → weather unavailable → `#/admin-rag-demo` | **PASS** |
| Public browser | Home widget → SUS316 supported with public-safe source → weather unavailable | **PASS** |
| Browser diagnostics | Console warnings/errors and observed request failures | **None**; tested requests returned HTTP 200 |

Browser fixtures, the temporary synthetic import CSV, temporary user, and temporary SQLite database were removed after the run.

## 8. CI review

| Workflow | Direct push to `integration/*` | Pull request to `main` | Required promotion evidence |
|---|---:|---:|---|
| `.github/workflows/ci.yml` | Yes (`push` is unfiltered) | Yes | Full backend/frontend jobs, PostgreSQL 16 migration smoke, Windows phase-6 static checks |
| `.github/workflows/aws-lab-ci.yml` | No; push filter is `main`, `develop`, `feature/**` | Yes | AWS lab compose/build validation |
| `.github/workflows/test_pipeline.yml` | No; push filter excludes `integration/*` | Yes | Phase 13.2 pipeline |

A protected PR to `main` exercises all three workflows and closes the branch-filter gap. Local checks do not replace the PostgreSQL, Windows, AWS lab, frozen-lockfile/format, or phase 13.2 CI jobs. All required PR checks must be green before promotion.

## 9. Branch protection status

**NOT VERIFIED**

The local GitHub CLI is installed, but its credential is not valid, so required checks, required reviews, force-push policy, and repository default-branch settings could not be queried reliably. No setting was changed and no assumption is made. An authorized repository administrator must confirm protection before merge.

The local remote-tracking state reports `origin/HEAD -> origin/codex/demo-database-validation`; this task intentionally did not change it.

## 10. Promotion recommendation

**PROTECTED PR TO MAIN**

Create a pull request from `integration/platform-current` to `main`, require the full CI matrix and human review, confirm branch protection, then merge through the protected GitHub flow. The ancestry permits a fast-forward-compatible promotion, but a protected PR is preferred because it triggers workflows not exercised by a direct integration-branch push and provides an auditable review gate.

Do not force-push, do not rebase the platform history, and do not bypass required checks.

## 11. Legacy main preservation

Immediately before a future promotion, create a protected branch or annotated tag named `legacy-main-before-platform-promotion` at `5a015e8`. Preserve these additional checkpoints:

- `eca707a` — phase-6/pre-remote-merge checkpoint.
- `8458ab7` — integration base.
- The exact integration promotion SHA selected after PR review.

Verify the refs exist on the remote before merging. No backup ref was created in this task.

## 12. Default branch plan

Only after promotion, all required CI checks, branch-protection confirmation, and a clean-clone validation pass:

1. Confirm `main` points to the approved promotion result.
2. Set the repository default branch to `main` through the authorized repository settings.
3. Refresh/verify the remote symbolic HEAD so `origin/HEAD -> origin/main`.
4. Clone afresh and confirm the default checkout is the promoted `main`.

No default-branch or symbolic-HEAD change was performed here.

## 13. Rollback plan

1. Preserve the pre-promotion `main` ref (`5a015e8`), integration SHA, PR number, CI evidence, and deployed release identifier.
2. Stop or pause further deployment if a promotion defect is detected.
3. If the protected PR produces one merge commit, open an emergency protected PR that reverts that merge commit.
4. If promotion is fast-forwarded, create a normal revert commit covering the promoted range and deliver it through a protected PR; do not reset or force-push `main`.
5. Redeploy the last known-good legacy release and restore its configuration/data compatibility as documented by the deployment process.
6. If the repository default branch had already changed away from the desired stable branch, restore it through authorized settings after the rollback commit is validated.
7. Run migration safety checks, backend/frontend tests, browser smoke, and clean-clone validation on the rollback result.
8. Keep `integration/platform-current` and all checkpoint refs for diagnosis; do not delete them.

## 14. Post-promotion checklist

- [ ] Confirm the protected PR has required approvals and every required check is green.
- [ ] Confirm the legacy backup ref at `5a015e8` and checkpoints `eca707a`/`8458ab7` exist remotely.
- [ ] Record the promoted commit SHA and deployed release identifier.
- [ ] Fresh-clone the repository from `main` into an empty directory.
- [ ] Verify the fresh clone checks out the expected promoted SHA.
- [ ] Install backend dependencies from the locked/declared dependency source.
- [ ] Install frontend dependencies with the CI frozen-lockfile command.
- [ ] Migrate an empty PostgreSQL database and verify no conflicting/missing migrations.
- [ ] Run the complete backend `pytest` suite.
- [ ] Run Django system and migration-drift checks using production-compatible settings.
- [ ] Run frontend typecheck, all frontend tests, formatting checks, and production build.
- [ ] Start the app and perform homepage/admin browser smoke tests with a non-production test account.
- [ ] Verify an authorized internal synthetic RAG query is supported with a citation.
- [ ] Verify an unsupported internal query returns `UNAVAILABLE`.
- [ ] Verify anonymous and unauthorized users cannot access internal RAG chat.
- [ ] Confirm production public AI flags remain off.
- [ ] In an explicitly local/development environment, verify the public component query is supported and a weather query is unavailable.
- [ ] Confirm no customer/RFQ/order/employee/private metadata appears in public output.
- [ ] Confirm browser console and network logs contain no unexpected errors.
- [ ] Confirm health checks, observability, and deployment rollback controls are operational.
- [ ] After all validation passes, verify repository default branch and `origin/HEAD` point to `main`.

## 15. Actions NOT performed

- No merge or promotion to `main`.
- No push to `main` or any other remote branch.
- No force push, history rewrite, or platform-history rebase.
- No remote default-branch or `origin/HEAD` change.
- No branch or tag deletion.
- No legacy backup branch/tag creation.
- No branch-protection or repository-setting modification.
- No rollback execution.

## Final answer

**Yes—with gates.** `integration/platform-current` is safe to submit for promotion to `main` through a **protected pull request**. It is not safe to merge outside that process: branch protection must first be verified, and every PR workflow—especially PostgreSQL migration smoke, Windows static checks, AWS lab validation, and the phase 13.2 pipeline—must pass.
