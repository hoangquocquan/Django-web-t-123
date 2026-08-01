# AI-00 Reproducible Baseline Review

## Phase

AI-00 - Discovery and Reproducible Baseline

## Branch

`codex/ai-00-baseline`

## Baseline Commit

`e0af74650ca3670589f482ff7fe44804d6ff41f7`

## Objective

Xác minh môi trường thật và thiết lập nguồn evidence trước khi triển khai AI-01.

## Repository Findings

- Python: 3.12.10.
- Django: 5.2.16.
- Django system check ban đầu: PASS.
- Ollama endpoint: `http://localhost:11434`.
- Generation model: `llama3:latest`.
- Embedding model: `nomic-embed-text:latest`.
- Embedding validation: 2 vectors, 768 dimensions.
- Docker CLI có, Docker daemon không chạy; Docker config báo access denied.
- Redis URL có placeholder; distributed Redis validation chưa chạy ở AI-00.
- Database mặc định là Django SQLite local và legacy database router theo settings hiện có.

## Existing AI Architecture

- `apps.ai`: Ollama client, model configuration, health and governance.
- `apps.knowledge`: document ingestion, deterministic hash embedding, RAG and search.
- `apps.ai_agent`: keyword controller, safe tools and sales assistant.
- `ai-review` và `ai-factory`: phase evidence/review framework hiện có nhưng chưa fail-closed đầy đủ.

## Security Review

- Không có external AI API được gọi.
- Không có autonomous action.
- Không deploy hoặc merge.
- Ba ZIP ngoài scope không được stage.
- Runtime database và `.env` không được stage.

## Known Limitations

- Docker daemon unavailable.
- Redis distributed rate limiting chưa được xác minh.
- PostgreSQL/pgvector chưa được xác minh.
- Existing AI review logic có nhánh fallback warning; AI-05 sẽ phải chuyển sang fail-closed.

## Rollback

Dùng `git revert <AI-00-commit>` trên branch tích hợp nếu cần. Không dùng reset hard.

## Commands and Tests

- Python compile: PASS.
- Django system check: PASS.
- Migration consistency: PASS, no changes detected.
- Focused AI tests: 21 passed.
- Full regression: 342 passed.
- Git diff check: PASS.

## Ollama Review

- Model: `llama3:latest`.
- Real local inference: yes.
- Fallback used: no.
- Decision: PASS.
- Critical findings: 0.
- High findings: 0.
- Output checksum: `75304e598ef438686d1135fc928048fdbf2e27e7894cad94877e3e9a43eeee12`.

## Final Decision

PASS

AI-00 is eligible for commit and integration. Human approval remains required before any merge to `main`, release or deployment.
