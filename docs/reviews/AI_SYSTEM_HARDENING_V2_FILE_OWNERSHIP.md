# AI System Hardening V2 File Ownership

| Phase | Primary paths | Shared paths requiring serialization |
| --- | --- | --- |
| AI-00 | `docs/evidence/ai-00`, baseline/review documents | None |
| AI-01 | `apps/knowledge/services`, knowledge models/migrations, reindex command | `config/settings/base.py`, knowledge tests |
| AI-02 | `apps/ai/services/governance*`, AI models/migrations | `config/settings/base.py`, AI views/tests |
| AI-03 | AI Sales synthesis services and business UI | Knowledge search, AI governance, sales tests |
| AI-04 | `apps/ai_agent/services`, agent models/migrations | AI Agent views/URLs/tests |
| AI-05 | `ai-review`, `ai-factory`, n8n gate scripts | Review config and shared evidence files |
| AI-06 | Final reviews and integration evidence | Whole-system test/runtime configuration |

## Protected Existing Files

- `docs.zip`
- `docs/reviews.zip`
- `mecprecision.zip`

Các file trên chưa được Git theo dõi, thuộc ngoài scope và không được sửa hoặc commit.

## Ownership Rule

Chỉ một phase được sửa shared settings, URL registry hoặc migration package tại một thời điểm. Không phase nào được xóa legacy code, database hoặc lịch sử Git.
