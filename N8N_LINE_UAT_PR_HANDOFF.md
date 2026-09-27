# n8n + LINE UAT — Pull Request Handoff

**Recorded:** 2026-09-27 (Asia/Tokyo)

## 1. Branch and pull request

- Branch: `feature/n8n-line-uat-demo`
- Reviewed implementation HEAD before this handoff document: `9a292c33a54da6f9e57e4fa5f5e9306d0b2ee018`
- Remote branch SHA at the start of handoff: `dc9f0aec1a715af67c1e15c3b3d56a7323c6d520`
- Pull request: [#4 — feat(line-uat): add human-approved n8n LINE UAT workflow](https://github.com/hoangquocquan/Django-web-t-123/pull/4)
- Base branch: `main`
- Base SHA / merge base: `6c349268db269108f9a012656c5fef37a5b7ab85`
- PR state at inspection: OPEN
- Merge action performed: NO

The commit containing this handoff document becomes the authoritative final HEAD after it is created and pushed. Its SHA is recorded in the PR and in the final operator handoff because a commit cannot embed its own SHA.

## 2. Commits in the PR before this report commit

1. `25d2f2a` — `feat: add human-gated LINE UAT workflow`
2. `8974e41` — `docs: add LINE UAT handoff report`
3. `c429b58` — `fix(line-uat): harden approval and send safety`
4. `4112ab9` — `docs: add LINE UAT security review`
5. `c15f235` — `fix(line-uat): address dry-run UAT finding`
6. `003dd77` — `docs: add LINE UAT dry-run report`
7. `f81a98a` — `fix(line-uat): repair live runtime workflow builder`
8. `e134278` — `fix(line-uat): bootstrap foundation role for isolated UAT runtime`
9. `6fc347f` — `fix(line-uat): resolve n8n cli dynamically on windows`
10. `8be071e` — `fix(line-uat): support nvm windows cli discovery`
11. `feea90c` — `fix(line-uat): attach workflow after owner setup`
12. `29f901a` — `docs(line-uat): record phase b and live uat evidence`
13. `dc9f0ae` — `docs(line-uat): add final review report`
14. `9a292c3` — `chore(line-uat): clean final diff hygiene`

## 3. Diff scope

- Changed files before adding this handoff: 28
- Expected changed files including this handoff: 29
- Reviewed areas: migrations, Django model/views/service, Foundation permissions, n8n workflow, runtime scripts, tests, configuration examples, and UAT evidence documents.
- Unexpected files: NONE
- Runtime database/log/PID/n8n-state/DPAPI artifacts: NONE

## 4. Final local validation

Validation was rerun after the last code/document hygiene change:

- Relevant pytest suite: **PASS — 94 passed in 11.22s**
- `makemigrations --check --dry-run`: **PASS — No changes detected**
- Django system check: **PASS — 0 issues**
- Ruff: **PASS**
- Python helper compilation: **PASS**
- PowerShell parse validation: **PASS**
- Workflow JSON validation: **PASS**
- Working-tree `git diff --check`: **PASS**

No live LINE test was rerun.

## 5. CI status

For pushed HEAD `dc9f0aec1a715af67c1e15c3b3d56a7323c6d520`, all available checks completed successfully:

| Check | Status |
|---|---|
| Django checks and tests | PASS |
| Phase 13.2 Test Pipeline | PASS |
| Phase 6A PostgreSQL migration smoke | PASS |
| Phase 6A runtime syntax | PASS |
| React production build | PASS |
| Validate local AWS learning lab | PASS |

The documentation/hygiene commits created during this handoff require a fresh CI run after push. Their latest status must be taken from PR #4. This report does not claim merge readiness based on an earlier SHA.

## 6. Secret and artifact scan

- Configured access-token exact matches in changed tracked files: `0`
- Configured channel-secret exact matches in changed tracked files: `0`
- Configured recipient exact matches in changed tracked files: `0`
- LINE user-ID pattern matches: `0`
- Private-key pattern matches: `0`
- Runtime artifact path matches: `0`
- Direct `api.line.me` references in the n8n workflow: `0`
- Credential values printed or copied into this report: NO

## 7. Safety assertions

- `LINE_SEND_ENABLED` tracked default: `false`
- n8n workflow `active`: `false`
- Human approval gate: REQUIRED
- Explicit `APPROVE` plus synthetic-UAT acknowledgement: REQUIRED
- Exact approved content/routing hash verification: REQUIRED
- Django remains the provider and security boundary: YES
- Direct n8n-to-LINE provider call: NO
- Allowlisted UAT recipient check: REQUIRED AT RUNTIME
- Production customer data/configuration committed: NO
- Workflow activated during handoff: NO
- LINE sending enabled during handoff: NO

## 8. UAT evidence

- Dry-run Scenario A — REJECT: PASS
- Dry-run Scenario B — APPROVE with send disabled: PASS
- Dry-run provider send count: `0`
- Phase C live UAT: PASS
- Operator confirmed exactly one UAT LINE message received: YES
- Duplicate retry produced a second provider call/message: NO
- Kill switch restored to false after Phase C: YES

Evidence is documented in:

- `N8N_LINE_UAT_DRY_RUN_REPORT.md`
- `N8N_LINE_UAT_PHASE_B_HANDOFF_REPORT.md`
- `N8N_LINE_UAT_PHASE_C_LIVE_REPORT.md`
- `N8N_LINE_UAT_SECURITY_REVIEW.md`
- `FINAL_REVIEW_REPORT.md`

## 9. Known limitations

- UAT only; no production mode or rollout authorization.
- Validated with one synthetic RFQ and one allowlisted UAT recipient.
- LINE integration is text-only push for this demo.
- A record left in `SENDING` after a crash requires manual reconciliation.
- Runtime tooling targets an isolated local Windows/n8n environment.
- n8n owner initialization remains an authenticated operator action.
- Credentials remain runtime/operator-managed and are not provisioned by the repository.

## 10. Unresolved review items

- PR comments: NONE at inspection time.
- PR reviews: NONE at inspection time.
- Final-HEAD CI: must complete after the handoff commit is pushed.
- Separate human merge review: REQUIRED.

## 11. Merge readiness

- Ready for human PR review: YES
- Ready to merge: NO — final-HEAD CI and a separate merge review are required.
- PR merged: NO

## Final verdict

`READY FOR HUMAN PR REVIEW`
