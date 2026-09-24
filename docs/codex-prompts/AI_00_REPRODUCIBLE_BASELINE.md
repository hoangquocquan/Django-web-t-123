# AI-00 - Discovery and Reproducible Baseline

## Objective

Thiết lập baseline có thể tái lập cho chương trình AI System Hardening V2 trước khi thay đổi code ứng dụng.

## Existing Problem

Hệ thống đã có Django AI, Knowledge/RAG, AI Sales, AI Agent và AI Factory nhưng mức độ sẵn sàng của embedding, review bắt buộc, Docker, Redis và vector backend chưa được xác minh cùng một chuẩn evidence.

## Scope

- Kiểm tra Git, Python, Django, database, cache, Docker và Ollama.
- Xác định generation model và embedding model chạy local.
- Phân loại test và dependency giữa AI-00 đến AI-06.
- Ghi lại file ngoài phạm vi mà không sửa hoặc commit chúng.
- Tạo evidence và review baseline.

## Out of Scope

- Không thay đổi business logic.
- Không tạo migration.
- Không merge `main`, push remote hoặc deploy.
- Không bật autonomous write action.

## Allowed Paths

- `docs/codex-prompts/AI_SYSTEM_HARDENING_V2_MASTER.md`
- `docs/codex-prompts/AI_00_REPRODUCIBLE_BASELINE.md`
- `docs/reviews/AI_SYSTEM_HARDENING_V2_*`
- `docs/reviews/AI_00_REPRODUCIBLE_BASELINE_*`
- `docs/evidence/ai-00/`

## Dependencies

- Baseline commit `e0af74650ca3670589f482ff7fe44804d6ff41f7`.
- Python 3.12.10 và Django 5.2.16.
- Ollama local tại `http://localhost:11434`.

## File Ownership

AI-00 chỉ sở hữu tài liệu và evidence kể trên. Ba file ZIP chưa được theo dõi thuộc người dùng và không được đưa vào commit.

## Database Impact

Không thay đổi schema hoặc dữ liệu.

## Security Impact

Không lưu prompt đầy đủ, secret, token, database runtime hoặc backup trong commit. Mọi bước giữ `human_approval_required = true` và `autonomous_action = false`.

## Acceptance Criteria

- Baseline commit, branch và worktree state được ghi nhận.
- Django check PASS.
- Ollama generation và embedding chạy thật.
- Dependency graph và file ownership được tạo.
- Docker blocker được ghi là blocker môi trường, không báo PASS giả.
- Ollama review dùng diff thật và trả PASS, không fallback.

## Required Tests

```text
python django_backend/manage.py check
python django_backend/manage.py makemigrations --check --dry-run
pytest tests/test_ai_ollama.py tests/test_ollama_real_inference.py tests/test_ai_enterprise_governance.py
git diff --check
```

## Rollback Plan

Xóa commit AI-00 bằng một revert commit trên branch tích hợp. Không reset hard và không xóa file người dùng.

## Planned Commit

`docs(ai): establish hardening v2 reproducible baseline`
