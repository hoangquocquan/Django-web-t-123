# AI-01 - Real Ollama Embedding and Vector Search

## Objective

Thay embedding hash trong runtime bằng semantic embedding thật qua Ollama local và tạo contract vector store có thể nâng cấp sang pgvector.

## Scope

- `EmbeddingProvider`, `OllamaEmbeddingProvider` và development fallback rõ tên.
- Batch embedding, timeout, retry và validate kích thước vector.
- Metadata provider/model/dimension/version/content hash/indexed time.
- VectorStore contract và Django JSON development fallback.
- Reindex an toàn, dry run, resume, single document và batch size.
- Test lỗi provider, tính idempotent, model change và retrieval Việt/Anh.

## Dependencies

- AI-00 PASS và commit `dbea8b2`.
- Ollama generation model `llama3:latest`.
- Ollama embedding model `nomic-embed-text:latest`, 768 chiều.

## DO NOT

- Không dùng external AI.
- Không xóa index cũ trước khi embedding mới thành công.
- Không mô tả JSONField fallback là production vector search.
- Không commit database runtime.

## Database Impact

Migration bổ sung metadata cho `knowledge_embeddings`; không xóa cột hoặc dữ liệu cũ.

## Security Impact

Không log toàn bộ tài liệu hoặc vector. Error chỉ ghi thông tin kỹ thuật tối thiểu.

## Acceptance Criteria

- Ollama embedding thật và batch hoạt động.
- Model missing/offline/empty/dimension mismatch được xử lý.
- Reindex rollback an toàn và idempotent.
- Model/provider/content change kích hoạt reindex.
- Search chỉ so sánh vector cùng provider và dimension.
- Focused, regression và Ollama review PASS.

## Rollback

Revert commit AI-01. Migration chỉ thêm field có default nên có thể reverse mà không ảnh hưởng bảng khác; sao lưu database trước rollback production.

## Commit

`feat(ai): implement real ollama embeddings and vector retrieval`
