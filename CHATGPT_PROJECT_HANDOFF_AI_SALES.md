# MecPrecision — ChatGPT project handoff

This is the single self-contained report to give to ChatGPT for review or continuation. It consolidates the relevant repository baseline, architecture, AI Sales audit, implementation, security boundaries, validation evidence, Git state, limitations, and recommended next work.

## Current post-merge status — 2026-09-26

PR #2 was merged on GitHub with a merge commit. The authoritative post-merge record is `AI_SALES_POST_MERGE_REPORT.md`.

```text
PR: #2
SOURCE: feature/ai-sales-assistant
TARGET: main
MERGE METHOD: merge commit
MERGE COMMIT: 6c349268db269108f9a012656c5fef37a5b7ab85
MAIN HEAD AFTER MERGE: 6c349268db269108f9a012656c5fef37a5b7ab85
MERGE DATE: 2026-09-26T06:57:12Z
POST-MERGE VALIDATION: PASS
MERGED TO MAIN: YES
```

Post-merge validation on the merged commit passed: backend `579 passed`; targeted AI Sales/security/governance `47 passed`; frontend `156 passed`; Django system check, migration drift check, TypeScript check, production build, and Git diff check all passed. The initial detached verification checkout produced one environment-only failure because a repository evidence test requires a non-empty branch name; the full suite passed after the checkout was attached to `docs/ai-sales-post-merge`, with no code fix required.

## Pre-merge review update — 2026-09-26

The authoritative current review is `AI_SALES_PRE_MERGE_REVIEW.md`. It reviewed feature code at `366c83fbc31d7363a7060a2399da28f9897e4037` against `origin/main` at `c03d55506ef3ffd38e5e7bb290b981c1a3ccb17f`, including the independent security fixes from `a93532f`. Final local validation was: backend `579 passed`; targeted security/governance/legacy `47 passed`; frontend `156 passed`; Django check, migration drift check, TypeScript check, production build, and Git diff check all passed. No unresolved Blocker or High finding remained.

Current policy is Sales/Manager/Admin only plus `ai_sales:read` and `sales:read`; Sales RFQ scope is creator/assignee, Manager/Admin can review all, and unsupported roles, Viewer, inactive users, missing permissions, foreign RFQs, malformed payloads, and ungoverned evidence fail closed. The selector remains exactly seven minimized fields. Production/base public AI flags remain disabled; development's pre-existing synthetic public-shaped demo remains protected by `DEBUG` and loopback checks. Knowledge remains `governed_synthetic`, with production catalog enablement intentionally unavailable. `MERGED TO MAIN: NO`.

## Latest continuation update — 2026-09-25

This section supersedes older statements below that said the RFQ selector, object scope, production-source boundary, or operational metrics were still future work.

```text
WORKSPACE: C:\Users\hoang\Documents\Codex\mecprecision-main-verification-c03d555
BRANCH: feature/ai-sales-assistant
STARTING COMMIT: 79fdcc5aa65c8273d0725994223fd796305e806f
ENDING IMPLEMENTATION COMMIT: a1ba5fc
MERGED TO MAIN: NO
STATUS: READY FOR AI SALES REVIEW
```

Completed in this continuation:

- `GET /api/v1/internal/ai-sales/rfqs/` provides a minimized, permission-scoped canonical selector.
- `#/admin-ai-sales` now separates `REAL / CANONICAL RFQ` from `SYNTHETIC DEMO`; canonical analysis sends exactly `{ "rfq_id": ... }`.
- `RfqAccessService` is shared by listing and analysis. Admin/Manager see all; Sales see only created/assigned RFQs; foreign direct IDs return 404 semantics.
- Selector data excludes customer email/phone, raw RFQ/customer notes, and full customer records.
- `AI_SALES_KNOWLEDGE_SOURCE` defaults to `governed_synthetic`; unimplemented production selection fails closed.
- Bounded operational metrics cover requests, latency, status, priority, retrieval, provider/fallback, and deterministic fallback without raw sensitive labels.
- React caller cancellation is correctly classified, preventing a stale StrictMode request from displaying an error after a successful selector load.
- Human approval and non-autonomous response fields remain mandatory; no n8n, LINE, send, quotation, pricing, order, RFQ, or customer mutation was added.

Latest validation:

```text
Backend full suite:                       567 passed
Targeted AI Sales:                        13 passed
Django check:                             PASS
Migration check:                          PASS, no changes
Frontend typecheck:                       PASS
Frontend tests:                           155 passed
Frontend build:                           PASS, 31 modules
git diff --check:                         PASS
Browser: canonical + 3 synthetic cases + scoped Sales selector PASS
```

Authoritative details, current limitations, changed files, and browser evidence are in `AI_SALES_MVP_IMPLEMENTATION_REPORT.md`.

## 1. Instructions for the receiving ChatGPT

You are reviewing or continuing development of the **MecPrecision Django + React repository**.

Treat the following as hard constraints:

1. Do not modify or merge `main` without a separate explicit instruction.
2. Work from `feature/ai-sales-assistant` for the AI Sales MVP described here.
3. Preserve the internal-only boundary and mandatory human review.
4. Do not add autonomous email, quotation, pricing, RFQ, order, customer-contact, or financial actions.
5. Reuse existing permissions, governance, RAG, business, sales, and transaction-domain services rather than creating parallel systems.
6. Do not enable public AI production flags.
7. Verify the repository and current branch rather than assuming the working directory is correct.
8. Never include passwords, tokens, credentials, hidden chain-of-thought, or raw sensitive customer records in reports or logs.

Current recommendation:

```text
READY FOR AI SALES REVIEW
READY FOR INTEGRATION REVIEW
```
## 2. Repository and Git state

```text
Repository: https://github.com/hoangquocquan/Django-web-t-123.git
Verified main baseline: c03d55506ef3ffd38e5e7bb290b981c1a3ccb17f
Feature branch: feature/ai-sales-assistant
Implementation snapshot before this consolidated report: ed48ad885e3c1ad9c6258fd399b97e5061795bdd
```

The feature branch was created from the verified `main`, developed without merging `main`, and pushed to GitHub. At the implementation snapshot, the remote branch and local branch both pointed to `ed48ad885e3c1ad9c6258fd399b97e5061795bdd`.

No direct push to `main`, merge to `main`, default-branch change, branch-protection change, or branch deletion was performed.

Pull-request creation URL:

```text
https://github.com/hoangquocquan/Django-web-t-123/pull/new/feature/ai-sales-assistant
```

## 3. Project overview

MecPrecision is a Django backend plus React/Vite frontend for precision-manufacturing business workflows. The promoted baseline already includes:

- Django backend and versioned APIs.
- React 19/Vite frontend.
- Foundation authentication, users, roles, and permissions.
- Business customer, product, and material master data.
- CRM customer profiles, interactions, notes, tasks, and timeline data.
- Sales leads, opportunities, canonical RFQs, RFQ lines/documents, quotations, follow-ups, and activity.
- Transaction-domain orders and append-only progress/audit evidence.
- Knowledge-document governance, approval/versioning, embeddings, vector search, RAG, citations, and access policy.
- Internal synthetic RAG technical demo.
- Public AI Component Assistant behind independent disabled-by-default production flags.
- AI governance, policy checks, redaction, rate limiting, and audit events.
- Protected CI/main workflow.

Important repository areas:

```text
django_backend/apps/ai_agent/          AI Sales and safe agent services
django_backend/apps/ai/                provider abstraction and AI governance
django_backend/apps/knowledge/         governed knowledge search and RAG
django_backend/apps/foundation/        auth, roles, permissions
django_backend/apps/business_core/     customers, products, materials
django_backend/apps/crm/               CRM context
django_backend/apps/sales/             leads, opportunities, RFQs, quotations
django_backend/apps/transaction_domain/orders and progress/audit
django_backend/apps/api/               versioned API routing and controllers
figma_make_frontend/src/               React application
tests/                                 cross-application integration tests
```

## 4. AI Sales code that existed before this feature

The repository already had a meaningful AI Sales subsystem. The implementation deliberately extended it rather than duplicating it.

Existing components included:

- `SalesAssistantService` with lead analysis, customer summary, email draft, and weekly recommendation actions.
- `SalesFactsService` for deterministic and minimized facts.
- `GroundedSalesSynthesisService` using the existing Ollama abstraction, structured JSON validation, unsafe-action rejection, source validation, and deterministic fallback.
- Existing `POST /api/v1/ai/sales-assistant/` endpoint.
- `FoundationPermissionService` and AI governance enforcement.
- `KnowledgeSearchService`, embeddings, vector store, access policy, and citations.
- `SyntheticRagWebDemoService` with isolated synthetic product/component records.
- Django business UI at `/business/ai-sales/`.
- React `#/sales-ai` placeholder that was static and not API-connected.
- Existing tests for RAG grounding, provider failure, draft-only output, human approval, governance, and public/private knowledge isolation.

Existing domain models already included `SalesLead`, `SalesOpportunity`, `SalesRfq`, `SalesRfqLine`, `SalesRfqDocument`, `SalesQuotation`, `BusinessCustomer`, `BusinessProduct`, and `BusinessMaterial`. Therefore no new Lead model or migration was justified.

## 5. AI Sales MVP objective and completed scope

The feature builds a safe internal assistant that can:

- Summarize an opportunity or persisted RFQ.
- Assign an explainable categorical priority.
- Detect missing technical/business information.
- Match product/component knowledge through governed RAG.
- Recommend a constrained next action.
- Produce a customer-facing draft for human review.
- Return source citations and a request/audit ID.

It cannot:

- Send an email.
- Submit or approve a quotation.
- Create or alter a price.
- Change an RFQ or order status.
- Contact a customer.
- Make a commitment about delivery, stock, capability, certification, or finance.

Every response states:

```text
human_approval_required = true
autonomous_action = false
```

## 6. Implemented architecture

```text
SalesRfq ID or controlled synthetic opportunity
                      ↓
             request validation
                      ↓
Foundation authentication + ai_sales:read + sales:read
                      ↓
             AI governance policy
                      ↓
            SalesAssistantService
                      ↓
existing governed SyntheticRagWebDemoService
                      ↓
existing embeddings / vector store / KnowledgeSearchService
                      ↓
grounded status + component + citation + action + draft
                      ↓
             mandatory human review
```

The API controller remains thin. It validates, authorizes, executes governance, invokes the service, enriches the existing governance event with bounded result metadata, and returns the structured response.

## 7. Internal API

New endpoint:

```text
POST /api/v1/internal/ai-sales/analyze/
```

Preferred persisted input:

```json
{
  "rfq_id": 123
}
```

Controlled ad-hoc/synthetic input:

```json
{
  "customer_name": "Synthetic Precision Systems",
  "request": "Need 100 SUS316 precision housings with CNC machining and electropolishing",
  "material": "SUS316",
  "quantity": 100,
  "process": "CNC machining",
  "surface_treatment": "electropolishing",
  "tolerance": "per customer drawing",
  "drawing_available": true,
  "deadline": "2026-12-01"
}
```

`rfq_id` cannot be mixed with ad-hoc fields.

Response contract:

```json
{
  "status": "SUPPORTED",
  "summary": "...",
  "priority": "HIGH",
  "priority_reasons": [],
  "matched_products": [],
  "recommended_next_action": "REVIEW_PRODUCT_MATCH",
  "recommended_next_action_reason": "...",
  "draft_response": "...",
  "risks": [],
  "missing_information": [],
  "sources": [],
  "input_reference": "rfq:123",
  "synthetic_input": false,
  "human_approval_required": true,
  "autonomous_action": false,
  "safety_note": "AI recommendation — human review required...",
  "request_id": "correlation UUID"
}
```

## 8. Deterministic decision logic

Supported statuses:

- `SUPPORTED`: governed component evidence exists.
- `NEEDS_MORE_INFORMATION`: material/process fundamentals are incomplete.
- `UNAVAILABLE`: request is out of manufacturing-sales scope or retrieval has no supported product evidence.

Priorities:

- `HIGH`
- `MEDIUM`
- `LOW`
- `NEEDS_REVIEW`

Factors are explicit and include known customer/company, requested quantity, clear material, clear manufacturing or surface process, grounded component evidence, and missing technical information. The new endpoint does not return deceptive decimal scores.

Advisory next actions include:

- `REQUEST_TECHNICAL_DETAILS`
- `REVIEW_PRODUCT_MATCH`
- `ESCALATE_ENGINEERING_REVIEW`
- `NO_ACTION`

The service explains the selected action but never executes it.

## 9. RAG and data-minimization behavior

The MVP reuses `SyntheticRagWebDemoService`; it does not call the public endpoint and does not create a second retrieval engine.

The internal synthetic corpus remains:

- Marked synthetic.
- Non-authoritative.
- Non-production-eligible.
- Internal permission level.
- Not approved for public AI.

A matched product is emitted only when a returned governed source includes a product code. No source means no recommendation.

The retrieval query is minimized to material, manufacturing process, and surface treatment when those structured fields are available. Customer name, quantity, email, unrelated notes, credentials, and full records are not sent to component retrieval. Free-text request is used only when structured technical fields are absent.

## 10. Authentication, authorization, and audit

The internal endpoint requires:

- An authenticated active Foundation user.
- A non-viewer role.
- `ai_sales:read`.
- `sales:read`.

Anonymous requests are denied. Viewer requests are denied even though the historical viewer role has broad read grants. Sales, Manager, and Admin are allowed when their grants permit it.

Audit uses the existing `AIGovernanceEvent` mechanism and records:

- Correlation/request ID.
- User identity.
- Timestamp.
- Input object reference such as `rfq:123` or `synthetic:ad-hoc`.
- Result status.
- RAG source IDs.

It does not store secrets, raw credentials, full customer requests, or hidden chain-of-thought in the result metadata.

Public data isolation is preserved. The public component assistant cannot read Customer, RFQ, Quotation, Order, sales notes, or lead-analysis data.

Production settings remain:

```python
PUBLIC_AI_ENABLED = False
PUBLIC_SYNTHETIC_RAG_DEMO_ENABLED = False
```

## 11. React internal workspace

New route:

```text
#/admin-ai-sales
```

It uses the existing memory-only Foundation authentication token and calls the internal API root directly.

The page displays:

- Persistent human-review warning.
- Opportunity summary.
- Status and categorical priority.
- Priority reasons.
- Matched components.
- Missing information.
- Risks.
- Recommended next action and reason.
- Draft response marked for review.
- Sources/citations.
- Request ID.

The page contains no external-send or business-mutation control.

It includes three controlled synthetic demo buttons:

1. SUS316 supported case.
2. Unsupported Tokyo-weather case.
3. Incomplete precision-component case.

## 12. Browser validation results

The local browser demo was completed at `#/admin-ai-sales` after authentication with an authorized internal user.

### Case A — supported

Input: SUS316 precision housing, CNC machining, electropolishing, quantity 100.

Observed result:

```text
status: SUPPORTED
priority: HIGH
matched product: SYN-RAG-0011
next action: REVIEW_PRODUCT_MATCH
source citation: displayed
draft: displayed
human-review warning: displayed
```

### Case B — unsupported

Input: `What is the weather in Tokyo?`

Observed result:

```text
status: UNAVAILABLE
matched products: none
sources: none
next action: NO_ACTION
```

### Case C — missing information

Input: `Need precision component.`

Observed result:

```text
status: NEEDS_MORE_INFORMATION
priority: NEEDS_REVIEW
next action: REQUEST_TECHNICAL_DETAILS
```

The UI listed missing manufacturing process, material, quantity, tolerance, surface finish, drawing/document availability, and deadline. The draft asked for those facts instead of inventing them.

Browser validation found and caused fixes for three integration problems:

1. An AI Sales timeout exceeded the canonical client limit.
2. The first frontend implementation incorrectly inherited the `/canonical/` API namespace.
3. Nontechnical opportunity text diluted synthetic RAG overlap; retrieval was narrowed to structured technical fields.

## 13. Final validation evidence

Validation completed on 2026-09-25:

```text
Backend: python -m pytest -q
Result: 563 passed, 0 failed, 0 errors

Django: python manage.py check
Result: PASS, 0 issues

Django: python manage.py makemigrations --check --dry-run
Result: PASS, no changes detected

Frontend: npm run typecheck
Result: PASS

Frontend: npm test
Result: 152 passed, 0 failed

Frontend: npm run build
Result: PASS, 31 modules transformed

Git: git diff --check
Result: PASS
```

Tests specifically cover:

- Supported SUS316/electropolished component match.
- Out-of-scope weather rejection.
- Incomplete request handling.
- Persisted canonical RFQ loading by ID.
- Anonymous and viewer denial.
- Sales, Manager, and Admin authorization with required grants.
- Human approval and non-autonomous behavior.
- Data-minimized audit metadata.
- Correct internal API URL.
- Public/private data isolation.
- Existing AI Sales, RAG, sales, CRM, quotation, order, and frontend regressions.

## 14. Files added or changed

Primary AI Sales changes:

```text
AI_SALES_CURRENT_STATE_AUDIT.md
AI_SALES_MVP_IMPLEMENTATION_REPORT.md
django_backend/apps/ai_agent/services/sales_assistant.py
django_backend/apps/ai_agent/views.py
django_backend/apps/api/urls.py
figma_make_frontend/package.json
figma_make_frontend/src/App.tsx
figma_make_frontend/src/api/aiDemo.ts
figma_make_frontend/src/api/aiSales.ts
figma_make_frontend/src/api/aiSales.test.ts
figma_make_frontend/src/components/AiSalesPage.tsx
tests/test_ai_sales_mvp.py
```

No model or migration file was added.

## 15. Implementation commits

```text
e7fd48a docs(ai-sales): audit existing sales assistant state
03458e0 feat(ai-sales): add grounded internal sales analysis
25457de feat(frontend): add internal AI sales workspace
49d2b8d test(ai-sales): cover grounding access and review workflow
b37365c fix(ai-sales): minimize component retrieval context
3c0d988 fix(frontend): route AI sales through internal API root
5760500 test(ai-sales): verify canonical RFQ analysis
ed48ad8 docs(ai-sales): add MVP implementation report
```

## 16. Known limitations

1. Component matching intentionally uses the governed synthetic corpus, not a production catalog.
2. The React page now contains a minimized canonical RFQ selector and sends only `rfq_id` for persisted analysis.
3. Priority is a transparent rule set, not a statistically calibrated conversion model.
4. AI Sales now enforces Admin/Manager all-RFQ access and Sales creator/assignee scope through one shared service. This remains a minimal object rule, not a claim of tenant isolation or a general per-customer ACL.
5. The legacy `/api/v1/ai/sales-assistant/` remains for compatibility and still has its historical numeric lead score. The new internal endpoint uses categorical priority only.
6. Local Ollama may return a validated generated answer or the existing grounded source fallback.
7. Synthetic demo seed data used for local browser validation is not a production-data migration and must not be treated as real company data.

## 17. Recommended review checklist

Before integration, the reviewer should verify:

- The response contract and categorical priority rules are acceptable.
- `ai_sales:read + sales:read + non-viewer` is the intended access policy.
- Real customer/RFQ use should wait for an explicit object/tenant-scope decision.
- The synthetic corpus boundary is understood and retained.
- The frontend must not gain action buttons that bypass human approval.
- Public AI flags remain off.
- CI reproduces the reported backend, Django, and frontend validation.

Recommended next iteration after approval:

1. Independently review the creator/assignee object-scope rule before real private-data rollout.
2. Replace or supplement the synthetic corpus only through the existing knowledge approval/indexing workflow and the fail-closed source boundary.
3. Add accepted/rejected feedback metrics only when a bounded human-feedback workflow exists.
4. Create or update a pull request from `feature/ai-sales-assistant` to `main`, request an independent reviewer, and merge only after required checks and approval.

## 18. Final handoff status

```text
Branch implementation: COMPLETE
Local validation: PASS
Browser validation: PASS
Feature branch pushed to GitHub: YES
PR #2 state: MERGED
Merge commit: 6c349268db269108f9a012656c5fef37a5b7ab85
Main head after merge: 6c349268db269108f9a012656c5fef37a5b7ab85
Post-merge validation: PASS
Merged to main: YES
AI SALES MERGED TO MAIN — POST-MERGE VALIDATION PASS
```
