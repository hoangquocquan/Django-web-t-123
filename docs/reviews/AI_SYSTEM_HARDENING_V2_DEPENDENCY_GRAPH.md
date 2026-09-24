# AI System Hardening V2 Dependency Graph

## Program Flow

```text
AI-00
  |
  +--> AI-01 Real Embedding and Vector Search
  |
  +--> AI-02 Governance V2
          |
          +-- AI-01 + AI-02 --> AI-03 Grounded Sales Synthesis
                                  |
                                  v
                                AI-04 Safe Agent Controller
                                  |
                                  v
                                AI-05 Mandatory Ollama Review
                                  |
                                  v
                                AI-06 Final Integration
```

## Execution Decision

AI-01 và AI-02 được chạy tuần tự. Cả hai cùng cần thay đổi Django settings, test fixture và các service AI dùng chung nên chạy song song sẽ làm giảm khả năng audit và tăng rủi ro conflict.

| Phase | Depends on | Blocking output |
| --- | --- | --- |
| AI-00 | Baseline repository | Environment, model and test inventory |
| AI-01 | AI-00 | Embedding provider, vector contract, metadata |
| AI-02 | AI-00, AI-01 settings contract | Normalization, policy, redaction, rate limiting |
| AI-03 | AI-01, AI-02 | Grounded facts and governed synthesis |
| AI-04 | AI-03 | Structured output and authorization foundation |
| AI-05 | AI-01 through AI-04 | Actual phase diff, test and security evidence |
| AI-06 | AI-01 through AI-05 | All commits, migrations, evidence and reviews |

## Tasks Run in Parallel

Không có task sửa code chạy song song trong cùng worktree. Các lệnh kiểm tra read-only độc lập được chạy song song.

## Tasks Serialized

Tất cả task tạo migration, sửa settings, URL registry, shared test fixture và AI service được tuần tự hóa.
