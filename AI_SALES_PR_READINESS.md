# AI Sales Assistant — Pull Request Readiness

```text
WORKSPACE: C:\Users\hoang\Documents\Codex\mecprecision-main-verification-c03d555
BRANCH: feature/ai-sales-assistant
FEATURE SHA AT PR CREATION: 1824dad268ad78a3384f5318e0bc9e1609ebaafd
ORIGIN MAIN SHA: c03d55506ef3ffd38e5e7bb290b981c1a3ccb17f
PR NUMBER: 2
PR URL: https://github.com/hoangquocquan/Django-web-t-123/pull/2
PR STATE: OPEN
PR BASE: main
PR HEAD: feature/ai-sales-assistant
CI STATUS: PENDING
MERGED TO MAIN: NO
```

`FEATURE SHA AT PR CREATION` is the commit containing the PR description. This readiness file is committed immediately afterward, so GitHub's final PR head is the later documentation commit recorded by Git and the final delivery response.

## PR identity

Title:

```text
feat(ai-sales): add safe internal AI Sales assistant workflow
```

The PR is open and non-draft. At readiness-file creation, GitHub reported the merge state as blocked because checks and required human approval were not complete. No merge or auto-merge action was requested.

## Current PR scope

- Internal canonical AI Sales analysis and minimized RFQ selector.
- Shared creator/assignee RFQ access boundary for Sales and all-RFQ access for Manager/Admin.
- Sales/Manager/Admin allowlist plus `ai_sales:read` and `sales:read`.
- Governed synthetic RAG with fail-closed production-source configuration.
- Bounded metrics and audit enrichment.
- Authenticated React AI Sales workspace with canonical/synthetic separation and stale-request guards.
- Independent security fixes, regression tests, and review documentation.
- No new model or migration.

## Validation results

Validation was re-run before PR creation on 2026-09-26:

```text
Backend full suite:                       579 passed in 41.29s
Django system check:                      PASS (0 issues)
Migration drift check:                    PASS (no changes detected)
Frontend TypeScript check:                PASS
Frontend tests:                           156 passed, 0 failed
Frontend production build:                PASS (31 modules transformed)
git diff --check:                         PASS
```

The prior pre-merge feature SHA completed all three repository workflows successfully. Checks for the PR head were pending when this readiness record was prepared. Pending checks are not classified as failures.

## Known limitations

1. Production knowledge/catalog is not enabled; only `governed_synthetic` is accepted.
2. Sales RFQ scope is creator/assignee and Manager/Admin scope is all RFQs; this is not tenant isolation or a general customer ACL.
3. The selector returns the newest 100 visible RFQs and does not implement pagination.
4. Priority is an explainable rule set rather than calibrated conversion scoring.
5. No n8n or LINE integration is included.
6. There is no autonomous customer contact or business mutation.
7. Human sales/engineering review remains mandatory.

## Remaining actions before merge

1. Allow the final PR-head CI checks to complete.
2. Have an independent human reviewer inspect authorization, RFQ scope, minimized RAG input, forged-evidence rejection, fail-closed knowledge configuration, legacy authorization tightening, metrics/audit privacy, and frontend safety boundaries.
3. Have the reviewer explicitly accept the creator/assignee policy or request a broader ACL in a separate change.
4. Obtain all required reviewer and repository approvals.
5. Only then consider merge in a separate authorized operation.

This task does not merge the PR, enable auto-merge, push `main`, delete the branch, or change repository protection/default-branch settings.

```text
MERGED TO MAIN: NO
```
