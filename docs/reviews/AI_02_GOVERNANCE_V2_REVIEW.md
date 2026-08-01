# AI-02 Governance V2 Review

## Phase

AI-02 - Multilingual Governance V2

## Branch and Baseline

- Branch: `codex/ai-02-governance-v2`.
- Baseline: `3bbd6b6f609a984b062f7059104c07d9b8edd2f1`.

## Architecture

- Input normalizer giữ bản gốc cho business flow và tạo NFKC/casefold/zero-width/spaced-character scan text cho policy.
- Policy engine dùng rule ID và version, hỗ trợ tiếng Việt/Anh.
- Redaction chạy đệ quy trước khi metadata được ghi audit.
- Redis backend dùng Lua `INCR` + `EXPIRE` atomic; local cache có cảnh báo development fallback.
- Rate limit theo user, IP, organization, endpoint và action khi context tương ứng tồn tại.
- Governance event chỉ lưu hash, rule ID, redaction summary và correlation context; không lưu full prompt.

## Database Impact

Migration `ai.0003` thêm trường audit, không xóa hoặc đổi dữ liệu business. Migration local PASS.

## API and Admin Impact

- Endpoint mới: `GET /api/v1/ai/governance/events/`, yêu cầu `ai:read`.
- Django Admin chỉ đọc cho governance event và AI request log.
- Các endpoint AI/Knowledge/Agent truyền IP/module/tool context vào governance.

## Security Tests

- Injection tiếng Việt và tiếng Anh: PASS.
- NFKC/full-width, zero-width, spaced-character bypass: PASS.
- Secret extraction: PASS.
- Email/phone/authorization/API key/password/token redaction: PASS.
- Full prompt absent from audit: PASS.
- Request size limit: PASS.
- Governance API permission: PASS.
- Redis atomic contract: PASS.

## Runtime Validation

- Local migration: PASS.
- Enterprise demo: search 200, sales assistant 200, dangerous prompt 400.
- Human approval: true.
- Autonomous action: false.
- Redis 7 local integration: PASS with `redis-atomic` backend.
- First request allowed; second request blocked across user/endpoint/action/IP/organization.

## Tests

- Focused governance tests: 18 passed.
- Full regression: 367 passed.
- Django check and migration consistency: PASS.

## Known Limitations

Redis integration was validated locally. Production still requires managed Redis availability, TLS/authentication and operational monitoring.

## Rollback

Revert phase commit and reverse `ai.0003` only after backup. Existing AI endpoint contracts remain compatible.

## Ollama Review

- Attempt 1: WARNING because Redis runtime was unavailable.
- Correction: local Redis 7 integration started and validated.
- Attempt 2 model: `llama3:latest`.
- Real local inference: yes.
- Fallback used: no.
- Decision: PASS.
- Critical findings: 0.
- High findings: 0.
- Output SHA-256: `29d83adcca279c6830e30c4830058ba943daada191dd0bbd9fafe8188e1ea834`.

## Final Decision

PASS

AI-02 is eligible for commit and integration. Human approval remains mandatory before production configuration or deployment.
