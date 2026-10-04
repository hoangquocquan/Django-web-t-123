# Main Promotion Execution Report

## 1. Result

**BLOCKED**

Promotion stopped at the branch-protection gate before any remote mutation. GitHub authentication is valid and `origin/main` is unchanged, but `main` has neither classic branch protection nor an applicable repository ruleset. Creating an unprotected PR or pushing backup/promotion refs before this gate is resolved would violate the requested protected promotion path.

Execution date: 2026-09-24 (Asia/Tokyo)

## 2. Legacy main backup

| Field | Value |
|---|---|
| Intended ref | `legacy-main-before-platform-promotion` (annotated tag preferred) |
| Legacy SHA | `5a015e8ab64a08bd9495b3610ae5a38db71af082` |
| Remote verification | **NOT CREATED / NOT PUSHED** |

The backup operation was intentionally not reached because branch protection verification failed first. The legacy commit remains reachable as the unchanged remote `main` tip.

## 3. PR

| Field | Value |
|---|---|
| PR number | Not created |
| URL | Not available |
| Base | `main` |
| Head | `integration/platform-current` |
| Reviewed code SHA | `a2feb5c635db3d5a045db08dd8f4bbbcee4e6a39` |
| Documentation-only successor | `4455a580ea1a0c70797b454ac2b3d4fa843b1540` |

The exact diff from `a2feb5c` to `4455a58` contains only the added `FINAL_INTEGRATION_REVIEW_REPORT.md`; no product code changed.

## 4. Branch protection

**NOT VERIFIED / BLOCKED — protection is absent**

GitHub API evidence:

- `main.protected`: `false`.
- Classic protection endpoint: HTTP 404 `Branch not protected`.
- Effective branch rules for `main`: empty list `[]`.
- Repository rulesets: empty list `[]`.
- Authenticated account permission: `ADMIN`.

| Protection | Status |
|---|---|
| PR required | **OFF / absent** |
| Required approvals | **OFF / absent** |
| Required checks | **OFF / none configured** |
| Force push blocked | **NOT ENFORCED by protection** |
| Delete blocked | **NOT ENFORCED by protection** |
| Admin bypass | **NOT RESTRICTED by protection** |
| Conversation resolution | **OFF / absent** |
| Signed commits | **OFF / absent** |
| Linear history | **OFF / absent** |

### Required administrator action

Establish a branch-protection rule or repository ruleset targeting `main` before this task resumes. At minimum it should:

1. Require a pull request before merging.
2. Require the repository's chosen number of approving reviews (recommended minimum: one independent approval).
3. Dismiss stale approvals on new commits and require review of the latest push if repository policy uses those controls.
4. Require resolution of review conversations.
5. Require all promotion CI contexts, including backend/Django, PostgreSQL migration smoke, frontend tests/build/frozen-lockfile checks, Windows/static checks, AWS lab validation, phase 13.2 pipeline, and applicable security checks.
6. Block force pushes and branch deletion.
7. Apply enforcement to administrators or explicitly document the repository's allowed admin-bypass policy.
8. Choose merge-history policy deliberately. Merge commits should remain permitted because the approved promotion strategy preserves the platform history; do not require a full-history rebase or squash.
9. Decide signed-commit policy explicitly rather than inferring it during promotion.

The authenticated admin capability was not used to invent or apply repository policy without an explicit approved configuration.

## 5. CI matrix

No PR exists, so no promotion CI run was triggered.

| Check | Result |
|---|---|
| Backend / Django | **NOT RUN on PR** |
| PostgreSQL migration | **NOT RUN on PR** |
| Frontend | **NOT RUN on PR** |
| Windows | **NOT RUN on PR** |
| AWS lab | **NOT RUN on PR** |
| Phase 13.2 pipeline | **NOT RUN on PR** |
| Security | **NOT RUN on PR** |

The prior integration review remains local evidence only: backend 554 passed, frontend 150 passed, typecheck/build/migration/bootstrap/browser checks passed. It is not a substitute for PR CI.

## 6. Human review

No PR was created, so approvals, requested changes, and conversation resolution are **NOT APPLICABLE / NOT VERIFIED**.

## 7. Merge

No merge was performed. Reason: `main` has no branch protection or applicable ruleset, so the required auditable protected path does not exist.

`origin/main` remains exactly:

```text
5a015e8ab64a08bd9495b3610ae5a38db71af082
```

## 8. Fresh clone verification

Not performed because no merge occurred. Post-promotion fresh-clone validation is pending until protection, PR, CI, review, and merge gates are satisfied.

## 9. Post-merge tests

Not performed because `main` was not changed. Required after a future protected merge:

- Full backend `pytest` suite.
- Django system check and migration drift check.
- Empty-database migration/bootstrap, preferably PostgreSQL.
- Frontend typecheck, complete test suite, formatting/frozen-lockfile checks, and production build.

## 10. Browser verification

No post-merge browser verification was performed because no merge occurred. Public and authenticated internal smoke tests remain required on a fresh promoted checkout.

## 11. Feature flags

No production code changed in this execution. The reviewed candidate retains:

```text
PUBLIC_AI_ENABLED=False
PUBLIC_SYNTHETIC_RAG_DEMO_ENABLED=False
```

Development-only local gating remains separate. These values must be reconfirmed after any future merge.

## 12. Default branch

| Field | Value |
|---|---|
| Before | `codex/demo-database-validation` |
| After | `codex/demo-database-validation` (unchanged) |
| Local remote symbolic HEAD | `origin/HEAD -> origin/codex/demo-database-validation` |
| Intended final state after successful promotion | `main`; `origin/HEAD -> origin/main` |

GitHub repository metadata and the local remote symbolic ref agree. No default-branch setting was changed.

## 13. Retained branches/checkpoints

No branch or tag was deleted. Confirmed local/remote references include:

- `origin/main` at `5a015e8`.
- `integration/platform-current` locally at the documentation-only successor of reviewed code.
- `origin/codex/demo-database-validation` at `8458ab7`.
- Local `backup/phase6-pre-remote-merge` at `eca707a`.
- `origin/codex/ai-assistant-update` at `af309f1`.

The integration branch was not pushed because execution stopped before the safe-push gate. No checkpoint tag was created.

## 14. Rollback readiness

- No rollback is required because `main` was not modified.
- Legacy `main` is still directly reachable at `origin/main` SHA `5a015e8`.
- The intended immutable backup ref has not yet been created and must be created and verified after protection is established but before merge.
- Future rollback must use a revert through a protected PR or the deployment runbook; no reset, force push, or history rewrite is permitted.

## 15. Final status

**MAIN NOT CHANGED**

Exact blocker: repository administrators must define and enable the approved protection/ruleset policy for `main`. After that, resume from protection verification, then create and verify the legacy backup ref, push the integration branch without force, create the protected PR, and wait for all CI and human-review gates. No unsafe merge, force push, branch deletion, remote ref creation, or default-branch change was performed.
