# AI Sales Assistant iteration report

## Post-merge update — 2026-09-26

PR #2 was merged from `feature/ai-sales-assistant` into `main` using GitHub's merge-commit method. Merge commit and merged main SHA: `6c349268db269108f9a012656c5fef37a5b7ab85`.

Post-merge validation passed on the merged state: backend `579 passed`, targeted AI Sales/security/governance `47 passed`, frontend `156 passed`, Django system check passed, no migration drift was detected, TypeScript passed, the production frontend build passed, and `git diff --check` passed. The implementation remains advisory, human-reviewed, non-autonomous, and restricted to the governed synthetic knowledge source.

```text
MERGED TO MAIN: YES
POST-MERGE VALIDATION: PASS
```

## Pre-merge update — 2026-09-26

The independent fixes in `a93532f` and the review record in `366c83f` supersede the earlier implementation snapshot and validation counts below. The integration review re-ran the complete branch against `origin/main` at `c03d55506ef3ffd38e5e7bb290b981c1a3ccb17f`: backend `579 passed`, targeted security/governance/legacy `47 passed`, frontend `156 passed`, Django system and migration checks passed, and the production frontend build passed. The current access policy is the strict Sales/Manager/Admin allowlist plus both `ai_sales:read` and `sales:read`; unknown roles and Viewer are denied. Full pre-merge evidence and remaining limitations are in `AI_SALES_PRE_MERGE_REVIEW.md`.

`AI_SALES_KNOWLEDGE_SOURCE=governed_synthetic` is now also documented in local and production environment examples. No production catalog source was enabled, and `main` was not modified or merged.

## 1. Final status

`READY FOR AI SALES REVIEW`

```text
WORKSPACE:
C:\Users\hoang\Documents\Codex\mecprecision-main-verification-c03d555

BRANCH:
feature/ai-sales-assistant

STARTING COMMIT:
79fdcc5aa65c8273d0725994223fd796305e806f

ENDING IMPLEMENTATION COMMIT:
a1ba5fc (the following documentation commit is intentionally not self-referential)

MERGED TO MAIN:
NO
```

The working tree was clean before this iteration. Only this checkout and branch were changed. `C:\Users\hoang\Documents\Django-web-t-123` and its `codex/demo-database-validation` work were not touched.

## 2. Files changed

```text
django_backend/apps/ai_agent/services/ai_sales_knowledge.py
django_backend/apps/ai_agent/services/ai_sales_metrics.py
django_backend/apps/ai_agent/services/sales_assistant.py
django_backend/apps/ai_agent/views.py
django_backend/apps/api/urls.py
django_backend/apps/sales/services/rfq_access_service.py
django_backend/config/settings/base.py
figma_make_frontend/src/api/aiDemo.ts
figma_make_frontend/src/api/aiSales.ts
figma_make_frontend/src/api/aiSales.test.ts
figma_make_frontend/src/components/AiSalesPage.tsx
tests/test_ai_sales_mvp.py
AI_SALES_CURRENT_STATE_AUDIT.md
AI_SALES_MVP_IMPLEMENTATION_REPORT.md
CHATGPT_PROJECT_HANDOFF_AI_SALES.md
```

No model or migration was added.

## 3. Backend changes

- Added `GET /api/v1/internal/ai-sales/rfqs/`, an authenticated minimized selector endpoint.
- Kept `POST /api/v1/internal/ai-sales/analyze/` and its preferred canonical input `{ "rfq_id": ... }`.
- Added `RfqAccessService` as the shared object-access boundary used by both listing and analysis.
- Added an explicit knowledge-source factory that defaults to governed synthetic knowledge and fails closed for an unimplemented production source.
- Added bounded operational metrics through the existing metrics registry.
- Enriched governance audit only with bounded references, status, priority, source IDs, latency, retrieval/provider state, and fallback state.
- Preserved thin controllers; access, analysis, knowledge selection, and metric rules remain in services.

## 4. Frontend changes and RFQ selector

The internal `#/admin-ai-sales` workspace now has two visibly separate areas:

- `REAL / CANONICAL RFQ`: loads only RFQs visible to the authenticated user, shows a minimized label, and sends exactly `{ "rfq_id": selectedId }` for analysis.
- `SYNTHETIC DEMO`: retains the three bounded regression/demo inputs and never presents them as production customer records.

Canonical results display the RFQ reference, permitted customer display name, summary, status, categorical priority and reasons, grounded matches, missing information, risks, advisory next action/reason, review-only draft, citations, request ID, and persistent human-review notice. There is no customer-send or mutation button.

Browser testing also found a caller-cancellation bug in the shared internal AI client. Caller aborts are now classified as `cancelled`, not `timeout`, preventing a stale React StrictMode request from showing an error after a successful selector load.

## 5. RFQ/customer access scope

The repository did not contain a reusable tenant/customer ownership mechanism for `SalesRfq`, so this iteration introduced a minimal, explicit boundary without claiming tenant isolation:

- Admin and Manager may review all RFQs.
- Sales may review RFQs they created or that are assigned to them.
- Unknown, inactive, and viewer roles receive no RFQs.
- Direct access to an out-of-scope or missing `rfq_id` returns not-found semantics, avoiding object-existence disclosure.
- The selector returns only ID, RFQ number, status, project name, customer display name, and relevant dates; it excludes customer email/phone, raw notes, and the full customer record.

This same service is applied to selector and analysis, so knowing an RFQ ID does not bypass scope.

## 6. Knowledge source and production readiness

Current active source: `governed_synthetic` through the existing synthetic RAG, embeddings, vector store, knowledge search, versioning, citations, and access policy.

The future configuration boundary is `AI_SALES_KNOWLEDGE_SOURCE`. The current default remains governed synthetic. Any non-implemented source, including `production`, raises `ImproperlyConfigured` instead of silently reading unapproved catalog data.

Production knowledge is not yet enabled. Readiness reporting is content-free and exposes only document/chunk counts plus explicit requirements: approved/versioned knowledge, existing access policy, and mandatory human review. No second RAG engine, vector store, hard-coded production catalog, approval bypass, or public exposure was introduced.

## 7. Operational metrics

The existing metrics registry now records low-cardinality counters only:

- total requests;
- result status distribution;
- priority distribution;
- retrieval hit/miss;
- provider success/fallback;
- deterministic fallback;
- response-duration sum and count.

Labels are allowlisted categorical values. Metrics do not contain prompts, customer names, RFQ notes, email, credentials, source text, or other raw customer content. No large feedback workflow was invented in this iteration.

## 8. Security and safety boundaries

The endpoint remains an internal decision-support assistant. Every successful analysis preserves:

```text
human_approval_required = true
autonomous_action = false
```

There is no email, LINE, SMS, chat, automatic follow-up, quotation/pricing action, RFQ/order/customer mutation, payment action, or customer commitment. Drafts remain advisory and conditional.

The public flags remain disabled:

```text
PUBLIC_AI_ENABLED = False
PUBLIC_SYNTHETIC_RAG_DEMO_ENABLED = False
```

The public component assistant still has no path to Customer, RFQ, Quotation, Order, CRM notes, sales analysis, or private AI audit data.

## 9. Automated validation

Final validation on 2026-09-25:

```text
Backend full suite (repository root):       567 passed in 40.37s
Targeted AI Sales suite:                    13 passed
python manage.py check:                    PASS (0 issues)
python manage.py makemigrations --check:   PASS (no changes detected)
npm run typecheck:                         PASS
npm test:                                  155 passed, 0 failed
npm run build:                             PASS (31 modules transformed)
git diff --check:                          PASS (line-ending warnings only)
```

Coverage includes anonymous/viewer denial, required permission enforcement, Sales/Manager/Admin policy, canonical RFQ loading, scoped selector output, direct-object-reference denial, safe missing-RFQ behavior, public/private isolation, immutable safety fields, bounded audit/metrics, exact `{ rfq_id }` transport, cancellation handling, persistent human-review wording, and absence of send buttons.

## 10. Browser/manual validation

Validated locally in the real React UI at `#/admin-ai-sales` against local Django:

1. Canonical RFQ `RFQ-AI-SALES-UAT-001`: `SUPPORTED`, `HIGH`, correct RFQ/customer identity, grounded `SYN-RAG-0011`, citations, review-only draft, and human-review warning.
2. Synthetic SUS316/CNC/electropolishing: `SUPPORTED`, `HIGH`, grounded match and citation.
3. Tokyo weather: `UNAVAILABLE`, no match/source, `NO_ACTION`, no fabricated recommendation.
4. `Need precision component.`: `NEEDS_MORE_INFORMATION`, `NEEDS_REVIEW`, missing technical fields listed, advisory request-for-details draft.
5. Restricted Sales account: selector showed only its owned RFQ and did not show the Admin-created foreign RFQ. Automated API coverage separately proves a direct foreign `rfq_id` returns 404 without leaking number or notes.

The local records and accounts used here are non-production UAT data only and are not migrations or fixtures.

## 11. Known limitations

- Production knowledge/catalog use remains deliberately disabled until approved/versioned content and its access policy are ready.
- The object rule is role plus creator/assignee scope; it is not a claim of tenant isolation or a general per-customer ACL framework.
- Priority is an explainable rule set, not a calibrated conversion model.
- The legacy `/api/v1/ai/sales-assistant/` remains for compatibility and retains its historical contract.
- Local generation may use the existing validated provider or deterministic grounded fallback; neither can execute an action.
- Human accepted/rejected feedback metrics were not added because no suitably bounded feedback workflow currently exists.

## 12. Commits and remote branch

Iteration commits before documentation:

```text
0398a6f feat(ai-sales): add scoped canonical rfq workflow
a1ba5fc test(ai-sales): cover scoped rfq and safe telemetry
```

The documentation commit and authoritative pushed remote SHA are verified after this report is committed. Only `feature/ai-sales-assistant` is pushed; `main` remains unchanged.

## 13. Recommendation

`READY FOR AI SALES REVIEW`

Review should focus on the creator/assignee policy, the deliberate fail-closed production-knowledge boundary, and whether a later iteration should introduce a broader organization/customer ACL before production rollout. n8n and LINE remain out of scope.
