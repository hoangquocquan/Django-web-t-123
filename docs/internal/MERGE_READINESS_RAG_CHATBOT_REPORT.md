# MERGE READINESS — RAG CHATBOT

## 1. Summary

**READY FOR MERGE REVIEW**

The production-demo seed/governance regression is fixed at its root, all focused and full backend tests pass, authenticated browser E2E passes for the internal AI chat, authorization remains fail-closed, and both the public chatbot and existing admin RAG demo pass regression verification.

Current branch: `codex/demo-database-validation`.

No merge to `main` and no push were performed.

## 2. Root cause of previous failure

Failing test:

```text
apps/core/tests/test_production_demo_seed.py::test_seed_rerun_is_idempotent
```

The failure occurred when `ProductionDemoSeedOrchestrator._ensure_knowledge()` called `KnowledgeIndexer.reindex()`. `KnowledgeAccessPolicy.can_index()` rejected the document with:

```text
PermissionDenied: Only an approved current revision may be indexed.
```

The production-demo seed flow predated the current governance lifecycle. On rerun it compared generated raw content with normalized stored content, falsely detected a change, directly mutated `KnowledgeDocument.content`, and attempted to reindex without creating and approving a new immutable `DocumentVersion`. The document therefore no longer satisfied the approved-current-revision invariant.

This was an integration/compatibility defect between the pre-existing production-demo seed flow and the later governance hardening. It was not caused by the public homepage widget or by the internal chat endpoint itself.

The idempotency test's intended meaning remains unchanged: a second seed run must not create duplicates or unnecessary revisions.

## 3. Fix applied

Files changed for this merge-readiness fix:

- `django_backend/apps/core/production_demo_seed/generators.py`
- `django_backend/apps/core/production_demo_seed/lifecycle.py`
- `django_backend/apps/core/tests/test_production_demo_seed.py`
- `MERGE_READINESS_RAG_CHATBOT_REPORT.md`

Production behavior changes:

- Seeded knowledge now has an explicit `MANAGEMENT` department, named owner, and effective date.
- Content comparison uses the normalized representation, so an unchanged rerun remains genuinely idempotent.
- A real content change creates a new immutable `DocumentVersion` and resets stale approval/index state.
- Seed documents go through the existing governance path: submit review, named-owner review, independent Admin approval, explicit `can_index` check, then indexing.
- No `PermissionDenied` catch, test-only bypass, special indexing permission, or direct approval shortcut was added.

Regression coverage now verifies the approved/indexed state, approved hash/version, independent owner review, department, non-public flag, chunk creation, and stable revision count after rerun. Obsolete expectations that unapproved pilot or draft content was searchable were aligned with the current fail-closed access policy; policy code itself was not loosened.

## 4. Governance impact

- **Internal permissions:** unchanged. Internal chat still requires authentication, capability permission, and an allowed internal role.
- **Public data scope:** unchanged. The public endpoint remains limited to `rag_synthetic_demo_v1` through `PublicSyntheticRagDemoService`, which wraps the shared `SyntheticRagWebDemoService`.
- **Production approval:** strengthened in the seed path. Indexing occurs only after the existing review and independent approval workflow establishes an approved current revision.
- **Synthetic demo isolation:** unchanged. Seeded production-demo knowledge is not marked `ai_public_approved` and is not made pilot-public merely to satisfy tests.
- **Metadata exposure:** public responses continue to omit chunk IDs, document IDs, revision/debug fields, embeddings, internal paths, and internal diagnostics.

## 5. Backend tests

Results:

```text
Exact previous failure + new governed-seed regression: 2 passed
Focused production-demo seed/governance checks:        5 passed
Related governance/pilot/public/internal RAG suites:   64 passed
Full backend pytest -q:                                379 passed, 151 skipped, 0 failed
Full-suite duration:                                   472.72s
```

Additional Django checks:

```text
python manage.py check                         PASS — 0 issues
python manage.py makemigrations --check --dry-run
                                               PASS — no changes detected
```

No schema migration was created.

## 6. Admin authenticated E2E

Real Chrome verification was performed against the running development frontend and backend:

1. Opened the internal login page and authenticated with a local test user in the allowed `Sales` role.
2. Navigated through the authenticated admin shell to `#/admin-ai-chat` without bypassing login.
3. Asked `Which synthetic product uses SUS316 with an electropolished finish?`.
4. Verified `SUPPORTED` and source `SYN-RAG-0011` (`[SYNTHETIC DEMO] Housing 0011`).
5. Asked `Thời tiết Tokyo hôm nay thế nào?`.
6. Verified `UNAVAILABLE` and no supporting source.
7. Navigated within the same in-memory authenticated session to `#/admin-rag-demo`; the session remained active and the page loaded normally.

Authorization verification against `/api/v1/internal/rag-chat/`:

```text
Anonymous request:          403 — bearer authentication required
Authenticated Sales role:  200 — allowed
Authenticated viewer role: 403 — internal staff-role restriction enforced
```

Authorization was not changed to facilitate E2E.

## 7. Public regression

The homepage `#/` was verified in Chrome without an Admin login. The public widget uses the dedicated endpoint:

```text
/api/v1/public/ai-component-demo/
```

Verified behavior:

```text
SUS316/electropolished query: SUPPORTED, source SYN-RAG-0011
Tokyo weather query:          UNAVAILABLE
Sales price query:            UNAVAILABLE
```

The rendered public response exposed only safe source labels and synthetic part codes. It did not expose chunk IDs, document IDs, embedding/debug metadata, internal URIs, or internal diagnostics. The public client sent no Admin bearer token. The dataset remained `rag_synthetic_demo_v1`.

## 8. Admin RAG regression

- `#/admin-ai-chat`: loaded after authentication; supported and unsupported browser flows passed.
- `#/admin-rag-demo`: loaded after authentication and displayed the expected `rag_synthetic_demo_v1` / 25 synthetic product scope.
- Internal RAG endpoint/auth tests and related backend suites passed.
- The existing `SyntheticRagWebDemoService` remains the shared RAG implementation for both internal and public wrappers.

## 9. Frontend verification

```text
npm run typecheck   PASS
npm test            PASS — 167 passed, 0 failed
npm run build       PASS — Vite production build completed
```

Chrome console verification found no warning or error entries for the authenticated admin flow or the public homepage chatbot flow.

The public homepage chatbot tab was left open after verification for manual review.

## 10. Remaining limitations

- This remains a development/demo feature backed only by the controlled synthetic dataset; it is not approval to enable production public AI or ingest real company knowledge.
- Local LLM wording can vary, while support status and source grounding are constrained by the service and tests.
- The repository worktree contains many unrelated pre-existing modified and untracked files. They were preserved and not reset; merge review must scope the intended branch changes carefully.

## 11. Merge recommendation status

**READY FOR MERGE REVIEW**

All required focused tests, full backend tests, authenticated browser E2E, authorization checks, public/admin RAG regressions, Django checks, frontend tests, typecheck, build, and console checks pass.

No merge or push was performed.
