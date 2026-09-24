# AI Sales MVP implementation report

## 1. Status

`READY FOR AI SALES REVIEW`

Implemented on `feature/ai-sales-assistant`, based on verified `main` commit `c03d55506ef3ffd38e5e7bb290b981c1a3ccb17f`. No merge to `main` and no push or branch-protection/default-branch change was performed.

## 2. Existing AI Sales audit

The repository already contained `SalesAssistantService`, deterministic sales facts, validated Ollama synthesis/fallback, AI governance, sales/CRM models, governed knowledge search, synthetic RAG, a Django AI Sales UI, and tests. The detailed pre-implementation inventory and reuse decisions are in `AI_SALES_CURRENT_STATE_AUDIT.md`.

The MVP extends that subsystem. It does not introduce a second sales assistant, retrieval engine, permission framework, or CRM domain.

## 3. Architecture

```text
SalesRfq / controlled synthetic opportunity
                ↓
       SalesAssistantService
                ↓
Foundation authentication + ai_sales:read + sales:read
                ↓
 existing governed SyntheticRagWebDemoService
                ↓
grounded status / component / citation / next action / draft
                ↓
         mandatory human review
```

The controller is thin: validate, authorize, run governance, call the service, enrich the existing audit event with result status/source IDs, and return the structured envelope.

## 4. Models reused/added

Reused: `SalesLead`, `SalesOpportunity`, `SalesRfq`, `SalesRfqLine`, `SalesRfqDocument`, `SalesQuotation`, `BusinessCustomer`, `BusinessProduct`, and `BusinessMaterial`.

No model or migration was added. A new Lead model was unnecessary because the existing canonical sales/RFQ aggregates cover persisted opportunities and the endpoint also supports bounded synthetic input.

## 5. API

New endpoint:

```text
POST /api/v1/internal/ai-sales/analyze/
```

Input is either a canonical `rfq_id` or controlled fields (`customer_name`, `request`, `material`, `quantity`, `process`, `tolerance`, `surface_treatment`, `drawing_available`, `deadline`). Mixing `rfq_id` with ad-hoc fields is rejected.

The endpoint requires an authenticated, active, non-viewer user with both `ai_sales:read` and `sales:read`. Anonymous and viewer requests are denied. Sales, Manager, and Admin roles are allowed when those grants are present.

The response contract includes `status`, `summary`, categorical `priority`, `priority_reasons`, `matched_products`, `recommended_next_action`, `recommended_next_action_reason`, `draft_response`, `risks`, `missing_information`, `sources`, `request_id`, and mandatory human/non-autonomous safety fields.

## 6. UI

Implemented internal route:

```text
#/admin-ai-sales
```

The workspace requires the existing in-memory authenticated session. It renders opportunity summary, categorical priority/reasons, matched components, missing information, risks, recommended next action, draft-only response, citations, request ID, and a persistent `AI recommendation — human review required` warning.

It includes three explicitly synthetic demo controls for supported, unsupported, and incomplete requests. It contains no send/approve/price/order/RFQ mutation control.

## 7. RAG integration

The service reuses `SyntheticRagWebDemoService`, which itself reuses the existing embedding provider, vector store, `KnowledgeSearchService` reranking, `RagGenerationPipeline`, source-based fallback, indexed governed knowledge records, and citation chain.

Component matching is created only from returned source records with a product code. An unsupported retrieval produces no matched product. The technical retrieval query is data-minimized to material, manufacturing process, and surface treatment when available; free text is used only as a fallback.

The private endpoint does not call the public assistant endpoint. The synthetic corpus remains internal, non-authoritative, non-production-eligible, and separately governed from the public surface.

## 8. Lead/RFQ logic

Statuses are deterministic:

- `UNAVAILABLE` for out-of-scope requests or requests without grounded component evidence.
- `NEEDS_MORE_INFORMATION` when material/process fundamentals are missing.
- `SUPPORTED` only when governed component evidence exists.

Priorities are categorical: `HIGH`, `MEDIUM`, `LOW`, or `NEEDS_REVIEW`. Transparent factors include known customer/company context, quantity, clear material, clear manufacturing/surface process, grounded component evidence, and missing fields. No opaque decimal score is produced by the new endpoint.

Next actions are constrained to advisory values such as `REQUEST_TECHNICAL_DETAILS`, `REVIEW_PRODUCT_MATCH`, `ESCALATE_ENGINEERING_REVIEW`, and `NO_ACTION`, each with a reason. Persisted RFQs are loaded by canonical ID with customer, line, material, part, document, quantity, tolerance, notes, and deadline context.

## 9. Human approval

Every response sets:

```text
human_approval_required = true
autonomous_action = false
```

Drafts are text only. The implementation has no path to send email, submit/approve a quotation, modify price, change an order/RFQ state, contact a customer, or make a financial commitment.

## 10. Security

- Authentication and permission decisions reuse `FoundationAuthService` and `FoundationPermissionService`.
- Viewer is explicitly denied private AI Sales data even though the legacy viewer role has broad read grants.
- AI governance runs before analysis and records a correlation/request ID, actor, timestamp, input reference, result status, and source IDs.
- Audit metadata contains references rather than raw customer requests, secrets, credentials, chain-of-thought, or full records.
- The public component endpoint remains separately gated and cannot read Customer/RFQ/Quotation/Order/sales-note context.
- Base production flags remain unchanged: `PUBLIC_AI_ENABLED=False` and `PUBLIC_SYNTHETIC_RAG_DEMO_ENABLED=False`.

## 11. Tests

Final validation on 2026-09-25:

```text
Backend full suite:                         563 passed, 0 failed, 0 errors
python manage.py check:                    PASS (0 issues)
python manage.py makemigrations --check:   PASS (no changes detected)
Frontend npm run typecheck:                PASS
Frontend npm test:                         152 passed, 0 failed
Frontend npm run build:                    PASS (31 modules transformed)
git diff --check:                          PASS
```

New tests cover the supported SUS316/electropolished case, weather rejection, incomplete request, canonical persisted RFQ loading, anonymous/viewer denial, Sales/Manager/Admin authorization, minimized audit metadata, human approval, URL namespace, and public-data isolation.

## 12. Browser demo

Local browser validation was completed at `#/admin-ai-sales` using an authenticated Admin account and an isolated synthetic `SYN-RAG-0011` document.

- Case A — SUS316 CNC + electropolishing: `SUPPORTED`, `HIGH`, matched `SYN-RAG-0011`, citation displayed, `REVIEW_PRODUCT_MATCH`, grounded draft displayed, human-review warning displayed.
- Case B — Tokyo weather: `UNAVAILABLE`, no match/source, `NO_ACTION`, no fabricated sales recommendation.
- Case C — `Need precision component.`: `NEEDS_MORE_INFORMATION`, missing material/process/quantity/tolerance/surface/drawing/deadline displayed, `REQUEST_TECHNICAL_DETAILS`, draft asks for the missing facts.

The browser pass found and drove fixes for two real integration defects before completion: an out-of-range frontend timeout and an incorrect `/canonical/` API namespace. It also exposed retrieval noise from nontechnical opportunity text, leading to a data-minimized technical query.

## 13. Known limitations

- MVP component matching is intentionally limited to the internal synthetic governed corpus; it is not a production catalog recommender.
- The React workspace currently provides controlled ad-hoc/demo entry. The API supports persisted `rfq_id`, but an RFQ selector has not yet been added to this page.
- Priority rules are transparent heuristics, not a statistically calibrated conversion model.
- The canonical domain has role/permission visibility but no tenant-level or per-customer object-scope policy to reuse; therefore the endpoint does not claim tenant isolation beyond existing canonical access controls.
- The legacy `/api/v1/ai/sales-assistant/` contract remains for compatibility and still exposes its historical numeric lead score. The new internal MVP endpoint uses only categorical priority.
- Local Ollama can return a validated generated answer or the existing grounded source fallback; neither path can execute a sales action.

## 14. Commits

- `e7fd48a` — `docs(ai-sales): audit existing sales assistant state` — records reusable code and gaps before implementation.
- `03458e0` — `feat(ai-sales): add grounded internal sales analysis` — adds the structured service contract, access boundary, audit enrichment, and internal endpoint.
- `25457de` — `feat(frontend): add internal AI sales workspace` — adds the authenticated React route, form, results, citations, and human-review UX.
- `49d2b8d` — `test(ai-sales): cover grounding access and review workflow` — adds backend/frontend status, security, isolation, audit, and UI tests.
- `b37365c` — `fix(ai-sales): minimize component retrieval context` — narrows RAG input to necessary technical fields.
- `3c0d988` — `fix(frontend): route AI sales through internal API root` — fixes timeout and API-root integration discovered in browser testing.
- `5760500` — `test(ai-sales): verify canonical RFQ analysis` — proves persisted canonical RFQ analysis by ID.

## 15. Final recommendation

`READY FOR INTEGRATION REVIEW`

Review should focus on the new internal response contract, role/grant policy, the deliberate synthetic-corpus boundary, and whether the next iteration should add an RFQ selector and an explicit object-scope policy before using real private customer data.
