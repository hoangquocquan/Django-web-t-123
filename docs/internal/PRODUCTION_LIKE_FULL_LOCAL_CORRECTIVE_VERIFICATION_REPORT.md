# Production-Like FULL Local Corrective Verification Report

Date: 2026-09-19  
Project root: `C:\Users\hoang\Documents\ChatGPT\WEB O TO DJANGO`  
Previous report: `PRODUCTION_LIKE_FULL_LOCAL_APPLY_VERIFICATION_REPORT.md`  
Previous verdict: `BLOCKED_LOCAL_PRODUCTION_LIKE_DEMO_DATA_APPLY`

## 1. Root causes

Three owner-approved blockers were reproduced before changes:

1. Future quotation timestamps
   - Exact affected rows: `pdv1-quote-705` and `pdv1-quote-revision-705`.
   - Root cause: historical backfill used `now - 6h + step`; RFQs near current time plus quotation revision offsets could move quotation timestamps into the future.

2. RAG provider/search mismatch
   - Stored embeddings: `development-hash-fallback`, `local-hash-embedding`, dimension `32`.
   - Active development runtime before fix: `ollama`, `nomic-embed-text`, dimension `768`.
   - Root cause: FULL seed intentionally indexed with deterministic local hash embeddings, while development settings defaulted to Ollama. The 0.5 relevance threshold also filtered out valid deterministic hash hits.

3. Stale `actual_ai_eval_cases`
   - FULL command report reproduced `actual_ai_eval_cases=20`.
   - `len(load_ai_eval_cases("FULL")) == 150`.
   - Root cause: validation used `owned_business_counts()` without passing the selected profile, so it defaulted to TEST.

## 2. Files changed

Changed corrective files:

- `django_backend/apps/core/production_demo_seed/historical.py`
- `django_backend/apps/core/production_demo_seed/lifecycle.py`
- `django_backend/apps/core/production_demo_seed/generators.py`
- `django_backend/apps/core/tests/test_production_demo_seed.py`
- `django_backend/config/settings/development.py`
- `django_backend/apps/knowledge/services/runtime_health.py`
- `django_backend/apps/knowledge/services/search_service.py`

Created report:

- `PRODUCTION_LIKE_FULL_LOCAL_CORRECTIVE_VERIFICATION_REPORT.md`

No stage, commit, push, merge, or deploy was performed.

## 3. Timestamp fix

The seed-only historical backfiller now places generated historical points at least three days behind its reference `now`, while preserving the relative lifecycle chain.

Additional validation now rejects any seed-owned quotation with `created_at > reference_now`.

Regression coverage added:

- `max(seed-owned quotation.created_at) <= timezone.now()`
- representative chronology:
  - RFQ `created_at` <= quotation `created_at`
  - quotation `created_at` <= sent/customer decision
  - customer decision <= order `ordered_at`
  - order progress events are not before order time

Local DB correction:

- Ran bounded `FULL --apply` rerun against the local disposable SQLite DB.
- Business records were reused.
- Only seed-owned historical timestamps were backfilled by the seed-only helper.
- Post-correction future seed-owned quotations: `0`.

## 4. RAG provider decision

Chosen strategy: Option A, deterministic local demo.

Reason:

- FULL local data was already indexed with deterministic development hash embeddings.
- Ollama health/reindex was not required for this local demo.
- Deterministic provider keeps local demo reproducible and avoids depending on external model availability.

Development settings now default to:

- `KNOWLEDGE_EMBEDDING_PROVIDER=development-hash`
- `KNOWLEDGE_MIN_RELEVANCE_SCORE=0.33`

This is scoped to development settings only. Production settings were not changed.

## 5. Threshold/reindex decision

Calibration before fix showed valid seeded results around:

- `0.3354` to `0.4990`

The selected local-demo threshold is `0.33`:

- high enough to reject measured unrelated probes such as `medical diagnosis cancer` and `football world cup`;
- low enough to return the five required seeded demo topics.

The knowledge fixture content was enriched with explicit demo phrases for:

- CNC first article inspection
- SUS304 quotation requirements
- RFQ drawing requirement
- quotation approval policy
- order delivery procedure

Existing local `production_demo_v1` knowledge documents were refreshed and reindexed in place. Document IDs were preserved.

Post-correction local knowledge counts:

- KnowledgeDocument: `200`
- KnowledgeChunk: `10,601`
- KnowledgeEmbedding: `10,601`

## 6. Retrieval validation results

Normal configured demo threshold was used.

| Query | Result | Confidence | Representative source |
| --- | ---: | ---: | --- |
| CNC first article inspection | 3 | 0.6751 | `[PDV1] CNC milling capability 1` |
| SUS304 quotation requirements | 3 | 0.5220 | `[PDV1] Quotation approval policy 2` |
| RFQ drawing requirement | 3 | 0.4407 | `[PDV1] RFQ intake checklist 6` |
| quotation approval policy | 3 | 0.6947 | `[PDV1] Quotation approval policy 2` |
| order delivery procedure | 3 | 0.6700 | `[PDV1] AI assistant human approval rules 5` |

All returned sources were owned by `production_demo_v1`.

No-answer probes:

| Query | Result | Confidence |
| --- | ---: | ---: |
| medical diagnosis cancer | 0 | 0 |
| football world cup | 0 | 0 |

## 7. Embedding compatibility behavior

Runtime health now reports:

- active embedding signature;
- stored embedding signatures;
- incompatible embedding signatures.

Post-correction:

- active provider: `development-hash-fallback`
- active model: `local-hash-embedding`
- active dimension: `32`
- stored provider/model/dimension: same
- incompatible signatures: none
- stale document IDs: none
- index coverage: `1.0`

Search service also now applies a small lexical rerank on top of vector hits. This is scoped and avoids deterministic hash collisions making obviously matching seeded chunks appear behind unrelated same-score chunks.

## 8. AI eval reporting fix

`owned_business_counts()` is now called with the selected profile.

Regression coverage:

- TEST eval fixture count: `20`
- SMALL eval fixture count: `60`
- FULL eval fixture count: `150`
- FULL command report now shows `actual_ai_eval_cases=150`

Local corrective apply confirmed:

- `ai_eval_cases=150`
- `actual_ai_eval_cases=150`

## 9. Local DB corrections performed

Command:

```powershell
PRODUCTION_DEMO_SEED_ALLOWED=true
PRODUCTION_DEMO_SEED_DATABASE_CONFIRMED=local-disposable
python manage.py seed_production_demo --profile FULL --apply
```

Result:

- Exit code: 0
- `runtime_total_ms`: 33,206
- `knowledge_documents_refreshed`: 200
- reused customers/materials/parts/RFQs/warehouses/leads/opportunities/orders
- orders remained owner-accepted count: `450`
- no duplicate growth detected

## 10. Regression tests

Commands run:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python -m pytest apps/core/tests/test_production_demo_seed.py -q
```

Results:

- `System check identified no issues (0 silenced).`
- `No changes detected`
- `15 passed in 355.45s (0:05:55)`

Focused heavy checks also passed:

- RAG retrieval validation
- FULL profile apply/history/idempotency

## 11. Final counts

Post-correction local counts:

- customers: 200
- materials: 100
- parts/products: 600
- RFQs: 1,500
- quotations: 990
- orders: 450
- knowledge documents: 200
- knowledge chunks: 10,601
- knowledge embeddings: 10,601
- future seed-owned quotations: 0
- chronology defects checked: 0

Owner decision accepted 450 orders as valid; no extra orders were manufactured.

## 12. Final local demo smoke

Read-only local smoke passed:

- customer summary: populated
- lead summary: populated
- sales pipeline summary: populated
- inventory summary: populated
- knowledge search: populated
- Sales Assistant lead analysis/email draft/weekly recommendation: populated

AI safety flags:

- `human_approval_required=true`
- `autonomous_action=false`
- email draft status: `draft_only_not_sent`

SQLite hash before and after AI read checks was unchanged.

## 13. Git status

Final worktree remained unstaged. No commit/push/merge/deploy was performed.

Expected dirty/untracked files include existing seed work, frontend pre-existing modifications, this corrective report, and the local corrective code changes.

The local SQLite DB remains ignored by git and is not tracked.

## 14. Remaining known gaps

Still intentionally out of scope:

- RFQ `QUOTED` remains omitted.
- Quotation `EXPIRED` remains omitted.
- Knowledge `admin` vs `Admin` role casing remains a separate corrective issue.
- Production-grade semantic retrieval still requires a real embedding provider such as Ollama/pgvector alignment; this task selected deterministic development-hash for the local demo.

## 15. Demo readiness

The concrete blockers from the previous local verification have been corrected:

- no future seed-owned quotation timestamps remain;
- RAG provider/index/search are consistent for the local demo;
- required knowledge searches return owned relevant sources;
- FULL AI eval reporting now reports 150;
- business counts remain stable;
- 450 canonical orders remain valid and accepted by owner decision.

FINAL VERDICT: LOCAL_PRODUCTION_LIKE_DEMO_DATA_READY
