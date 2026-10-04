# AI Sales Assistant — Independent Security and Correctness Review

## Review identity

```text
WORKSPACE: C:\Users\hoang\Documents\Codex\mecprecision-main-verification-c03d555
BRANCH: feature/ai-sales-assistant
REVIEWED COMMIT: 5d16e782a423695703fe2fac9438c8e89e5315f0
FIX COMMIT: a93532f
REVIEW DATE: 2026-09-25
MERGED TO MAIN: NO
```

This was an adversarial review, not a feature iteration. The review attempted permission escalation, IDOR, malformed input, source forgery, unsafe provider output, sensitive retrieval leakage, frontend cancellation/race failures, public/private crossover, audit/metric leakage, and compatibility regressions.

## Scope and files inspected

Primary implementation:

```text
django_backend/apps/sales/services/rfq_access_service.py
django_backend/apps/ai_agent/views.py
django_backend/apps/ai_agent/services/sales_assistant.py
django_backend/apps/ai_agent/services/ai_sales_knowledge.py
django_backend/apps/ai_agent/services/ai_sales_metrics.py
django_backend/apps/ai_agent/services/sales_facts.py
django_backend/apps/ai_agent/services/sales_synthesis.py
django_backend/apps/ai/services/governance_service.py
django_backend/apps/common/observability.py
django_backend/apps/foundation/services.py
django_backend/apps/foundation/models.py
django_backend/apps/sales/models.py
django_backend/apps/knowledge/services/synthetic_rag_demo.py
django_backend/apps/knowledge/services/search_service.py
django_backend/apps/knowledge/services/access_policy.py
django_backend/apps/knowledge/services/public_assistant_service.py
django_backend/apps/knowledge/views.py
django_backend/apps/api/urls.py
django_backend/config/settings/base.py
django_backend/config/settings/development.py
figma_make_frontend/src/api/aiSales.ts
figma_make_frontend/src/api/aiDemo.ts
figma_make_frontend/src/components/AiSalesPage.tsx
```

Documents inspected:

```text
CHATGPT_PROJECT_HANDOFF_AI_SALES.md
AI_SALES_CURRENT_STATE_AUDIT.md
AI_SALES_MVP_IMPLEMENTATION_REPORT.md
```

Tests inspected or executed include `tests/test_ai_sales_mvp.py`, `tests/test_ai_sales_grounded_synthesis.py`, `tests/test_ai_enterprise_governance.py`, `tests/test_sales_crm_ai.py`, the knowledge/public-isolation suites, and `figma_make_frontend/src/api/aiSales.test.ts` plus the complete backend/frontend suites.

## Adversarial cases executed

1. Foreign RFQ by direct ID versus a genuinely missing ID, including identical 404 body comparison.
2. Selector access to owned, assigned, foreign, and unassigned RFQs.
3. Viewer, inactive user, unknown role with both grants, mixed-case Sales roles, missing `sales:read`, and missing `ai_sales:read`.
4. Admin/Manager policy independent of frontend behavior.
5. Exact selector key allowlist and absence of email, phone, customer notes, RFQ notes, documents, quotation, and order data.
6. Canonical request containing private RFQ notes and unrelated line-note content, with captured retrieval query.
7. Unset/approved knowledge default, `production`, case variants, whitespace, typo, empty value, and attempted BusinessProduct source selection.
8. Forged product code, forged citation, ungoverned title, duplicate source identity, and empty source behavior.
9. Provider text claiming email sent, price confirmed, and delivery guaranteed.
10. Metrics with raw customer name/RFQ notes and audit with raw synthetic request markers.
11. Public endpoints disabled and public knowledge restricted to approved public documents.
12. Legacy `customer_summary` direct-ID access by Viewer.
13. Frontend exact `{ rfq_id }`, caller cancellation, independent latest-request guards, token non-persistence, sanitized errors, and absence of send/mutation controls.
14. Unknown JSON fields and mixed canonical/ad-hoc payloads.

## Findings

### CRITICAL

No Critical finding was identified.

### HIGH

#### AI-SALES-SEC-001

- Severity: HIGH
- Component: internal AI Sales authorization
- Status: FIXED
- Evidence: an arbitrary `contractor` role granted `ai_sales:read` and `sales:read` received HTTP 200 for synthetic analysis. The implementation denied only the literal Viewer role.
- Impact: permission administrators could unintentionally grant access outside the documented Sales/Manager/Admin trust boundary; synthetic/internal AI use and future private paths could be exposed to an unsupported principal.
- Reproducibility: deterministic test with a custom role and both grants.
- Fix: both private AI Sales endpoints now require a case-normalized role in `{sales, manager, admin}` in addition to both required permissions.
- Commit: `a93532f`

#### AI-SALES-PRIV-002

- Severity: HIGH
- Component: canonical RFQ → RAG data flow
- Status: FIXED
- Evidence: an RFQ without structured material/process caused `_analysis_query` to fall back to the combined summary containing `rfq.notes`; a unique private marker was captured in the RAG query.
- Impact: private sales notes could be hashed/logged and passed into retrieval/generation even though they were unnecessary for technical matching.
- Reproducibility: deterministic capturing-RAG test with a unique RFQ-note marker.
- Fix: canonical retrieval now has a separate minimized request made only from project/line descriptions; raw RFQ notes are excluded. Free-form line notes are reduced to an allowlisted set of manufacturing-process terms before retrieval.
- Commit: `a93532f`

#### AI-SALES-RAG-003

- Severity: HIGH
- Component: product/source grounding
- Status: FIXED
- Evidence: an injected adapter response with `status=SUPPORTED`, product `INVENTED-999`, an unmarked title, and an untrusted URL produced a `SUPPORTED` matched product.
- Impact: a compromised or incorrectly implemented adapter could turn ungoverned/hallucinated source metadata into a product recommendation.
- Reproducibility: deterministic forged-source adapter test.
- Fix: the current governed-synthetic boundary now accepts only bounded `SYN-RAG-####` codes, `[SYNTHETIC DEMO]` titles, matching dataset citations, non-null source IDs, and non-duplicate identities. Invalid evidence yields `UNAVAILABLE` with no match.
- Commit: `a93532f`

#### AI-SALES-LEGACY-004

- Severity: HIGH
- Component: compatibility endpoint `POST /api/v1/ai/sales-assistant/`
- Status: FIXED
- Evidence: a Viewer seeded with historical `ai_sales:read` called `customer_summary` using a direct customer ID and received HTTP 200 including the private customer email.
- Impact: the compatibility endpoint bypassed the stricter private-AI role boundary and exposed customer-sensitive data to Viewer.
- Reproducibility: deterministic API test with a Viewer and a customer containing a unique email.
- Fix: the compatibility endpoint retains its response contract but now requires Sales/Manager/Admin plus both `ai_sales:read` and `sales:read`.
- Commit: `a93532f`

### MEDIUM

#### AI-SALES-FE-005

- Severity: MEDIUM
- Component: React selector/analysis concurrency
- Status: FIXED
- Evidence: cancellation was the only stale-response control. A transport that ignored/late-observed abort could resolve request A after request B and overwrite the latest state; selector cleanup could also settle loading for the wrong generation.
- Impact: users could see an analysis result that did not correspond to their latest request.
- Reproducibility: independent request-generation test proving old selector/analysis IDs are rejected.
- Fix: separate latest-request guards now protect selector and analysis success, error, and loading state; authentication change and unmount invalidate both generations.
- Commit: `a93532f`

#### AI-SALES-VAL-006

- Severity: MEDIUM
- Component: internal analyze request validation
- Status: FIXED
- Evidence: DRF silently ignored an unknown `customer_email` field next to `rfq_id`, returning HTTP 200, while a known mixed `request` field returned 400.
- Impact: silent field acceptance creates frontend/backend mismatch, weakens the minimized transport contract, and can hide caller mistakes or attempted sensitive-data submission.
- Reproducibility: direct API test with `rfq_id + customer_email`.
- Fix: the serializer now rejects every unknown request key before canonical/synthetic exclusivity validation.
- Commit: `a93532f`

### LOW

No unresolved Low finding was identified. Style-only changes were intentionally not made.

### INFORMATIONAL

#### AI-SALES-INFO-001 — development-only synthetic public demo

Base/production settings keep `PUBLIC_AI_ENABLED=False` and `PUBLIC_SYNTHETIC_RAG_DEMO_ENABLED=False`. Development settings intentionally default the synthetic public-shaped demo to enabled, but the endpoint additionally requires `DEBUG=True` and a loopback remote address and uses the isolated synthetic service. This predates the reviewed AI Sales change and is not a private-sales data path. Reports should say “production/base disabled,” not imply every development runtime has the flag false.

#### AI-SALES-INFO-002 — known object-scope limitation

The implemented RFQ rule is creator/assignee scope for Sales and all-RFQ scope for Manager/Admin. It is not tenant isolation or a general customer ACL. `created_by` is protected from deletion, `assigned_to` is a single nullable foreign key, and inactive users fail permission checks. A future organization/customer ACL should extend the shared service rather than add view-specific queries.

## Data minimization, telemetry, and public/private conclusions

- The selector response has exactly seven fields: ID, RFQ number, status, project name, customer display, quote due date, and required delivery date.
- Selector/analyzer both use `RfqAccessService`; no second AI Sales `SalesRfq.objects.get(pk=...)` path was found.
- Retrieval receives structured material plus allowlisted process terms, or minimized project/line descriptions. Customer identity and RFQ notes are excluded.
- The component provider's generated answer is not copied into the internal AI Sales result; unsafe autonomous claims are therefore not exposed. Legacy generative synthesis separately validates source IDs, allowed structure, mandatory human approval/non-autonomy, and banned claims.
- Metrics use only allowlisted status/priority/retrieval/provider/fallback labels and duration. Governance audit stores request hash plus bounded references/outcomes, not raw request text.
- Public AI remains gated off in base/production, and the public knowledge service accepts only governed public documents; no public path to SalesRfq, BusinessCustomer, quotations, orders, CRM notes, or private governance metadata was found.
- The React page uses the existing in-memory token and does not add localStorage/sessionStorage persistence or customer-send/business-mutation controls.

## Validation evidence

Final validation after fixes:

```text
Targeted security/governance/legacy suite: 47 passed
Targeted AI Sales suite:                   25 passed
Backend full suite:                        579 passed in 40.61s
python manage.py check:                    PASS (0 issues)
python manage.py makemigrations --check:   PASS (no changes detected)
npm run typecheck:                         PASS
npm test:                                  156 passed, 0 failed
npm run build:                             PASS (31 modules transformed)
git diff --check:                          PASS (line-ending warnings only)
```

No test was skipped, weakened, deleted, or converted to an unjustified xfail. No migration was created.

## Required review questions

1. **Can Sales access a foreign RFQ by direct ID?** No. Creator/assignee scope is enforced and foreign/missing IDs return the same 404 envelope without RFQ/customer/note data.
2. **Does the selector leak sensitive customer fields?** No. Exact-key assertions confirm only the seven minimized fields; email, phone, notes, documents, quotation, and order data are absent.
3. **Do selector and analyzer use the same boundary?** Yes. Both use `RfqAccessService.visible_queryset`.
4. **Can production knowledge accidentally enable or fail open?** No. Only exact `governed_synthetic` is accepted; `production`, typo, case/whitespace variants, empty, and BusinessProduct attempts fail closed.
5. **Can AI return an autonomous-action claim without being blocked?** The internal component provider answer is ignored and deterministic output remains human-reviewed/non-autonomous; legacy synthesis rejects banned claims and falls back safely.
6. **Can a matched product exist without governed evidence?** No after the fix. Unsupported, empty, forged, malformed, or duplicate-only evidence produces no match.
7. **Do metrics/audit contain raw customer-sensitive content?** No raw prompt, customer name, RFQ note, email, credential, or source text was found in AI Sales labels/metadata. Governance retains a hash and bounded outcome fields.
8. **Can public AI read sales/private data?** No path was found. Base/production flags are off and the public knowledge pipeline is public-approved-document only.
9. **Does the frontend contain a customer-send/mutation action?** No. It contains analysis controls only; no send, approve, quote, price, RFQ/order/customer mutation action exists.
10. **Was there a legacy AI Sales regression?** No contract regression. A pre-existing Viewer data leak was discovered and fixed while preserving the legacy response contract for authorized Sales/Manager/Admin users.
11. **Did full validation pass?** Yes: backend 579/579, frontend 156/156, Django checks, typecheck, build, migration check, and diff check all passed.
12. **Is there a blocker before integration review?** No unresolved Critical or High finding remains. Known limits are the deliberate synthetic knowledge source and absence of tenant/customer ACL beyond the documented creator/assignee rule.

## Final verdict

`READY FOR INTEGRATION REVIEW`

- No unresolved Critical findings.
- No unresolved High findings.
- Full backend/frontend validation passed.
- Remaining limitations are documented and do not represent a fail-open or autonomous-action path.
- This review did not merge or modify `main`, enable public AI, add n8n/LINE, or add any customer/business action.
