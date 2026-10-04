# AI Sales Assistant — Integration / Pre-Merge Review

## 1. Review identity

```text
WORKSPACE: C:\Users\hoang\Documents\Codex\mecprecision-main-verification-c03d555
BRANCH: feature/ai-sales-assistant
REVIEWED FEATURE HEAD: 366c83fbc31d7363a7060a2399da28f9897e4037
ORIGIN MAIN HEAD: c03d55506ef3ffd38e5e7bb290b981c1a3ccb17f
REVIEW DATE: 2026-09-26
MERGED TO MAIN: NO
```

`REVIEWED FEATURE HEAD` is the code/documentation tip fetched and inspected before this report and its environment-documentation update were committed. The final feature SHA is recorded by Git and in the delivery response; a commit cannot embed its own final SHA.

## 2. PR diff summary

The final documentation-inclusive PR contains `21` changed files, `3,091` insertions, `20` deletions, and `15` feature commits relative to `origin/main`.

Major components:

- Backend AI Sales: one structured internal analysis flow extending `SalesAssistantService`.
- Sales access control: shared `RfqAccessService` used by selector and analyzer.
- Knowledge/RAG: exact fail-closed `governed_synthetic` source boundary and evidence filtering.
- Observability: bounded metrics and governance-event result enrichment.
- API: canonical RFQ selector, internal analyzer, and tightened legacy endpoint authorization.
- Frontend: authenticated `#/admin-ai-sales` workspace with canonical and synthetic flows.
- Tests: deterministic backend security/integration coverage and frontend transport/race coverage.
- Documentation/config examples: audit, implementation, independent review, handoff, pre-merge report, and explicit safe knowledge-source examples.

No merge commit, binary, generated build artifact, credential, temporary fixture, debug dump, n8n/LINE feature, email send, business mutation, or unrelated refactor is part of the PR. The largest introduced objects are normal text source/docs; no large binary was added. `origin/main` is an ancestor of the feature branch, so the reviewed tip does not require a merge/rebase to reconcile the current main reference.

## 3. Integration checks

### API

- `GET /api/v1/internal/ai-sales/rfqs/` and `POST /api/v1/internal/ai-sales/analyze/` are unique routes under the existing `/api/v1/` namespace.
- `POST /api/v1/ai/sales-assistant/` keeps its authorized response contract while applying the tightened private-sales boundary.
- Canonical input is exactly `{ "rfq_id": <positive integer> }`; mixing canonical and synthetic fields is rejected.
- Unknown JSON fields are rejected instead of being silently ignored.
- The public AI routes do not call the internal AI Sales views or RFQ/customer services.

### Permissions and object scope

- Both internal endpoints and the legacy private endpoint allow only case-normalized Sales, Manager, or Admin roles.
- Both `ai_sales:read` and `sales:read` remain required; inactive users and inactive roles fail the existing permission service.
- Selector and analyzer both use `RfqAccessService.visible_queryset`; no second unscoped AI Sales RFQ lookup was found.
- Sales can see RFQs where `created_by=user` or `assigned_to=user`; Manager/Admin can see all RFQs.
- Foreign and missing RFQ IDs return the same 404 envelope.
- `SalesRfq.created_by` is a required protected foreign key; `assigned_to` is a nullable `SET_NULL` foreign key. Existing indexes cover creator/assignee access patterns and no schema change is needed.

### Data minimization

The selector returns exactly: `id`, `rfq_number`, `status`, `project_name`, `customer_display`, `quote_due_at`, and `required_delivery_date`. It excludes customer email/phone/notes, RFQ notes, documents, quotations, orders, and document content. The frontend contract matches these names and nullability assumptions for the existing model fields.

Canonical retrieval uses structured material plus allowlisted manufacturing terms, or minimized project/line descriptions. Customer identity, RFQ notes, arbitrary technical-note prose, email, phone, and full objects are not sent to component retrieval. Private RFQ notes may remain in the authorized on-screen summary, but not in RAG input, metrics labels, or audit metadata.

### RAG and source grounding

- `AI_SALES_KNOWLEDGE_SOURCE` defaults to the exact string `governed_synthetic`; any other value, including `production`, case/whitespace variants, an empty value, typo, or direct BusinessProduct selection, raises `ImproperlyConfigured`.
- The service reuses the isolated `SyntheticRagWebDemoService`; it does not fall back to production products, public knowledge, or an unapproved source.
- Accepted evidence requires a bounded `SYN-RAG-####` product code, `[SYNTHETIC DEMO]` title marker, matching `synthetic://rag_synthetic_demo_v1/<code>` citation prefix (allowing the governed revision query suffix), a non-null source/document ID, and a non-duplicate `(source ID, product code)` identity.
- Invalid/empty evidence yields `UNAVAILABLE` and no matched product. Provider prose is not copied into the response, preventing autonomous-action claims from surfacing.

### Metrics and audit

- AI Sales metric names do not conflict with the existing registry.
- Labels are allowlisted status/priority/retrieval/provider/fallback values; no request, customer, RFQ, source text, or identity becomes a label.
- Latency uses the registry's established counter-based `_sum`/`_count` convention.
- Governance correlation/request ID is preserved. The enrichment replaces the initial metadata object, whose only field for this endpoint is `input_reference`, and restores that field together with bounded outcome metadata; model fields, policy decision, request hash, redaction summary, and correlation ID are not overwritten.

### Frontend

- `#/admin-ai-sales` is a unique admin route and uses the existing memory-only bearer token.
- The canonical selector sends GET without a body; canonical analysis sends exactly `{ rfq_id }`; the synthetic form remains visually and structurally separate.
- Independent generation guards protect selector and analysis success/error/loading state. Caller cancellation is classified separately from timeout and does not render a false error.
- Backend response names and frontend TypeScript types agree for status, priority, RFQ selector, matches, sources, human-review flags, and request ID.
- No customer-send, quotation, RFQ/order/customer mutation, pricing, approval, n8n, or LINE control was added.

### Settings, environment, DB, and public/private isolation

- Base/production keep `PUBLIC_AI_ENABLED=False` and `PUBLIC_SYNTHETIC_RAG_DEMO_ENABLED=False`.
- Development intentionally defaults the pre-existing synthetic public-shaped demo on, but that endpoint additionally requires `DEBUG=True`, a loopback client, and the isolated synthetic corpus. This is not a private-sales data path.
- Local and production env examples now document `AI_SALES_KNOWLEDGE_SOURCE=governed_synthetic`; this does not enable a production catalog.
- No model or migration file is changed. The code relies only on existing RFQ/customer/material/document relationships and existing permission rows/grants.
- Public component tests confirm disabled public routes cannot expose private sales/customer records.

### Performance and reliability

- RFQ access uses `select_related` for customer/creator/assignee; analysis prefetches RFQ lines with material/part plus documents, avoiding obvious N+1 behavior.
- Selector results are explicitly bounded to 100. The returned `count` describes the returned bounded page, not a database-wide total; pagination is an accepted MVP limitation.
- RAG executes once per supported analysis; metrics degrade to the process-local registry if Redis is unavailable.
- New tests use in-memory SQLite, deterministic fake RAG or the development-hash embedding provider, no sleeps, no browser service, no stale database, and no live Ollama/provider requirement. Frontend race tests use synchronous generation guards or AbortController events.
- CI uses Python 3.12, Node 22, pnpm 10.34.3, a frozen frontend lockfile, SQLite for the full suite, and a separate PostgreSQL 16 migration smoke. The legacy advisory CI step tolerates unavailable Ollama through its rule-based fallback.

## 4. CI / validation

Executed from the required feature worktree after fetching `origin/main`:

```text
python -m pytest -q
579 passed in 52.76s

python -m pytest -q tests/test_ai_sales_mvp.py tests/test_ai_sales_grounded_synthesis.py tests/test_ai_enterprise_governance.py tests/test_sales_crm_ai.py
47 passed in 11.31s

python manage.py check
System check identified no issues (0 silenced).

python manage.py makemigrations --check --dry-run
No changes detected.

npm run typecheck
PASS

npm test
156 passed, 0 failed, 0 skipped, 0 todo

npm run build
PASS — Vite transformed 31 modules

git diff --check
PASS
```

The full backend suite refreshes three tracked business-simulation evidence timestamps. They were verified as timestamp-only test artifacts and restored to `HEAD`; they are not included in this PR update.

## 5. Security regression checklist

- [x] Unknown unsupported role denied.
- [x] Viewer denied.
- [x] Inactive user denied.
- [x] Missing either required permission denied.
- [x] Foreign RFQ has the same semantics and response as missing.
- [x] RFQ notes and arbitrary technical-note prose excluded from retrieval.
- [x] Forged/ungoverned source rejected.
- [x] Autonomous provider claim not exposed.
- [x] Legacy Viewer customer-summary leak fixed.
- [x] Unknown request field rejected.
- [x] Public/private isolation preserved.
- [x] Stale frontend selector/analysis result prevented.

## 6. Findings

### BLOCKER

None.

### HIGH

None unresolved. The four High findings from the independent review are present as fixes in code and covered by tests: unsupported-role authorization, RFQ-note retrieval leakage, forged source/product grounding, and legacy Viewer customer-summary leakage.

### MEDIUM

None unresolved. The independent stale-response and unknown-field findings remain fixed and covered.

### LOW

None unresolved. The pre-merge review found one documentation/config discoverability gap: `AI_SALES_KNOWLEDGE_SOURCE` was absent from environment examples. The examples were updated to the safe `governed_synthetic` value.

### INFO

- The PR has 14 pre-report commits with clear topical messages and no accidental merge. The final pre-merge documentation commit increases that count by one.
- Existing CI includes an advisory Ollama review step, but the script returns a rule-based `PASS_WITH_WARNING` when Ollama is unavailable and exits successfully; AI Sales tests themselves do not use Ollama.
- The frontend production bundle is approximately 378 kB uncompressed / 101 kB gzip for the main JavaScript asset; this review found no AI Sales-specific build regression or chunk failure.

## 7. Known accepted limitations

- The only enabled knowledge source is still the governed synthetic corpus.
- Production catalog knowledge is not enabled or implemented; selecting it fails closed.
- RFQ scope is creator/assignee for Sales and all-RFQ for Manager/Admin, not tenant isolation or a general customer ACL.
- The selector is bounded to the newest 100 visible RFQs and has no pagination in this MVP.
- There is no n8n or LINE integration and no customer-send/business-mutation automation.
- Human sales/engineering review remains mandatory; the output is advisory and cannot commit price, stock, delivery, certification, manufacturability, quotation, or order action.

## 8. Merge risks

- Before production rollout, reviewers must explicitly accept the creator/assignee object-scope policy or require a future tenant/customer ACL.
- Enabling real catalog knowledge requires a separately approved adapter through the existing governed document/version/index/access-policy pipeline; changing the setting alone must continue to fail closed.
- Manager/Admin visibility is intentionally broad. It depends on the existing role and permission administration being correctly governed.
- The 100-item selector bound may hide older visible RFQs; it is safe from unbounded-query risk but may need pagination as data volume grows.
- Development's loopback-only synthetic public-shaped demo must not be confused with production/public enablement.

## 9. Recommended PR reviewer focus

1. Confirm Sales creator/assignee scope and Manager/Admin all-RFQ scope.
2. Confirm the exact role allowlist plus both permission grants on internal and legacy endpoints.
3. Review minimized selector/retrieval fields, especially exclusion of RFQ notes from RAG.
4. Confirm governed-synthetic evidence checks and production knowledge fail-closed behavior.
5. Confirm legacy access tightening is intentional while its authorized response contract remains compatible.
6. Confirm metrics/audit contain only bounded operational data and preserve correlation IDs.
7. Confirm synthetic versus canonical UI separation, request-generation guards, and absence of action controls.

## 10. Final verdict

`READY FOR PR / MERGE REVIEW`

- No unresolved Blocker.
- No unresolved High.
- Full backend and targeted security/governance suites pass.
- Full frontend typecheck, tests, and production build pass.
- Django system check and migration drift check pass.
- Git diff check passes.
- The feature worktree is clean after the review commit.
- `origin/main` was fetched for comparison but not checked out, modified, rebased, merged, or pushed.
- No work was performed in `C:\Users\hoang\Documents\Django-web-t-123`.

```text
MERGED TO MAIN: NO
```
