# Demo Database AI And RAG Report

## AI Sales

Test tạo một `SalesLead` trong Django test database rồi gọi
`SalesAssistantService.handle("lead_analysis", ...)`.

- Lead được đọc lại từ ORM theo `lead_id`.
- Tên công ty trong kết quả khớp database.
- `human_approval_required = true`.
- `autonomous_action = false`.
- Không gửi email và không tự cập nhật CRM.

Kết quả: PASS.

## Knowledge/RAG

Database demo có:

- 105 documents.
- 105 chunks.
- 105 embeddings.
- 0 document thiếu chunk.
- 0 chunk thiếu embedding.

Các regression test hiện hữu cho knowledge assistant, document intelligence,
vector search và Ollama fallback đều PASS trong bộ `554 passed`.

## Giới hạn

Focused phase không gọi model để thay đổi dữ liệu. Mandatory Ollama chỉ làm
review cục bộ, không được phép gửi dữ liệu ra dịch vụ AI bên ngoài hoặc tự phê
duyệt production.
