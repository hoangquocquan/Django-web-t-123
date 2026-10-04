# N8N + LINE UAT — FINAL REVIEW REPORT

## Review identity

- Timestamp: `2026-09-27 15:43:24 +09:00`
- Worktree: `C:\Users\hoang\Documents\Codex\n8n-line-uat-demo`
- Branch: `feature/n8n-line-uat-demo`
- Base: `origin/main` at `6c349268db269108f9a012656c5fef37a5b7ab85`
- Reviewed implementation HEAD before this report commit: `29f901a72db54a2ff7f8f0e907cf7c21d08f9ebf`
- Branch commits above base before this report: `12`
- Files changed before this report: `27`
- n8n compatibility target: `2.37.10`

No merge from `main`, remote push, workflow activation, production-data use, or production LINE configuration occurred during review.

## Scope reviewed

The complete branch diff against the freshly fetched `origin/main` was reviewed, including:

- Django approval model, API views, service boundary and URL registration;
- `ai_agent` and Foundation migrations;
- strict environment parsing and default configuration;
- synthetic fixture;
- source n8n workflow and runtime-only workflow builder;
- Windows n8n CLI resolver;
- isolated Foundation role/token bootstrap;
- isolated runtime launcher and owner-project attachment flow;
- automated regression coverage;
- setup, security, dry-run, Phase B and Phase C evidence documents.

## Architecture and security boundary

```text
Synthetic UAT fixture
  -> Django AI Sales analysis
  -> PENDING approval record
  -> n8n Human Approval Gate
  -> explicit APPROVE + synthetic acknowledgement
  -> Django approve endpoint
  -> re-fetch + approved-content verification
  -> final runtime send interlock
  -> Django send endpoint
  -> LINE provider adapter
  -> one UAT recipient
```

The LINE credential exists only in the Django UAT process. The source and runtime n8n workflows do not contain a LINE credential and do not call the LINE Messaging API directly.

## Mandatory safety assertions

```text
LINE_SEND_ENABLED default=false: PASS
LINE_SEND_ENABLED current runtime=false: PASS
source workflow active=false: PASS
runtime workflow active=false: PASS
direct n8n -> api.line.me call absent: PASS
real LINE credential absent from tracked files: PASS
full configured recipient ID absent from tracked files: PASS
production recipient/channel configuration absent: PASS
synthetic fixture only: PASS
human approval gate mandatory: PASS
explicit APPROVE + UAT acknowledgement mandatory: PASS
reject branch cannot reach send: PASS
post-approval content/routing hash enforced by Django: PASS
recipient exact allowlist enforced by Django: PASS
at-most-once send claim committed before provider call: PASS
approval UUID used as LINE retry key: PASS
retry of SENT record does not call provider: PASS
workflow activation/schedule absent: PASS
```

## Permissions and migrations

- `OutboundMessageApproval` is constrained to `environment=uat`, `synthetic=true`, and `channel=line`.
- Known status and approved-content constraints are migration-backed.
- Only Sales/Manager/Admin can read/create within their permitted scope.
- Only Manager/Admin with `line_uat:approve` can approve, reject or invoke the send boundary.
- The isolated UAT bootstrap role has exactly:
  - `ai_sales:read`
  - `sales:read`
  - `line_uat:read`
  - `line_uat:approve`
- No superuser, wildcard or production permission is granted.
- Fresh-database bootstrap and repeat bootstrap are deterministic and idempotent.
- `makemigrations --check --dry-run` reports no model drift.

## Final-review finding and fix

One reproducibility issue was found during final review.

### Finding

The original isolated launcher imported the workflow before a fresh n8n database had an owner and personal project. The later owner could not access that unowned workflow, so the successful UAT run required a manual owner-project re-import and n8n restart.

### Fix

Commit `feea90c fix(line-uat): attach workflow after owner setup` makes the supported lifecycle explicit and fail-closed:

1. `start_live_runtime.ps1` starts the isolated services with sending disabled and reports that owner setup is required; it no longer imports an unowned workflow.
2. The operator completes n8n's normal owner setup without bypassing authentication.
3. `attach_runtime_workflow.ps1` resolves exactly one enabled owner personal project.
4. It imports with `--projectId=<resolved project>` and `--activeState=false`.
5. It restarts only the isolated n8n process tree so permission caches are current.
6. It verifies the workflow is inactive and owned with `workflow:owner`.

The helper fails closed for missing/ambiguous owner state, wrong branch/runtime identity, active workflow JSON, wrong n8n version, live-send switch enabled, missing protected Foundation token, failed restart, or invalid ownership.

Regression coverage was added for owner-project resolution, missing-owner failure and launcher/import sequencing. A read-only check against the completed isolated UAT database also passed.

## Credential and artifact review

The configured LINE access token, channel secret and recipient ID were compared in memory against every tracked branch file and all pending reports without printing their values.

```text
exact configured credential matches=0
signed n8n form URL matches=0
full LINE recipient-ID pattern matches=0
private-key matches=0
new tracked SQLite/database artifacts=0
new tracked runtime logs=0
new tracked DPAPI/token artifacts=0
new tracked runtime-state/pointer artifacts=0
```

Ignored local caches, the normal local Django database and local logs remain outside the branch diff.

## Dry-run and live-UAT evidence

Dry-run evidence:

```text
Scenario A REJECT: PASS
Scenario B APPROVE with send disabled: PASS
provider send count: 0
LINE_SEND_ENABLED=false
```

Phase C evidence:

```text
human approval verified: YES
exact approved message hash verified: YES
provider accepted request: YES (HTTP 200)
final database status: SENT
provider send count for approval: 1
operator received exactly one message: YES
retry caused second provider call: NO
retry caused duplicate LINE message: NO
LINE_SEND_ENABLED restored to false: YES
workflow active: NO
production customer data used: NO
production LINE channel used: NO
```

## Final validation

```text
Relevant pytest suite: 94 passed
Django makemigrations check: PASS — no changes detected
Django system check: PASS — 0 issues
Ruff: PASS
Python helper compile: PASS
PowerShell parse: PASS
Source workflow JSON: PASS
n8n owner-project read-only runtime verification: PASS
git diff --check: PASS
```

Automated tests mock provider calls. No additional LINE message was sent during final review or regression.

## Known UAT-only limitations

- Single synthetic RFQ, one allowlisted recipient and text-only push are supported.
- There is no production mode, broadcast, multicast, narrowcast or autonomous send path.
- Owner account creation remains an explicit operator action in n8n.
- Foundation token protection/rotation and LINE UAT credential lifecycle remain operator responsibilities.
- A process crash after the committed send claim may leave `SENDING`; it requires manual reconciliation and must not be automatically retried.
- Provider acceptance is not a general delivery guarantee; this UAT separately recorded operator receipt.

## Final review verdict

```text
FINAL REVIEW: PASS
ALL REQUIRED FIXES COMMITTED: YES
WORKING TREE CLEAN BEFORE REPORT CREATION: YES
SECRETS COMMITTED: NO
RUNTIME ARTIFACTS COMMITTED: NO
LINE_SEND_ENABLED: false
WORKFLOW ACTIVE: false
DRY-RUN UAT: PASS
PHASE C LIVE UAT: PASS
READY TO PUSH FEATURE BRANCH: YES
READY TO CREATE PR INTO MAIN: YES
READY TO MERGE PR: NO — requires normal PR review and CI
```

This report authorizes only pushing `feature/n8n-line-uat-demo` and opening a PR for review. It does not authorize merging, activating the workflow, enabling LINE sending, using production data or transitioning to production.
