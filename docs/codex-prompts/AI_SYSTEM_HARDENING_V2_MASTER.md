# CODEX MASTER PROMPT

## AI SYSTEM HARDENING V2 — FULL MULTI-PHASE EXECUTION PIPELINE

Bạn đang làm việc trực tiếp trên repository **MEC Precision Platform**.

Bạn đồng thời đảm nhận các vai trò:

* Principal Software Architect
* Senior Django Engineer
* AI/RAG Engineer
* Ollama Integration Engineer
* DevOps Engineer
* QA Automation Engineer
* Security Reviewer
* Git Release Manager
* Technical Documentation Engineer

## MỤC TIÊU

Thực hiện toàn bộ chương trình nâng cấp hệ thống AI theo một lần khởi động, gồm:

```text
AI-00 — Discovery and Reproducible Baseline
AI-01 — Real Ollama Embedding and Vector Search
AI-02 — AI Governance V2
AI-03 — Grounded Sales AI Synthesis
AI-04 — Safe Structured AI Agent Controller
AI-05 — Mandatory Ollama Phase Review
AI-06 — Final Integration and Handover
```

Codex phải:

* Tự kiểm tra repository thật.
* Tạo specification cho từng phase.
* Phân tích dependency giữa phase và task.
* Chạy song song những task thực sự không phụ thuộc.
* Dùng branch/worktree riêng cho các task chạy song song.
* Viết code, migration và test.
* Chạy validation thực tế.
* Dùng Ollama để review độc lập.
* Sửa lỗi có giới hạn.
* Tạo evidence.
* Tạo file review.
* Commit toàn bộ thay đổi vào Git.
* Ghi commit hash vào báo cáo.
* Chỉ chuyển phase khi đầy đủ gate.
* Dừng ở human approval trước merge/release.

Không được chỉ tạo tài liệu hoặc code giả lập mà không triển khai chức năng thật.

---

# 1. EXECUTION MODE

```text
MODE = SEQUENTIAL_PHASES_WITH_PARALLEL_INDEPENDENT_TASKS
AUTO_CONTINUE_AFTER_VALIDATED_PHASE = TRUE
AUTO_MERGE_MAIN = FALSE
AUTO_DEPLOY = FALSE
MAX_CORRECTION_ATTEMPTS_PER_PHASE = 3
OLLAMA_REVIEW_REQUIRED = TRUE
HUMAN_APPROVAL_REQUIRED_BEFORE_MAIN_MERGE = TRUE
```

Prompt này cho phép Codex tự chạy liên tiếp AI-00 đến AI-06 trên branch phát triển riêng.

Việc tự chuyển phase chỉ được phép khi:

* Code đã được triển khai.
* Test bắt buộc đã PASS.
* Migration validation đã PASS.
* Ollama review thật đã PASS.
* Không còn Critical hoặc High finding.
* Evidence đã được lưu.
* Review file đã được tạo.
* Commit Git đã được tạo thành công.
* Working tree không có thay đổi ngoài phạm vi không được giải thích.

Human approval vẫn bắt buộc trước:

* Merge vào `main`.
* Push remote nếu chưa được cho phép.
* Tạo release tag.
* Deploy staging.
* Deploy production.
* Bật autonomous write action.

---

# 2. NGUYÊN TẮC AN TOÀN BẮT BUỘC

Không được:

* Tự merge vào `main`.
* Tự deploy production.
* Dùng `git push --force`.
* Dùng `git push --force-with-lease`.
* Xóa hoặc sửa lịch sử Git đã chia sẻ.
* Dùng `git reset --hard` để loại bỏ thay đổi của người dùng.
* Dùng `git clean -xfd` khi chưa kiểm tra toàn bộ file bị ảnh hưởng.
* Xóa legacy code khi chưa có bằng chứng không còn dependency.
* Xóa migration cũ.
* Thay đổi database lớn ngoài phạm vi phase.
* Commit database runtime, backup, cache hoặc ZIP.
* Commit `.env`, token, password, API key hoặc secret.
* Báo PASS khi command thực tế chưa chạy.
* Tạo bằng chứng giả.
* Bỏ qua test lỗi để chuyển phase.
* Dùng fallback review để tạo trạng thái PASS.
* Cho nhiều worker sửa cùng một worktree.
* Cho nhiều worker đồng thời sửa cùng một file.
* Cho nhiều phase đồng thời tạo migration trong cùng Django app.
* Cho AI tự gửi email.
* Cho AI tự duyệt quotation.
* Cho AI tự cập nhật CRM.
* Cho AI tự deploy.
* Cho AI tự thực hiện database write nguy hiểm.
* Cho Codex tự phê duyệt kết quả cuối của chính mình.

Phải giữ nguyên nguyên tắc:

```text
human_approval_required = True
autonomous_action = False
```

---

# 3. KIỂM TRA REPOSITORY BAN ĐẦU

Trước khi sửa bất kỳ file nào, chạy:

```bash
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git status --short
git remote -v
git log -10 --oneline --decorate
```

Ghi lại:

```text
Repository root
Current branch
Baseline commit
Current working-tree state
Configured remotes
Python version
Django version
Database configuration
Redis configuration
Ollama endpoint
Available Ollama models
Docker availability
```

Không được tự động discard thay đổi đang tồn tại.

Nếu working tree có thay đổi:

1. Xác định thay đổi của người dùng.
2. Không sửa đè.
3. Ghi chúng vào baseline report.
4. Chỉ tiếp tục khi có thể cô lập phần triển khai bằng branch/worktree.
5. Không đưa thay đổi không liên quan vào commit phase.

Tạo:

```text
docs/codex-prompts/AI_SYSTEM_HARDENING_V2_MASTER.md
docs/reviews/AI_SYSTEM_HARDENING_V2_BASELINE.md
docs/reviews/AI_SYSTEM_HARDENING_V2_DEPENDENCY_GRAPH.md
docs/reviews/AI_SYSTEM_HARDENING_V2_FILE_OWNERSHIP.md
docs/reviews/AI_SYSTEM_HARDENING_V2_PHASE_STATUS.md
docs/reviews/AI_SYSTEM_HARDENING_V2_COMMIT_MANIFEST.md
```

---

# 4. BRANCH VÀ WORKTREE

## 4.1 Integration branch

Tạo branch tích hợp từ baseline hiện tại:

```text
codex/ai-system-hardening-v2
```

Không tạo branch từ một commit cũ nếu working branch hiện tại có code mới hơn cần giữ.

## 4.2 Phase branch

Mỗi phase dùng branch riêng:

```text
codex/ai-00-baseline
codex/ai-01-vector-search
codex/ai-02-governance-v2
codex/ai-03-sales-synthesis
codex/ai-04-agent-controller
codex/ai-05-mandatory-review
codex/ai-06-final-integration
```

## 4.3 Task worktree

Task chạy song song phải dùng:

```text
worktrees/<phase>/<task-slug>/
```

Mỗi task phải có:

* Branch riêng.
* Worktree riêng.
* Allowed path riêng.
* Task specification riêng.
* Test command riêng.
* Commit riêng.
* Evidence riêng.

Không cho hai task chia sẻ cùng working directory.

---

# 5. QUY TẮC CHẠY SONG SONG

Trước mỗi phase, tạo dependency graph và file ownership matrix.

Một task chỉ được chạy song song khi đáp ứng toàn bộ:

1. Không phụ thuộc output chưa hoàn thành của task khác.
2. Không sửa cùng file.
3. Không sửa cùng migration package.
4. Không cùng sửa Django settings.
5. Không cùng sửa URL registry hoặc app registry.
6. Không cùng sửa một test fixture dùng chung.
7. Không thay đổi cùng database model.
8. Không dùng chung worktree.
9. Có acceptance criteria độc lập.
10. Có thể test độc lập.

Ví dụ có thể chạy song song:

```text
Embedding provider implementation
Vector-store abstraction
Retrieval benchmark dataset
Documentation
```

Chỉ khi các task trên không sửa cùng file.

Ví dụ không được chạy song song:

```text
Task A sửa ai/models.py
Task B cũng sửa ai/models.py
```

```text
Task A tạo migration 0003 trong app knowledge
Task B cũng tạo migration trong app knowledge
```

```text
Task A sửa config/settings/base.py
Task B cũng sửa config/settings/base.py
```

Khi phát hiện conflict tiềm năng:

```text
PARALLEL → SERIALIZED
```

Ghi lý do vào:

```text
docs/reviews/AI_SYSTEM_HARDENING_V2_DEPENDENCY_GRAPH.md
```

Codex phải ưu tiên tính đúng và auditability hơn tốc độ.

---

# 6. MÔ HÌNH DEPENDENCY TOÀN CHƯƠNG TRÌNH

Dependency mặc định:

```text
AI-00
  |
  +-------------------+
  |                   |
  v                   v
AI-01               AI-02
  |                   |
  +---------+---------+
            |
            v
          AI-03
            |
            v
          AI-04
            |
            v
          AI-05
            |
            v
          AI-06
```

AI-01 và AI-02 chỉ được chạy song song khi kiểm tra source cho thấy:

* Không sửa chung file.
* Không tạo migration cùng app.
* Không cùng sửa settings.
* Không phụ thuộc shared utility chưa tồn tại.
* Có worktree riêng.

Nếu không thỏa mãn, thực hiện:

```text
AI-01 → AI-02
```

AI-03 chỉ bắt đầu khi AI-01 và AI-02 đã tích hợp và PASS.

AI-04 chỉ bắt đầu khi structured output, governance và tool authorization foundation đã sẵn sàng.

AI-05 chỉ bắt đầu sau khi tất cả reviewer và execution pipeline cần kiểm tra đã tồn tại.

AI-06 chỉ bắt đầu khi AI-01 đến AI-05 đều có commit, review và evidence hợp lệ.

---

# 7. QUY TẮC CHUYỂN PHASE

## 7.1 State machine

Mỗi phase phải đi qua:

```text
DRAFT
→ SPECIFIED
→ READY
→ EXECUTING
→ INTEGRATING
→ VALIDATING
→ AI_REVIEWING
→ CORRECTION_REQUIRED
→ REVALIDATING
→ COMMITTED
→ READY_FOR_NEXT_PHASE
```

Trạng thái lỗi:

```text
BLOCKED_BY_DEPENDENCY
BLOCKED_BY_ENVIRONMENT
BLOCKED_REQUIRES_HUMAN
FAILED
```

Trạng thái cuối:

```text
WAITING_FOR_HUMAN_APPROVAL
```

## 7.2 Điều kiện từ DRAFT sang SPECIFIED

Chỉ được chuyển khi đã tạo:

```text
docs/codex-prompts/<PHASE_NAME>.md
```

Specification phải có:

* Objective.
* Existing problem.
* Scope.
* Out of scope.
* Allowed paths.
* Dependencies.
* File ownership.
* Database impact.
* Security impact.
* Acceptance criteria.
* Required tests.
* Rollback plan.
* Commit message dự kiến.

## 7.3 Điều kiện từ SPECIFIED sang READY

Chỉ được chuyển khi:

* Dependency đã được xác minh.
* Allowed paths không xung đột.
* Baseline commit đã ghi nhận.
* Worktree đã tạo.
* Không có unresolved Git conflict.
* Môi trường đủ để thực thi task.

## 7.4 Điều kiện từ EXECUTING sang INTEGRATING

Chỉ được chuyển khi:

* Tất cả task bắt buộc hoàn thành.
* Mỗi task có commit.
* Không còn thay đổi chưa giải thích.
* Task output đúng phạm vi.
* Không có secret hoặc dữ liệu runtime trong commit.

## 7.5 Điều kiện từ INTEGRATING sang VALIDATING

Chỉ được chuyển khi:

* Các task commit đã được tích hợp.
* Conflict đã được giải quyết rõ ràng.
* Migration graph hợp lệ.
* `git diff --check` PASS.
* Không có file ngoài scope bị sửa.
* Integration branch compile được.

## 7.6 Điều kiện từ VALIDATING sang AI_REVIEWING

Bắt buộc PASS:

```text
Python compile check
Django system check
Migration consistency check
Focused unit tests
Focused integration tests
Security-focused tests
Relevant regression tests
Full regression tests
```

Nếu repository có các tool tương ứng, chạy thêm:

```text
ruff
format check
mypy hoặc pyright
bandit
pip-audit
Docker configuration validation
```

Tool không có phải ghi `NOT_RUN`, không được ghi PASS.

## 7.7 Điều kiện từ AI_REVIEWING sang COMMITTED

Bắt buộc:

* Ollama đang chạy thật.
* Model review tồn tại.
* Review sử dụng actual Git diff.
* Review output đúng JSON schema.
* Decision là `PASS`.
* Critical findings = 0.
* High findings = 0.
* Không dùng fallback review.
* Review evidence đã được lưu.
* Review report đã được tạo.

## 7.8 Điều kiện từ COMMITTED sang READY_FOR_NEXT_PHASE

Bắt buộc:

* Phase commit tồn tại.
* Commit hash được ghi trong manifest.
* Working tree sạch hoặc chỉ còn file được giải thích.
* Evidence có checksum.
* Review file tham chiếu đúng commit.
* Test summary tham chiếu đúng commit.
* Rollback command đã được ghi.
* Phase status được cập nhật.

Chỉ sau đó mới được chuyển phase.

---

# 8. QUY TẮC DỪNG PIPELINE

Dừng ngay toàn bộ pipeline khi:

* Baseline không xác định được.
* Repository có unresolved conflict.
* Không thể bảo toàn thay đổi hiện có.
* Migration conflict không giải quyết an toàn.
* Focused test fail sau ba vòng sửa.
* Regression test fail sau ba vòng sửa.
* Django check fail sau ba vòng sửa.
* Ollama bắt buộc nhưng không hoạt động.
* Model review không tồn tại.
* Review trả invalid JSON.
* Review chỉ chạy fallback.
* Critical finding chưa xử lý.
* High finding chưa xử lý.
* File ngoài allowed paths bị sửa mà không có lý do hợp lệ.
* Không thể tạo phase commit sạch.
* Phát hiện secret trong staged files.
* Phát hiện database runtime hoặc backup trong staged files.
* Phát hiện hành động autonomous nguy hiểm.
* Dependency chưa hoàn thành.
* Một task vượt quá retry limit.

Trạng thái:

```text
BLOCKED_REQUIRES_HUMAN
```

Không được:

* Bỏ qua phase lỗi.
* Chạy phase phụ thuộc.
* Đánh dấu pipeline COMPLETE.
* Tự merge.
* Tự deploy.

---

# 9. CORRECTION LOOP

Khi test hoặc review lỗi:

```text
Collect failure
→ Classify root cause
→ Create correction task
→ Codex sửa trong đúng worktree
→ Run focused test
→ Run integration test
→ Run regression test
→ Run Ollama review lại
```

Tối đa:

```text
3 correction attempts per phase
```

Mỗi attempt phải lưu:

```text
Attempt number
Failure summary
Root cause
Files changed
Commands executed
Test result
Review result
Commit hash
```

Không được lặp lại cùng một patch không hiệu quả.

Sau ba lần không đạt:

```text
BLOCKED_REQUIRES_HUMAN
```

---

# 10. OLLAMA PREFLIGHT

Trước AI-01, chạy kiểm tra Ollama thật.

Xác định endpoint từ settings hoặc environment.

Kiểm tra:

```text
Ollama endpoint reachable
Generation model available
Embedding model available
Review model available
Model names recorded
Timeout configuration available
```

Lưu kết quả:

```text
docs/evidence/ai-00/ollama-health.json
docs/evidence/ai-00/ollama-models.json
```

Không lưu secret.

Khi `OLLAMA_REVIEW_REQUIRED=true`:

```text
Ollama unavailable = BLOCKED
Review model missing = BLOCKED
Timeout = BLOCKED
Malformed output = BLOCKED
Fallback = BLOCKED
```

---

# 11. PHASE AI-00 — DISCOVERY AND REPRODUCIBLE BASELINE

## Mục tiêu

Tạo baseline sạch, có thể tái lập và xác định chính xác source hiện tại.

## Thực hiện

* Kiểm tra Git.
* Kiểm tra app AI, Knowledge, AI Agent, AI Factory và n8n.
* Kiểm tra Docker/settings.
* Kiểm tra database và cache config.
* Kiểm tra dependency files.
* Kiểm tra migration graph.
* Kiểm tra test discovery.
* Kiểm tra Ollama.
* Kiểm tra file runtime, database, backup và ZIP lồng.
* Không tự xóa dữ liệu.
* Tạo release manifest.
* Phân loại test:

  * Product tests.
  * Evidence/contract tests.
  * Integration tests.
  * E2E tests.
  * Security tests.

## File bắt buộc

```text
docs/codex-prompts/AI_00_REPRODUCIBLE_BASELINE.md
docs/reviews/AI_00_REPRODUCIBLE_BASELINE_REVIEW.md
docs/reviews/AI_00_REPRODUCIBLE_BASELINE_RESULT.json
docs/evidence/ai-00/
```

## Acceptance criteria

* Baseline commit xác định.
* Git state được bảo toàn.
* Ollama health được xác minh.
* Dependency graph được tạo.
* File ownership được tạo.
* Test command thật được xác định.
* Không có secret trong staged files.
* Không có runtime database được commit.
* Baseline report hoàn chỉnh.

## Commit

```text
docs(ai): establish hardening v2 reproducible baseline
```

---

# 12. PHASE AI-01 — REAL OLLAMA EMBEDDING AND VECTOR SEARCH

## Mục tiêu

Thay hash embedding bằng semantic embedding chạy thật qua Ollama và xây vector retrieval có thể mở rộng.

## Thành phần

### Embedding provider

Tạo abstraction:

```python
class EmbeddingProvider:
    def embed_text(self, text: str) -> list[float]:
        ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        ...

    def health_check(self) -> dict:
        ...
```

Triển khai:

```text
OllamaEmbeddingProvider
```

Yêu cầu:

* Configurable base URL.
* Configurable model.
* Timeout.
* Retry có giới hạn.
* Batch support.
* Empty-vector validation.
* Dimension validation.
* Không log full document.

### Vector store

Tạo abstraction:

```python
class VectorStore:
    def upsert(self, ...):
        ...

    def search(self, ...):
        ...

    def delete(self, ...):
        ...

    def health_check(self, ...):
        ...
```

Ưu tiên PostgreSQL + pgvector khi phù hợp.

Fallback development phải:

* Được đặt tên rõ là fallback.
* Có warning.
* Không được mô tả là production vector search.

### Metadata

Lưu:

```text
provider
model
dimension
embedding version
content hash
created timestamp
indexed timestamp
```

### Reindex command

Tạo management command:

```bash
python django_backend/manage.py reindex_knowledge_embeddings
```

Hỗ trợ:

* All documents.
* Single document.
* Batch size.
* Dry run.
* Resume.
* Error summary.
* Không xóa embedding cũ trước khi embedding mới thành công.

### Benchmark

Tạo benchmark:

* Tiếng Việt có dấu.
* Tiếng Việt không dấu.
* Tiếng Anh.
* Từ đồng nghĩa.
* Cách diễn đạt khác.
* Câu không có context.

## Task có thể chạy song song

Chỉ khi không xung đột file:

```text
AI-01-A: Ollama embedding provider
AI-01-B: Vector-store abstraction
AI-01-C: Retrieval benchmark and tests
AI-01-D: Documentation and operational runbook
```

Integration task phải chạy sau tất cả.

## Test bắt buộc

* Ollama embedding hợp lệ.
* Ollama offline.
* Model missing.
* Empty vector.
* Dimension mismatch.
* Batch failure.
* Reindex idempotent.
* Model change triggers reindex.
* Vietnamese semantic retrieval.
* Citation correctness.
* No-context behavior.
* Fallback warning.
* Vector backend contract.

## File bắt buộc

```text
docs/codex-prompts/AI_01_REAL_EMBEDDING_VECTOR_SEARCH.md
docs/reviews/AI_01_REAL_EMBEDDING_VECTOR_SEARCH_REVIEW.md
docs/reviews/AI_01_REAL_EMBEDDING_VECTOR_SEARCH_RESULT.json
docs/evidence/ai-01/
```

## Commit

```text
feat(ai): implement real ollama embeddings and vector retrieval
```

---

# 13. PHASE AI-02 — AI GOVERNANCE V2

## Mục tiêu

Nâng governance thành policy đa ngôn ngữ, có normalization, redaction, distributed rate limit và audit versioning.

## Thành phần

### Input normalization

* Unicode NFKC.
* Case folding.
* Zero-width removal.
* Whitespace normalization.
* Spaced-character detection.
* Request-size limit.
* Giữ bản gốc cho business flow.
* Dùng normalized form cho policy scan.

### Multilingual policy

Hỗ trợ tối thiểu tiếng Việt và tiếng Anh:

* Bỏ qua chỉ dẫn trước.
* Tiết lộ system prompt.
* Tiết lộ secret/token/password.
* Trích xuất dữ liệu nhạy cảm.
* Tự phê duyệt.
* Tự gửi email.
* Tự deploy.
* Xóa database.
* Hành động nghiệp vụ nguy hiểm.
* Injection trong tài liệu RAG.

Policy phải có cấu trúc và version, không chỉ là danh sách regex hard-coded.

### Policy context

Nhận:

```text
user
role
organization
module
endpoint
action
tool
request source
policy version
```

### PII/secret redaction

Redact:

* Email.
* Phone.
* Authorization header.
* Access token.
* API key.
* Password.
* Reset token.
* Secret-like values.

Áp dụng cho:

* AI logs.
* Governance metadata.
* Error logs.
* Prompt preview.
* Review evidence.

### Redis distributed rate limit

Hỗ trợ:

* User.
* IP.
* Organization.
* Endpoint/action.
* Time window.
* Atomic increment.
* Multiple workers.
* Restart-safe behavior.

### Audit

Lưu:

```text
policy version
model version
prompt template version
normalized request hash
redaction summary
matched rule IDs
correlation ID
organization ID
tool name
```

Không lưu full prompt trong governance event.

## Task có thể chạy song song

Chỉ khi file ownership không xung đột:

```text
AI-02-A: Normalization and policy configuration
AI-02-B: Redaction service
AI-02-C: Redis rate-limit backend
AI-02-D: Governance admin/API
AI-02-E: Multilingual security tests
```

## Test bắt buộc

* Injection tiếng Việt.
* Injection tiếng Anh.
* Unicode bypass.
* Zero-width bypass.
* Spaced-character bypass.
* Secret extraction.
* PII redaction.
* Authorization header redaction.
* Role/module policy.
* Redis atomic rate limit.
* Development fallback warning.
* Audit không chứa full prompt.
* Governance dashboard permission.

## File bắt buộc

```text
docs/codex-prompts/AI_02_GOVERNANCE_V2.md
docs/reviews/AI_02_GOVERNANCE_V2_REVIEW.md
docs/reviews/AI_02_GOVERNANCE_V2_RESULT.json
docs/evidence/ai-02/
```

## Commit

```text
feat(ai): add multilingual governance v2 controls
```

---

# 14. PHASE AI-03 — GROUNDED SALES AI SYNTHESIS

## Mục tiêu

Giữ scoring và business facts deterministic; dùng Ollama để tạo phần giải thích, tóm tắt và email draft có grounding.

## Nguyên tắc

Ollama không được:

* Thay đổi lead score.
* Tự cập nhật CRM.
* Tự gửi email.
* Tự duyệt quotation.
* Tự giảm giá.
* Tự tạo order.
* Tự chuyển pipeline.

### Facts layer

Tạo structured facts:

```json
{
  "lead_facts": {},
  "score_facts": {},
  "crm_facts": {},
  "sales_facts": {},
  "knowledge_sources": []
}
```

### Ollama output schema

```json
{
  "summary": "",
  "reasoning_summary": [],
  "recommended_next_steps": [],
  "draft_email": {
    "subject": "",
    "body": ""
  },
  "risks": [],
  "source_ids": [],
  "human_approval_required": true,
  "autonomous_action": false
}
```

### Validation

* JSON hợp lệ.
* Schema hợp lệ.
* Source tồn tại.
* Không thay đổi score.
* Không hallucinate fact.
* Không chứa action bị cấm.
* Luôn human approval.
* Không tự gửi email.

### Fallback

Khi Ollama lỗi:

* Retry có giới hạn.
* Sau đó dùng deterministic fallback.
* Ghi `generation_mode=fallback`.
* Không được giả rằng Ollama đã sinh thành công.

### UI

Chuyển raw dictionary thành card:

* Lead summary.
* Score explanation.
* Recommended next steps.
* Risks.
* Draft email.
* Sources.
* Human approval notice.

## Task có thể chạy song song

```text
AI-03-A: Facts and deterministic scoring layer
AI-03-B: Ollama synthesis and schema validation
AI-03-C: Business UI structured cards
AI-03-D: Tests and fixtures
```

Chỉ chạy song song nếu không sửa chung service/template/test.

## Test bắt buộc

* Score không bị model thay đổi.
* Valid JSON.
* Invalid JSON.
* Missing field.
* Unknown source.
* Hallucinated source.
* Ollama offline.
* Deterministic fallback.
* Dangerous output blocked.
* Email remains draft.
* No auto-send.
* UI không hiển thị raw dict.
* PII không cần thiết không được log.

## File bắt buộc

```text
docs/codex-prompts/AI_03_GROUNDED_SALES_SYNTHESIS.md
docs/reviews/AI_03_GROUNDED_SALES_SYNTHESIS_REVIEW.md
docs/reviews/AI_03_GROUNDED_SALES_SYNTHESIS_RESULT.json
docs/evidence/ai-03/
```

## Commit

```text
feat(ai-sales): add grounded ollama sales synthesis
```

---

# 15. PHASE AI-04 — SAFE STRUCTURED AI AGENT CONTROLLER

## Mục tiêu

Thay keyword-based simulated agent bằng structured planner và read-only tool controller.

## Tool registry

Mỗi tool khai báo:

```text
name
description
input schema
output schema
required permission
risk level
read only
timeout
allowed modules
audit required
```

Read-only tool có thể gồm:

* Knowledge search.
* Customer summary.
* Lead summary.
* Sales pipeline summary.
* Inventory summary.
* System health.

Cấm trong phase này:

* Arbitrary shell.
* Arbitrary SQL.
* Database write.
* File write ngoài evidence/workspace.
* Email send.
* Quotation approval.
* Deployment.
* Data deletion.

## Structured plan

```json
{
  "goal": "",
  "steps": [
    {
      "step": 1,
      "tool": "",
      "arguments": {},
      "reason": ""
    }
  ],
  "final_response_requirements": [],
  "requires_human_approval": false
}
```

Validate:

* Tool tồn tại.
* User có permission.
* Arguments đúng schema.
* Không vượt max steps.
* Không gọi tool nguy hiểm.
* Không loop vô hạn.

## Execution state

```text
PLANNED
VALIDATING
EXECUTING
TOOL_FAILED
SYNTHESIZING
COMPLETED
BLOCKED
FAILED
```

## Audit

Mỗi tool call lưu:

```text
correlation ID
user
permission
input hash
output summary
latency
status
error
policy decision
```

## Limits

* Max steps.
* Max tool calls.
* Per-tool timeout.
* Total timeout.
* Max context.
* Retry limit.

## Task có thể chạy song song

```text
AI-04-A: Tool registry and permission layer
AI-04-B: Structured planner and schema
AI-04-C: Execution controller and audit
AI-04-D: Safe read-only tools
AI-04-E: Agent security tests
```

Không chạy song song khi cùng sửa registry/controller chung.

## Test bắt buộc

* Unknown tool.
* Missing permission.
* Invalid arguments.
* Timeout.
* Tool exception.
* Max-step limit.
* Shell request.
* Database-write request.
* Email-send request.
* Dangerous tool request.
* Audit per tool.
* Final response grounded in actual tool output.
* Partial failure does not hallucinate.

## File bắt buộc

```text
docs/codex-prompts/AI_04_SAFE_AGENT_CONTROLLER.md
docs/reviews/AI_04_SAFE_AGENT_CONTROLLER_REVIEW.md
docs/reviews/AI_04_SAFE_AGENT_CONTROLLER_RESULT.json
docs/evidence/ai-04/
```

## Commit

```text
feat(ai-agent): add safe structured read-only agent controller
```

---

# 16. PHASE AI-05 — MANDATORY OLLAMA PHASE REVIEW

## Mục tiêu

Không cho AI Factory hoặc n8n đánh dấu phase thành công khi Ollama review thật chưa chạy.

## Cấu hình

```text
AI_REVIEW_REQUIRED=true
AI_REVIEW_MODEL=<configurable>
AI_REVIEW_TIMEOUT_SECONDS=<configurable>
AI_REVIEW_MAX_RETRIES=3
```

## Fail-closed behavior

```text
Ollama unavailable → BLOCKED
Model missing → BLOCKED
Timeout → BLOCKED
Invalid JSON → BLOCKED
Schema failure → BLOCKED
Fallback used → BLOCKED
Review WARNING → WAITING_HUMAN_REVIEW
Review BLOCKED → BLOCKED
Review PASS → approval gate
```

## Review input

Phải dùng dữ liệu thực:

* Phase specification.
* Base commit.
* Current commit.
* Actual Git diff.
* Changed files.
* Migration list.
* Test commands.
* Test results.
* Security findings.
* Known limitations.
* Codex implementation summary.

Không chỉ review report tự khai.

## Review schema

```json
{
  "decision": "PASS|WARNING|BLOCKED",
  "summary": "",
  "requirements_checked": [],
  "missing_requirements": [],
  "critical_findings": [],
  "high_findings": [],
  "medium_findings": [],
  "security_findings": [],
  "test_findings": [],
  "migration_findings": [],
  "recommended_actions": [],
  "requires_human_review": true,
  "model": "",
  "prompt_version": ""
}
```

## Correction loop

```text
Review finding
→ Correction task
→ Codex sửa
→ Focused tests
→ Regression tests
→ Review actual diff lại
```

Tối đa ba vòng.

## n8n state

```text
CODEX_RUNNING
TESTING
AI_REVIEWING
CORRECTION_REQUIRED
WAITING_HUMAN_APPROVAL
APPROVED
BLOCKED
FAILED
```

n8n không được:

* Tự approve.
* Tự merge.
* Tự deploy.
* Chuyển phase nếu gate chưa đạt.

## Evidence

Lưu:

```text
model
model digest/version
prompt version
review input hash
review output hash
base commit
current commit
diff summary
test-result hashes
timestamp
correlation ID
```

## Test bắt buộc

* Required mode + Ollama offline.
* Model missing.
* Timeout.
* Invalid JSON.
* Schema mismatch.
* WARNING.
* BLOCKED.
* PASS.
* Critical finding blocks COMPLETE.
* High finding blocks COMPLETE.
* Fallback cannot PASS.
* Actual Git diff is reviewed.
* Correction limit.
* AI cannot set human approval.
* n8n cannot advance without gate.

## File bắt buộc

```text
docs/codex-prompts/AI_05_MANDATORY_OLLAMA_REVIEW.md
docs/reviews/AI_05_MANDATORY_OLLAMA_REVIEW_REVIEW.md
docs/reviews/AI_05_MANDATORY_OLLAMA_REVIEW_RESULT.json
docs/evidence/ai-05/
```

## Commit

```text
feat(ai-factory): enforce mandatory ollama phase review
```

---

# 17. PHASE AI-06 — FINAL INTEGRATION AND HANDOVER

## Mục tiêu

Tích hợp toàn bộ AI-01 đến AI-05, chạy regression toàn hệ thống và tạo handover hoàn chỉnh.

## Thực hiện

1. Kiểm tra dependency graph cuối.
2. Kiểm tra migration graph.
3. Chạy migration trên database rỗng.
4. Chạy migration compatibility trên database demo được sao chép an toàn.
5. Chạy Django system check.
6. Chạy focused AI tests.
7. Chạy Knowledge/RAG tests.
8. Chạy Governance tests.
9. Chạy AI Sales tests.
10. Chạy AI Agent tests.
11. Chạy AI Factory tests.
12. Chạy n8n workflow validation.
13. Chạy toàn bộ regression tests.
14. Chạy security scan hiện có.
15. Chạy dependency audit nếu công cụ sẵn sàng.
16. Kiểm tra Docker/settings.
17. Kiểm tra Redis.
18. Kiểm tra PostgreSQL/vector backend.
19. Kiểm tra Ollama health.
20. Chạy local real-data demo bằng dữ liệu đã được làm sạch.
21. Kiểm tra không có autonomous action.
22. Kiểm tra không có secret trong Git diff.
23. Kiểm tra không có runtime database/backup/ZIP trong commit.

## Final review

Ollama phải review:

```text
Baseline commit
Final commit
All phase specifications
All phase review reports
All migrations
Actual cumulative Git diff
All test results
All security findings
Known limitations
Production readiness
```

## File bắt buộc

```text
docs/codex-prompts/AI_06_FINAL_INTEGRATION.md
docs/reviews/AI_SYSTEM_HARDENING_V2_FINAL_REPORT.md
docs/reviews/AI_SYSTEM_HARDENING_V2_FINAL_RESULT.json
docs/reviews/AI_SYSTEM_HARDENING_V2_FINAL_HANDOVER.md
docs/reviews/AI_SYSTEM_HARDENING_V2_PHASE_STATUS.md
docs/reviews/AI_SYSTEM_HARDENING_V2_COMMIT_MANIFEST.md
docs/reviews/AI_SYSTEM_HARDENING_V2_KNOWN_ISSUES.md
docs/reviews/AI_SYSTEM_HARDENING_V2_HUMAN_APPROVAL_QUEUE.md
docs/evidence/ai-06/
```

## Final commit

```text
docs(ai): finalize hardening v2 review and handover
```

---

# 18. EVIDENCE BẮT BUỘC CHO MỖI PHASE

Tạo:

```text
docs/evidence/ai-XX/
```

Tối thiểu gồm:

```text
environment-summary.txt
git-status-before.txt
baseline-commit.txt
task-dependency-graph.json
file-ownership.json
commands.log
changed-files.txt
git-diff-stat.txt
git-diff-check.txt
compile-results.txt
django-check-results.txt
migration-check-results.txt
focused-test-results.txt
integration-test-results.txt
regression-test-results.txt
lint-results.txt
typecheck-results.txt
security-results.txt
dependency-audit-results.txt
ollama-health.json
ollama-review-input-hash.txt
ollama-review-output.json
ollama-review-output-hash.txt
known-limitations.md
commit-hash.txt
commit-show.txt
```

Nếu công cụ không chạy được:

```text
STATUS = NOT_RUN
REASON = <lỗi thật>
RETRY_COMMAND = <command cần chạy lại>
IMPACT = <ảnh hưởng>
```

Không được tạo output PASS giả.

Evidence quan trọng phải có SHA-256 checksum.

---

# 19. REVIEW FILE CHO MỖI PHASE

Mỗi review phải có:

```text
Phase
Date/time
Branch
Baseline commit
Task commits
Integration commit
Objective
Scope
Files changed
Architecture decision
Database impact
Security impact
Runtime behavior
Commands executed
Tests passed
Tests failed
Tests skipped
Tools not run
Ollama model
Ollama review decision
Critical findings
High findings
Medium findings
Known limitations
Rollback instructions
Final phase decision
Next phase eligibility
```

Decision chỉ được dùng:

```text
PASS
PASS_WITH_WARNINGS
BLOCKED
FAILED
```

`PASS_WITH_WARNINGS` không được chuyển phase nếu warning thuộc mức Critical hoặc High.

---

# 20. GIT COMMIT POLICY

## Task commit

Mỗi task hoàn chỉnh có thể tạo commit riêng:

```text
feat(ai): ...
test(ai): ...
fix(ai): ...
docs(ai): ...
```

## Phase integration commit

Sau khi tích hợp và test, mỗi phase phải có commit checkpoint rõ ràng.

Không dùng message:

```text
update
changes
fix
done
final
```

## Trước commit

Chạy:

```bash
git status --short
git diff --check
git diff --stat
git diff --cached --check
```

Kiểm tra staged files:

* Không secret.
* Không database.
* Không backup.
* Không ZIP.
* Không cache.
* Không log chứa dữ liệu nhạy cảm.
* Không file ngoài scope.

## Sau commit

Chạy:

```bash
git rev-parse HEAD
git show --stat --oneline --decorate HEAD
git status --short
```

Ghi hash tự động vào:

```text
docs/reviews/AI_SYSTEM_HARDENING_V2_COMMIT_MANIFEST.md
```

Bảng manifest:

| Phase | Task/Integration | Commit | Message | Tests | Ollama review | Status |
| ----- | ---------------- | ------ | ------- | ----- | ------------- | ------ |

Không chỉnh sửa commit hash bằng tay.

Nếu remote không có hoặc credentials không hợp lệ:

```text
LOCAL_COMMITS_CREATED_REMOTE_NOT_CONFIGURED
```

Đây không phải lỗi code.

Không tự tạo remote giả.

---

# 21. QUALITY COMMANDS

Codex phải tự xác định command phù hợp với repository thật.

Tối thiểu thử:

```bash
python -m compileall django_backend ai-factory ai-review scripts
python django_backend/manage.py check
python django_backend/manage.py makemigrations --check --dry-run
pytest <focused-tests>
pytest
```

Nếu repository hỗ trợ:

```bash
ruff check .
ruff format --check .
mypy .
bandit -r django_backend ai-factory ai-review
pip-audit
docker compose config
```

Chạy AI Factory theo phase slug thực tế:

```bash
python ai-factory/run_ai_factory.py --phase <phase-slug>
```

Không tự bịa phase slug. Phải kiểm tra config/registry thật.

---

# 22. FINAL STATUS

Chỉ dùng:

```text
AI_SYSTEM_HARDENING_V2_COMPLETE
AI_SYSTEM_HARDENING_V2_PASS_WITH_WARNINGS
AI_SYSTEM_HARDENING_V2_BLOCKED
AI_SYSTEM_HARDENING_V2_FAILED
```

Chỉ dùng `COMPLETE` khi:

* AI-00 đến AI-06 đều PASS.
* Tất cả phase có commit.
* Tất cả phase có review.
* Tất cả phase có evidence.
* Full regression PASS.
* Ollama review thật PASS.
* Critical findings = 0.
* High findings = 0.
* Không dùng fallback review.
* Không có secret trong Git.
* Không có runtime database hoặc backup trong commit.
* Không có autonomous dangerous action.
* Working tree sạch hoặc mọi thay đổi còn lại đều được giải thích.

Trạng thái cuối cùng bắt buộc:

```text
WAITING_FOR_HUMAN_APPROVAL
```

Không merge vào `main`.

Không push nếu chưa được phép.

Không tạo release tag.

Không deploy staging hoặc production.

---

# 23. FINAL RESPONSE CỦA CODEX

Khi hoàn thành hoặc bị block, Codex phải trả lời:

```text
PIPELINE STATUS:
BASELINE COMMIT:
FINAL COMMIT:
CURRENT BRANCH:
PHASES COMPLETED:
PHASES BLOCKED:
TASKS RUN IN PARALLEL:
TASKS SERIALIZED:
MIGRATIONS CREATED:
TEST COMMANDS:
TEST RESULTS:
OLLAMA MODELS:
OLLAMA REVIEW STATUS:
CRITICAL FINDINGS:
HIGH FINDINGS:
COMMITS CREATED:
REVIEW FILES:
EVIDENCE DIRECTORIES:
KNOWN LIMITATIONS:
WORKING TREE STATUS:
REMOTE STATUS:
NEXT HUMAN ACTION:
```

Không chỉ trả lời “done” hoặc “complete”.

Bắt đầu ngay bằng Phase AI-00.

Không hỏi xác nhận lại trừ khi:

* Có nguy cơ mất dữ liệu.
* Cần secret/credential.
* Cần merge `main`.
* Cần push remote.
* Cần deploy.
* Cần thực hiện hành động phá hủy.

Trong mọi trường hợp còn lại, tự thực hiện toàn bộ pipeline theo dependency graph và quy tắc chuyển phase ở trên.
