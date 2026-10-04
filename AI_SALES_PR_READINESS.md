# AI Sales Assistant — Pull Request Readiness

```text
WORKSPACE: C:\Users\hoang\Documents\Codex\mecprecision-main-verification-c03d555
BRANCH: feature/ai-sales-assistant
FEATURE SHA REVIEWED: 06b860d3458ae12dceaa47ad8b4c5972b55f7213
ORIGIN MAIN SHA: c03d55506ef3ffd38e5e7bb290b981c1a3ccb17f
PR NUMBER: 2
PR URL: https://github.com/hoangquocquan/Django-web-t-123/pull/2
PR STATE: OPEN
PR BASE: main
PR HEAD: feature/ai-sales-assistant
CI STATUS: PASS (all 12 reported check runs on reviewed SHA)
REVIEW STATUS: NO HUMAN REVIEW / APPROVAL YET
MERGEABILITY: MERGEABLE / CLEAN
MERGED TO MAIN: NO
```

`FEATURE SHA REVIEWED` is the PR head whose GitHub checks and local validation were inspected before the final CI-review documentation commit. A commit cannot embed its own SHA; the final documentation SHA and its checks are recorded by GitHub and the delivery response after push.

## PR identity

Title:

```text
feat(ai-sales): add safe internal AI Sales assistant workflow
```

The PR is open and non-draft. GitHub reports it as mergeable with a clean merge state. There are no reviews, no approval, and no active changes-requested review. No merge or auto-merge action was requested.

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
Backend full suite:                       579 passed in 42.00s
Django system check:                      PASS (0 issues)
Migration drift check:                    PASS (no changes detected)
Frontend TypeScript check:                PASS
Frontend tests:                           156 passed, 0 failed
Frontend production build:                PASS (31 modules transformed)
git diff --check:                         PASS
```

All reported PR checks for the reviewed SHA passed: both CI workflow runs, both Test Pipeline runs, and both AWS Learning Lab runs. No failed, cancelled, skipped, or pending check remained on that SHA. The final documentation commit must receive its own successful checks before the final verdict is delivered.

## Known limitations

1. Production knowledge/catalog is not enabled; only `governed_synthetic` is accepted.
2. Sales RFQ scope is creator/assignee and Manager/Admin scope is all RFQs; this is not tenant isolation or a general customer ACL.
3. The selector returns the newest 100 visible RFQs and does not implement pagination.
4. Priority is an explainable rule set rather than calibrated conversion scoring.
5. No n8n or LINE integration is included.
6. There is no autonomous customer contact or business mutation.
7. Human sales/engineering review remains mandatory.

## Remaining actions before merge

1. Have an independent human reviewer inspect authorization, RFQ scope, minimized RAG input, forged-evidence rejection, fail-closed knowledge configuration, legacy authorization tightening, metrics/audit privacy, and frontend safety boundaries.
2. Have the reviewer explicitly accept the creator/assignee policy or request a broader ACL in a separate change.
3. Obtain all required reviewer and repository approvals.
4. Only then consider merge in a separate authorized operation.

This task does not merge the PR, enable auto-merge, push `main`, delete the branch, or change repository protection/default-branch settings.

```text
MERGED TO MAIN: NO
```
