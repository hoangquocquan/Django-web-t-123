## Summary

This PR adds a safe internal AI Sales Assistant workflow for decision support. It provides canonical RFQ analysis, governed RAG component matching, explainable categorical priority, missing-information detection, an advisory next action, a review-only customer draft, a minimized RFQ selector, scoped authorization, bounded metrics/audit metadata, and security hardening.

The assistant is not autonomous and does not enable production catalog knowledge.

## Scope

### Backend

- Adds `POST /api/v1/internal/ai-sales/analyze/` for canonical RFQ or controlled synthetic analysis.
- Adds `GET /api/v1/internal/ai-sales/rfqs/` as a minimized, scoped canonical RFQ selector.
- Extends the existing `SalesAssistantService` rather than creating a parallel subsystem.
- Adds shared RFQ object access through `RfqAccessService`.
- Adds a fail-closed governed knowledge-source boundary.
- Records bounded, non-sensitive operational metrics and governance metadata.
- Tightens authorization on the legacy `POST /api/v1/ai/sales-assistant/` endpoint without changing its authorized response contract.

### Frontend

- Adds the authenticated `#/admin-ai-sales` workspace.
- Separates `REAL / CANONICAL RFQ` from `SYNTHETIC DEMO` input.
- Sends exactly `{ "rfq_id": ... }` for canonical analysis.
- Displays categorical status/priority, missing information, grounded matches, citations, request ID, advisory next action, and a review-only draft.
- Keeps a persistent human-review warning.
- Uses independent stale-request guards for selector and analysis responses.
- Adds no send, approval, pricing, quotation, RFQ/order/customer mutation, or other business-action control.

### Tests

- Covers authentication, role and permission enforcement, RFQ object scope, foreign/missing ID semantics, and legacy authorization.
- Covers minimized RAG input, forged evidence rejection, public/private isolation, safe metrics/audit content, and mandatory human review.
- Covers exact frontend transport, caller cancellation, stale-response prevention, canonical/synthetic separation, and absence of send/mutation controls.

Primary implementation areas are `django_backend/apps/ai_agent/`, `django_backend/apps/sales/services/rfq_access_service.py`, `django_backend/apps/api/`, `figma_make_frontend/src/`, and `tests/`.

No new model or migration is included.

## Security review

An independent adversarial review identified and fixed the following issues:

- Closed authorization for unsupported custom roles even when both permissions were granted.
- Removed private RFQ notes and arbitrary free-form technical-note content from RAG input.
- Rejected forged or ungoverned product/source evidence.
- Fixed the legacy Viewer customer-summary data leak.
- Rejected unknown request fields instead of silently ignoring them.
- Prevented stale frontend selector or analysis responses from replacing newer state.

All identified High findings were fixed. No unresolved Critical or High finding remains. Detailed evidence is in `AI_SALES_INDEPENDENT_REVIEW.md` and `AI_SALES_PRE_MERGE_REVIEW.md`.

## Authorization model

Allowed roles:

- Sales
- Manager
- Admin

Required permissions:

- `ai_sales:read`
- `sales:read`

RFQ object scope:

- Sales: RFQs created by or assigned to the user.
- Manager/Admin: all RFQs.
- Foreign and missing RFQ IDs return the same not-found semantics.

This is not tenant isolation or a general customer ACL.

## Knowledge / RAG boundary

Current source:

```text
AI_SALES_KNOWLEDGE_SOURCE=governed_synthetic
```

Production catalog knowledge is **not enabled**. Unknown or unimplemented sources fail closed with `ImproperlyConfigured`; there is no silent fallback to `BusinessProduct`, public knowledge, or unapproved content.

Real production knowledge will require a separately approved adapter through the existing document governance, versioning, indexing, and access-policy pipeline.

## Safety boundary

Every successful analysis preserves:

```text
human_approval_required = true
autonomous_action = false
```

AI Sales does not automatically:

- send email, LINE, or SMS;
- contact a customer;
- create or approve a quotation;
- change a price;
- mutate an RFQ or order;
- perform a payment or financial action;
- guarantee stock, delivery, capability, manufacturability, or certification.

This is an internal decision-support assistant. Human sales/engineering review remains mandatory.

## Validation

Validation was re-run from `feature/ai-sales-assistant` on 2026-09-26:

```text
python -m pytest -q
579 passed in 41.29s

python manage.py check
PASS — 0 issues

python manage.py makemigrations --check --dry-run
PASS — no changes detected

npm run typecheck
PASS

npm test
156 passed, 0 failed, 0 skipped, 0 todo

npm run build
PASS — Vite transformed 31 modules

git diff --check
PASS
```

The preceding feature SHA also completed the repository's CI, Test Pipeline, and AWS Learning Lab workflows successfully. PR-head checks must still complete for the final documentation commit before merge approval.

## Checklist

- [x] Internal AI Sales API added
- [x] Canonical RFQ selector added
- [x] RFQ object access enforced
- [x] Human review mandatory
- [x] Autonomous actions disabled
- [x] Governed synthetic RAG only
- [x] Production knowledge fails closed
- [x] Sensitive RFQ notes excluded from retrieval
- [x] Public/private isolation preserved
- [x] Legacy Viewer data leak fixed
- [x] Metrics use bounded non-sensitive labels
- [x] Backend tests pass
- [x] Frontend tests pass
- [x] Django checks pass
- [x] Migration drift check pass
- [x] Production frontend build pass
- [x] Independent security review completed
- [x] Pre-merge review completed
- [ ] Human reviewer approval
- [ ] Required CI checks on PR
- [ ] Merge approval

## Known limitations

1. Production knowledge/catalog is not enabled.
2. RFQ scope is creator/assignee for Sales and all-RFQ for Manager/Admin; it is not tenant isolation or a customer ACL.
3. The RFQ selector returns the newest 100 visible RFQs; pagination is not implemented.
4. Priority is an explainable rule set, not calibrated conversion scoring.
5. No n8n or LINE integration is included.
6. No customer or business action is autonomous.
7. Human review remains mandatory.

## Reviewer focus

- Role allowlist and dual-permission enforcement.
- Creator/assignee RFQ scope and foreign/missing not-found behavior.
- Minimized RAG query and exclusion of private RFQ notes.
- Forged/ungoverned evidence rejection.
- Production knowledge source fail-closed behavior.
- Legacy endpoint authorization tightening and compatibility.
- Audit and metrics privacy.
- Canonical versus synthetic frontend separation and stale-request guards.
- Absence of mutation and customer-send controls.

## Before merge

1. Allow all PR-head CI checks to complete.
2. Obtain independent human review of scope and security.
3. Confirm the creator/assignee policy is accepted or request a broader ACL in a separate change.
4. Obtain all required approvals.
5. Consider merge only after those steps; this PR preparation does not merge or enable auto-merge.
