# AI-02 - AI Governance V2

## Objective

Nâng governance thành policy đa ngôn ngữ có normalization, PII/secret redaction, rate limit phân tán và audit versioning.

## Scope

- NFKC, casefold, zero-width removal, whitespace và spaced-character detection.
- Policy rule có ID/version, tiếng Việt và tiếng Anh.
- Redaction email, phone, authorization, API key, password và token.
- Redis Lua atomic rate limit theo user/IP/organization/endpoint/action.
- Development cache fallback có warning rõ ràng.
- Audit correlation ID, role/module/tool/source, policy version và matched rule IDs.
- API/Admin chỉ đọc cho governance events.

## Dependencies

- AI-01 integration commit `3bbd6b6`.

## DO NOT

- Không lưu full prompt trong governance event.
- Không lưu authorization/token/password.
- Không để AI tự gửi email, duyệt báo giá, cập nhật CRM hoặc deploy.
- Không mô tả local cache là distributed production rate limit.

## Database Impact

Migration chỉ thêm trường audit vào `ai_governance_events`.

## Acceptance Criteria

- Injection VI/EN và Unicode bypass bị chặn.
- PII/secret không xuất hiện trong metadata/audit.
- Redis backend dùng thao tác atomic.
- Local fallback cảnh báo rõ.
- Governance API cần permission.
- Existing API compatibility và regression PASS.

## Rollback

Revert phase commit và reverse migration sau khi backup. Các field mới không thay đổi dữ liệu business.

## Commit

`feat(ai): add multilingual governance v2 controls`
