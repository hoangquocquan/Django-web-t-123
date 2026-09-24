# Integration Backend Compatibility Fix Report

## 1. Summary

`READY FOR INTEGRATION REVIEW`

Branch `integration/platform-current` now runs from the clean integration baseline without a developer-specific legacy database or restored legacy backend. The complete backend, governance/RAG, Django, frontend, and browser smoke checks are green.

## 2. Initial failures

Initial command: `pytest -q`

- 511 passed
- 38 failed
- 5 errors
- 43 total failing/error cases classified before fixes

| Category | Count |
| --- | ---: |
| A. Legacy immediate-indexing/governed lifecycle | 19 |
| B. Missing local SQLite/config dependency | 7 |
| C. Retired legacy backend compatibility | 7 |
| D. Missing seed/fixture data | 6 |
| E. Genuine regression | 1 |
| F. Other infrastructure/contract drift | 3 |
| **Total** | **43** |

The complete per-test classification is in `BACKEND_FAILURE_CLASSIFICATION.md`.

## 3. Root causes

### A. Governed lifecycle assumptions

Nineteen older AI/knowledge tests treated document creation as immediate approval and indexing. This was a test-fixture issue: the current platform intentionally requires draft creation, review, independent approval, pilot admission, and indexing.

### B. Local SQLite dependency

Seven compatibility/performance/monitoring tests copied or opened an ignored developer-local legacy SQLite artifact. This was test infrastructure drift and made a clean worktree non-reproducible.

### C. Retired legacy backend expectations

Seven tests still opened or asserted files under the retired `backend/` runtime, or asserted retired English page copy. These were stale compatibility assertions; the canonical runtime is Django and the old backend must remain absent.

### D. Seeded-data assumptions

Six tests assumed imported legacy users, products, customers, orders, or an existing first product. These were non-deterministic fixture assumptions on a clean test database.

### E. Genuine regression

One production routing bug placed the generic knowledge transition route before the specific document download route. The generic route captured `download` and returned HTTP 405. URL ordering was corrected and the private-download regression test now exercises a fully governed readable document.

### F. Other contract/infrastructure drift

Two runtime-health tests used an embedding double without the current `dimensions` signature. The dependency audit also treated `-r requirements-prod.txt` as a package line instead of recursively reading the referenced requirements file.

## 4. Fixes applied

- Added `tests/knowledge_test_helpers.py` with reusable real-service lifecycle helpers:
  - create immutable document revision;
  - submit review;
  - owner review;
  - independent approval;
  - quality review and pilot admission;
  - index through `KnowledgeIndexer`;
  - approve and train pilot readers through production services.
- Updated legacy AI, RAG, chatbot, simulation, demo-data, Ollama, and sales-AI tests to use governed fixtures.
- Added `tests/legacy_sqlite_helpers.py` to generate a bounded temporary SQLite compatibility fixture and normalized Django alias settings.
- Replaced developer-local SQLite assumptions in Phase 12, Phase 14, and Wave 1–3 tests.
- Added deterministic product fixtures and clean-clone migration assertions for Wave 1–3.
- Updated legacy cleanup, admin, UI, and public-site assertions to verify the canonical Django runtime and current frontend.
- Moved the document download route before the generic transition route in `django_backend/apps/api/urls.py`.
- Updated the PROD-03 download regression test to use the real governance and access lifecycle.
- Added the missing embedding-dimension contract to the runtime test double.
- Made the offline dependency audit recursively resolve `-r` / `--requirement` files with cycle protection.
- Removed a prohibited quotation-review phrase from synthetic demo knowledge without changing business behavior.

## 5. Governance verification

- No governance policy was bypassed or made permissive.
- Draft content still cannot be indexed.
- Review and independent approval remain required.
- Indexing still requires the current approved immutable revision and owner/quality evidence.
- Stale approval hashes cannot be reused.
- Knowledge permission and pilot-scope checks remain enforced.
- Public synthetic demo retrieval remains isolated to its bounded synthetic dataset and exposes only public-shaped citations.
- Dedicated governance suite: **39 passed**.

## 6. Backend test result

Final command: `pytest -q`

- **554 passed**
- **0 skipped**
- **0 failed**
- **0 errors**
- Duration: 40.98 seconds

Django checks:

- `python manage.py check`: PASS, 0 issues
- `python manage.py makemigrations --check --dry-run`: PASS, no changes detected

## 7. Frontend regression

- `npm run typecheck`: PASS
- `npm test`: **150 passed, 0 failed**
- `npm run build`: PASS

## 8. RAG/chatbot regression

- Knowledge governance and controlled pilot: **39 passed**
- Synthetic RAG, internal chatbot, public chatbot, vector search, and knowledge assistant selection: **60 passed**
- Browser smoke:
  - `#/admin-rag-demo`: rendered the internal authentication gate
  - `#/admin-ai-chat`: rendered the internal authentication gate
  - `#/`: public site and synthetic assistant rendered
  - SUS316/electropolished query: `SUPPORTED`, cited `[SYNTHETIC DEMO] Optical Sensor Housing` / `SYN-RAG-0011`
  - Tokyo weather query: `UNAVAILABLE`, with no source disclosure

The browser smoke used a temporary local synthetic row and SQLite database. Both temporary artifacts were removed after the check.

## 9. New commits

| SHA | Message | Purpose |
| --- | --- | --- |
| `eef1d13` | `fix(tests): align legacy knowledge tests with governed lifecycle` | Real lifecycle/pilot helpers and governed legacy AI fixtures |
| `a54cd91` | `fix(tests): remove local database dependency from backend suite` | Generated SQLite fixture and clean alias configuration |
| `76d0a39` | `fix(tests): make backend seed fixtures deterministic` | Clean-database Wave 1–3 fixtures and assertions |
| `bb3a9ff` | `fix(tests): align legacy assertions with Django cutover` | Canonical Django/backend/frontend compatibility assertions |
| `e0ba4fe` | `fix(api): route private knowledge downloads correctly` | Production URL-order regression and governed test |
| `f094c19` | `fix(tests): update runtime doubles and dependency audit` | Embedding signature and recursive requirements discovery |

## 10. Remaining limitations

- The Phase 12.1 dependency audit is intentionally offline and therefore does not replace a network-backed CVE scanner such as `pip-audit` or Dependabot.
- Browser smoke verified the internal pages' authentication boundary, while authenticated internal RAG/chat behavior is covered by automated backend and frontend suites.
- No source dirty worktree content was copied or modified, and no merge to `main` was performed.

## 11. Final status

`READY FOR INTEGRATION REVIEW`
