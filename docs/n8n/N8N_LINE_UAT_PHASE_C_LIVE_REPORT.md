# N8N + LINE — PHASE C LIVE UAT E2E REPORT

## Run identity

- Timestamp: `2026-09-27 +09:00`
- Worktree: `C:\Users\hoang\Documents\Codex\n8n-line-uat-demo`
- Branch: `feature/n8n-line-uat-demo`
- HEAD: `8be071e687945212c18b04615539837b8e623a4d`
- n8n version: `2.37.10`
- Workflow: `UAT - AI Sales LINE Approval Demo`
- Execution ID: `4`
- Approval UUID: `a3a6afc2-41bd-4460-8ea1-87d6cf390ac2`

No access token, channel secret, Foundation bearer token, Authorization header, or full recipient ID is included in this report.

## Safety preflight

- Correct branch verified: yes.
- Existing unrelated working-tree changes preserved: yes.
- Dedicated operator-designated LINE UAT channel: yes.
- LINE UAT recipient profile reverified read-only immediately before the run: yes.
- Production customer data used: no.
- Production LINE channel used: no.
- Source workflow active: false.
- Runtime workflow active: false.
- Direct n8n call to `api.line.me`: no.
- Provider boundary: Django LINE adapter only.
- Human Approval Gate present: yes.
- Final Runtime Send Interlock present: yes.
- Post-approval re-fetch and exact-content hash verification present: yes.
- `LINE_SEND_ENABLED` before live enable: false.

## Controlled live enable

- Process-only live enable timestamp: `2026-09-27 14:53:52 +09:00`.
- Persistent User/Machine setting changed: no.
- Django runtime verified `LINE_SEND_ENABLED is True` before the approval execution: yes.
- No message was sent during enable or recipient-profile verification.

## Fresh approval and human decision

A new synthetic fixture created a fresh `PENDING` approval. No Scenario A/B approval was reused.

The Human Approval Gate displayed:

- `UAT / SYNTHETIC — NO REAL CUSTOMER` warning;
- RFQ `UAT-RFQ-001`;
- AI recommendation;
- UAT allowlisted-recipient marker;
- exact proposed LINE message.

The operator explicitly selected `APPROVE`, acknowledged synthetic UAT data, submitted the human gate, and separately authorized continuation at the final live-send interlock.

Pre-send revalidation passed:

```text
status=APPROVED
environment=uat
synthetic=true
channel=line
human_approval_required=true
autonomous_action=false
recipient_exact_allowlist_match=true
send_claimed_at=null
approved_content_hash_match=true
LINE_SEND_ENABLED=true (UAT process only)
```

Exact approved-message SHA-256:

```text
2d459c64580191c6893fb4e2b96fb938ad60f6ec50433f5458c9504e5ca1d7c5
```

## Provider attempt and final database state

- Provider attempt count for this approval: `1`.
- Provider result: accepted, HTTP `200`.
- Provider message/request identifier: present; value intentionally omitted.
- Final status: `SENT`.
- `send_attempted=true`.
- `send_claimed_at`: present.
- `sent_at`: `2026-09-27 06:07:15.095165 UTC`.
- `line_result_status=SENT`.
- Approved content hash unchanged: yes.
- Audit order: `DRAFT_CREATED → APPROVED → SEND_CLAIMED → SENT`.
- `SEND_CLAIMED` event count: `1`.
- `SENT` event count: `1`.

Provider acceptance is confirmed independently from operator receipt. At `2026-09-27 15:24:31 +09:00`, the operator manually confirmed that the UAT recipient received exactly one LINE message and that its content matched the approved message.

## Idempotency retry

The Django send endpoint was called one additional time with the same already-`SENT` approval UUID.

```text
retry HTTP result=200
provider message/request identifier unchanged=true
sent_at unchanged=true
SEND_CLAIMED count before=1
SEND_CLAIMED count after=1
SENT event count before=1
SENT event count after=1
```

The retry did not create a second provider call. The operator subsequently confirmed that exactly one LINE message was received; no duplicate message was observed.

## Kill-switch restoration and post-send state

- Django live-send process stopped immediately after the one retry check.
- Django restarted with `LINE_SEND_ENABLED=false`.
- Runtime setting verified as literal boolean `False`.
- Persistent User/Machine live-send setting: false/unset.
- Workflow active: false.
- Waiting n8n executions: `0`.
- Scheduled/automatic workflow enabled: no.
- Additional approval waiting to send from this run: no.
- No automatic retry worker was enabled.

## Secret and log review

Runtime Django and n8n logs were scanned without printing sensitive values:

```text
runtime credential-value matches=0
runtime Authorization bearer-header matches=0
runtime Foundation-token-name matches=0
runtime full-recipient-ID-pattern matches=0
tracked real credential-value matches=0
```

One unrelated tracked documentation file contains an illustrative `Authorization: Bearer ...` example. It does not match any configured credential and is not a runtime log or Phase C report finding.

Secret/log scan: PASS.

## Regression

```text
Relevant pytest suite: 91 passed
Django system check: PASS (0 issues)
Ruff: PASS
Source workflow JSON: PASS
Runtime workflow JSON: PASS
```

No LINE message was sent during regression.

## Unresolved risk

None for the scoped Phase C UAT acceptance criteria. This result remains UAT-only and is not authorization for production rollout or merge.

## Final verdict

```text
PHASE C LIVE UAT: PASS
LIVE MESSAGE SENT TO UAT RECIPIENT: YES
PROVIDER SEND COUNT FOR APPROVAL: 1
OPERATOR RECEIVED EXACTLY ONE MESSAGE: YES
RETRY CAUSED SECOND PROVIDER CALL: NO
RETRY CAUSED DUPLICATE LINE MESSAGE: NO
LINE_SEND_ENABLED RESTORED TO FALSE: YES
WORKFLOW ACTIVE: NO
PRODUCTION CUSTOMER DATA USED: NO
PRODUCTION LINE CHANNEL USED: NO
READY FOR FINAL REVIEW BEFORE MERGE: YES
```

All scoped Phase C acceptance conditions are satisfied. No additional LINE send is authorized or required.

No main merge, remote push, workflow activation, or production transition was performed.
