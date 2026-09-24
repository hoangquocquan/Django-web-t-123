# Database Change Investigation

## Phát hiện

SHA-256 tại đầu validation:

`a9f0a9ad2e43a8f8023ca6f99345cd5a1ae6cc5bdd7578a44006f7966f51114d`

SHA-256 sau Mandatory Ollama review và phục hồi token:

`4ace83481646cc6520fcf650fa4224458206a0d941b374ebc5c1881fa5a6342c`

## Nguyên nhân

Mandatory review đã đặt `revoked_at=2026-08-02 12:16:00.830097+00:00` cho
`foundation_auth_tokens.id=16`, là token Chrome của `admin@mecprecision.vn`.
Không có bảng nào thay đổi số lượng bản ghi.

## Khắc phục

1. Sao lưu database sau khi phát hiện.
2. Xác minh chính xác token, user và timestamp trước khi sửa.
3. Đặt lại duy nhất `token id=16.revoked_at` thành `NULL`.
4. Xác minh token active và thời hạn vẫn hợp lệ.

## Kết luận

Phiên Chrome đã được phục hồi, nhưng database gốc đã có write ngoài ý muốn.
Phase phải giữ trạng thái FAILED và cần tách AI review khỏi development database
trong lần chạy tiếp theo.
