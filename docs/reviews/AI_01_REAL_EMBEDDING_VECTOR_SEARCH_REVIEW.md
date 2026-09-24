# AI-01 Real Embedding and Vector Search Review

## Phase

AI-01 - Real Ollama Embedding and Vector Search

## Date/Time

2026-08-01 Asia/Tokyo

## Branch and Baseline

- Branch: `codex/ai-01-vector-search`.
- Baseline: `e10b456d21e1c190b2944fbe79befb88d81d4763`.

## Objective and Scope

Runtime Knowledge/RAG chuyển từ hash embedding sang Ollama semantic embedding. Test vẫn dùng development fallback được đặt tên rõ để không phụ thuộc service local.

## Architecture Decision

- `EmbeddingProvider` tách model embedding khỏi business flow.
- `VectorStore` tách cách lưu/tìm vector khỏi search/indexer.
- `DjangoJSONVectorStore` là local fallback, không được coi là production vector engine.
- Reindex tạo toàn bộ vector trước, chỉ thay index cũ trong transaction sau khi embedding thành công.
- Search bỏ qua vector khác provider/dimension và áp relevance threshold cấu hình được.

## Database Impact

Migration `knowledge.0003` chỉ thêm metadata: provider, dimension, embedding version, content hash và indexed time. Local demo migration PASS; không commit database runtime.

## Runtime Validation

- Ollama model: `nomic-embed-text:latest`.
- Real embedding dimension: 768.
- Local documents reindexed: 105, failed: 0.
- Resume validation: skipped 105, processed 0.
- Vietnamese unaccented query top source: `CNC Precision Shaft Technical Specification`, score 0.5124.
- English query top source: same document, score 0.8106.
- Out-of-domain query: no sources after threshold.

## Tests

- Focused Knowledge/vector tests: 35 passed.
- Full regression: 354 passed.
- Django check: PASS.
- Migration consistency: PASS.
- Compile check: PASS.
- Git diff check: PASS.

## Security

- Full documents are not logged by embedding provider.
- External AI is not used.
- Old index survives provider failure.
- Human approval remains required; autonomous action is false.

## Tools Not Run

- PostgreSQL/pgvector runtime: NOT_RUN, Docker daemon unavailable.
- Ruff/mypy/bandit/pip-audit: NOT_RUN at this phase; documented in evidence.

## Known Limitations

SQLite JSON search is linear and intended for learning/demo. Production scale requires PostgreSQL + pgvector and a controlled full reindex.

## Rollback

Revert AI-01 commit. Reverse migration `knowledge.0003` only after database backup; no old columns are removed by this phase.

## Ollama Review Decision

- Model: `llama3:latest`.
- Real local inference: yes.
- Fallback used: no.
- Decision: PASS.
- Critical findings: 0.
- High findings: 0.
- Output SHA-256: `2b8783acec5d96ac08fb33abf1425dde061a2f7323eabe32ccd1cd347f9f0faa`.

## Final Phase Decision

PASS

AI-01 is eligible for commit and integration. Production cutover still requires human approval and pgvector readiness review.
