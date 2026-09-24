# CODEX PROMPT — KIỂM THỬ TOÀN DIỆN DỮ LIỆU DEMO TRONG DATABASE DJANGO

## 1. Bối cảnh

Repository MEC Precision Platform đang sử dụng database local:

```text
django_backend/db.sqlite3
```

Database này chứa dữ liệu demo/mô phỏng thật đã được lưu bằng Django ORM để phục vụ kiểm thử, không phải dữ liệu HTML hard-code.

Số lượng dữ liệu dự kiến:

```text
Sản phẩm:                214
Hồ sơ khách hàng:        501
Khách hàng tiềm năng:  1.003
Báo giá:                 503
Tài liệu kiến thức:      105
Người dùng hệ thống:      17
```

Đây là dữ liệu demo, không phải dữ liệu khách hàng production. Dữ liệu có thể được thêm, sửa và xóa an toàn trong môi trường local.

## 2. Mục tiêu

Thực hiện kiểm thử toàn diện để xác minh:

1. Database `django_backend/db.sqlite3` tồn tại và Django đang kết nối đúng database này.
2. Các số lượng dữ liệu thực tế khớp hoặc giải thích được sự khác biệt với số liệu dự kiến.
3. Dữ liệu được lấy từ database, không phải HTML giả hoặc danh sách hard-code.
4. Django ORM đọc được dữ liệu.
5. Trang quản trị và Business UI hiển thị đúng dữ liệu database.
6. Có thể thêm, sửa và xóa dữ liệu demo an toàn.
7. Quan hệ giữa Customer, Lead, Opportunity, Quotation, Order và Knowledge Document hợp lệ.
8. API, UI, AI Sales và RAG sử dụng đúng dữ liệu database.
9. Toàn bộ test hiện có vẫn PASS.
10. Tạo bằng chứng, báo cáo review và commit Git riêng.

Không được xóa hoặc làm hỏng database gốc trong quá trình kiểm thử.

---

# 3. Quy tắc an toàn

Không được:

* Kiểm thử CRUD trực tiếp trên database gốc nếu có nguy cơ làm mất dữ liệu.
* Xóa toàn bộ bảng.
* Dùng `flush` trên database gốc.
* Dùng `reset_db`.
* Xóa file `django_backend/db.sqlite3`.
* Chạy migration phá hủy dữ liệu.
* Thay đổi dữ liệu production.
* Tạo kết quả kiểm thử giả.
* Chỉ kiểm tra HTML mà không kiểm tra ORM/database.
* Đánh dấu PASS khi command chưa chạy.
* Commit file database sau khi test.
* Commit backup, token, session hoặc secret.
* Merge `main`, push, tạo tag hoặc deploy.

Phải tạo bản sao database trước khi chạy CRUD test.

Ví dụ:

```text
django_backend/db.sqlite3
→ temporary_test_database.sqlite3
```

CRUD test phải chạy trên:

* Django test database;
* transaction rollback;
* hoặc bản sao tạm của database.

Không được làm thay đổi dữ liệu gốc ngoài những thao tác đã được người dùng thực hiện thủ công.

---

# 4. Kiểm tra Git và môi trường

Trước khi sửa code, chạy:

```bash
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git status --short
python --version
```

Ghi lại:

```text
Repository root
Current branch
Baseline commit
Working-tree state
Python version
Django version
Database path
Database file size
Database last modified time
```

Không reset hoặc discard thay đổi của người dùng.

Tạo branch nếu phù hợp:

```text
codex/demo-database-validation
```

---

# 5. Xác minh database thật

## 5.1 Kiểm tra file

Xác minh:

```text
django_backend/db.sqlite3
```

Ghi nhận:

* File có tồn tại không.
* Kích thước file.
* Quyền đọc/ghi.
* SQLite header hợp lệ.
* Django settings đang trỏ đến đúng đường dẫn.
* Có database nào khác đang được dùng thay thế hay không.

Chạy:

```bash
python django_backend/manage.py check
python django_backend/manage.py showmigrations
python django_backend/manage.py makemigrations --check --dry-run
```

## 5.2 Kiểm tra bảng

Dùng Django ORM và SQLite metadata để liệt kê:

* Tên bảng.
* Số lượng bản ghi.
* Migration hiện tại.
* Foreign key.
* Index.
* Unique constraint.

Không chỉ dùng raw SQL. Đối chiếu kết quả raw SQLite với Django ORM.

## 5.3 Kiểm tra số lượng bản ghi

Xác định chính xác model tương ứng với:

```text
214 sản phẩm
501 hồ sơ khách hàng
1.003 khách hàng tiềm năng
503 báo giá
105 tài liệu kiến thức
17 người dùng hệ thống
```

Không giả định tên model. Phải kiểm tra source và app thực tế.

Tạo command hoặc script kiểm tra, ví dụ:

```bash
python django_backend/manage.py validate_demo_database
```

Kết quả phải có dạng JSON và text dễ đọc:

```json
{
  "database": "django_backend/db.sqlite3",
  "models": {
    "products": {
      "expected": 214,
      "actual": 214,
      "status": "PASS"
    },
    "customers": {
      "expected": 501,
      "actual": 501,
      "status": "PASS"
    }
  }
}
```

Nếu số lượng khác:

* Không tự sửa dữ liệu chỉ để làm test PASS.
* Ghi số lượng thực tế.
* Tìm nguyên nhân.
* Xác định bản ghi tăng/giảm có hợp lệ không.
* Đánh dấu `PASS_WITH_DATA_DRIFT` hoặc `FAIL` tùy mức độ.

---

# 6. Chứng minh dữ liệu không phải HTML giả

Kiểm tra source để phát hiện:

* Danh sách sản phẩm hard-code trong template.
* Customer/lead/quotation hard-code trong view.
* JSON fixture nhúng trực tiếp vào JavaScript.
* Template hiển thị dữ liệu mẫu khi ORM không trả dữ liệu.
* Các số lượng dashboard được viết cố định.
* Fake API response.
* Mock data bị dùng trong runtime.

Đối với từng trang chính:

```text
Dashboard
Products
Customers
Leads
Opportunities
Quotations
Orders
Knowledge Documents
Users
```

Phải truy vết:

```text
URL
→ View
→ Service
→ ORM QuerySet
→ Model
→ Database table
→ Template/API response
```

Tạo bảng evidence:

| Trang/API | View | Service | Model | Table | Dữ liệu từ ORM | Hard-code phát hiện |
| --------- | ---- | ------- | ----- | ----- | -------------: | ------------------: |

Nếu phát hiện runtime đang dùng dữ liệu hard-code thay cho database:

* Sửa để dùng ORM thật.
* Viết regression test.
* Không xóa fixture chỉ dùng cho test.

---

# 7. Kiểm thử chất lượng dữ liệu

Kiểm tra các vấn đề:

## Products

* Tên sản phẩm rỗng.
* Mã sản phẩm trùng.
* Giá âm.
* Giá dùng sai kiểu dữ liệu.
* Sản phẩm thiếu category.
* Trạng thái không hợp lệ.
* Dữ liệu archive/draft hiển thị sai phạm vi.

## Customers

* Tên rỗng.
* Email sai định dạng.
* Email trùng bất thường.
* Điện thoại sai.
* Công ty thiếu.
* Customer bị orphan.
* Customer có dữ liệu demo không nhất quán.

## Leads

* Lead không có customer.
* Lead status không hợp lệ.
* Assigned user không tồn tại.
* Lead score ngoài phạm vi.
* Lead có ngày tạo sau ngày cập nhật.
* Lead không có nguồn.
* Lead trùng bất thường.

## Quotations

* Quotation không có customer/lead/opportunity.
* Tổng tiền âm.
* Currency không hợp lệ.
* Status không hợp lệ.
* Quotation approved nhưng thiếu approver.
* Draft quotation có approved timestamp.
* File bản vẽ không tồn tại hoặc URL không an toàn.

## Knowledge documents

* Tài liệu không có chunk.
* Chunk orphan.
* Embedding thiếu.
* Embedding model/version không khớp.
* File nguồn không tồn tại.
* Trạng thái index sai.
* Citation source ID không tồn tại.

## Users

* Email trùng.
* User không có role.
* Role không có permission.
* User inactive nhưng session còn hiệu lực.
* Admin demo có password mặc định nguy hiểm.
* Token/session hết hạn chưa được cleanup.

Tạo kết quả phân loại:

```text
Critical
High
Medium
Low
Informational
```

Không tự sửa dữ liệu hàng loạt nếu chưa có quy tắc rõ ràng.

---

# 8. Kiểm thử CRUD an toàn

Viết test cho mỗi nhóm:

```text
Create
Read
Update
Delete
Validation
Permission
Audit
Rollback
```

## Products

* Tạo sản phẩm.
* Đọc chi tiết.
* Sửa giá/tên/trạng thái.
* Xóa hoặc archive theo business rule.
* Kiểm tra validation.

## Customers

* Tạo customer.
* Thêm interaction.
* Thêm note.
* Tạo task.
* Sửa dữ liệu.
* Xóa/archive theo rule.
* Kiểm tra timeline.

## Leads và Sales

```text
Create lead
→ Assign user
→ Update status
→ Convert opportunity
→ Create quotation
→ Approve/reject
→ Create follow-up
```

## Knowledge

```text
Create document
→ Upload/index
→ Search
→ Ask RAG
→ Verify citation
→ Delete/archive
→ Ensure chunks/embeddings cleanup
```

## Users

* Tạo user demo.
* Gán role.
* Kiểm tra permission.
* Disable.
* Revoke session.
* Xóa user theo rule.

CRUD tests phải sử dụng:

* Django test database;
* `TestCase`;
* transaction rollback;
* hoặc database copy tạm.

Sau test, đối chiếu checksum/số lượng của database gốc để chứng minh không bị thay đổi ngoài ý muốn.

---

# 9. Kiểm thử Admin và Business UI

Dùng Django test client và Playwright/Selenium nếu repository có hỗ trợ.

Kiểm tra:

* Danh sách hiển thị đúng số lượng.
* Pagination.
* Filter.
* Search.
* Sort.
* Detail page.
* Create form.
* Edit form.
* Delete/archive confirmation.
* Validation error.
* Permission theo role.
* CSRF.
* Không lộ raw dictionary.
* Không lộ secret, token hoặc internal note cho role không phù hợp.

Tối thiểu kiểm tra các role:

```text
CEO
Admin
Sales Manager
Sales
CRM
Technical
```

So sánh một số bản ghi trực tiếp:

```text
ORM value
API value
HTML displayed value
```

Các giá trị phải nhất quán.

---

# 10. Kiểm thử API

Với các API Products, Customers, Leads, Quotations, Knowledge và Users:

* Authentication.
* Authorization.
* Pagination.
* Filtering.
* Search.
* Detail.
* Create.
* Update.
* Delete/archive.
* Invalid input.
* Not found.
* Rate limit.
* Audit event.
* Không trả dữ liệu role không có quyền.
* Không trả draft/private data cho public endpoint.

Đối chiếu API response với ORM/database.

---

# 11. Kiểm thử AI và RAG bằng dữ liệu database

## AI Sales

Xác minh:

* Lead/customer/quotation được lấy từ database thật.
* Deterministic score không bị model tự thay đổi.
* Ollama chỉ tạo phần tổng hợp hoặc draft.
* Không tự gửi email.
* Không tự cập nhật CRM.
* `human_approval_required = true`.
* `autonomous_action = false`.

## Knowledge/RAG

Chọn một số tài liệu trong 105 tài liệu:

```text
Document
→ Chunk
→ Embedding
→ Retrieval
→ AI answer
→ Citation
```

Kiểm tra:

* Citation trỏ đúng document/chunk.
* Không có context thì không bịa.
* Tiếng Việt và tiếng Anh.
* Quyền tài liệu.
* Tài liệu bị archive không được retrieval nếu policy cấm.
* Database record và vector index nhất quán.

## Governance

Kiểm tra:

* Prompt an toàn được cho phép.
* Prompt nguy hiểm bị chặn.
* Audit event được lưu.
* Không lưu full secret/prompt nhạy cảm.
* Rate limit hoạt động.

---

# 12. Kiểm thử hiệu năng cơ bản

Trên database demo hiện tại, đo:

* Dashboard query count.
* Products list.
* Customers list.
* Leads list.
* Quotations list.
* Knowledge search.
* AI Sales context building.

Ghi:

```text
Record count
Query count
Response time
p50/p95 nếu chạy lặp
N+1 query detected
Pagination status
```

Không cần load test production lớn, nhưng phải phát hiện N+1 và truy vấn toàn bảng không cần thiết.

---

# 13. Test bắt buộc

Chạy:

```bash
python -m compileall django_backend ai-factory ai-review scripts
python django_backend/manage.py check
python django_backend/manage.py makemigrations --check --dry-run
pytest <focused-demo-database-tests>
pytest
```

Nếu có:

```bash
ruff check .
ruff format --check .
mypy .
bandit -r django_backend ai-factory ai-review
```

Tạo các test mới phù hợp, ví dụ:

```text
tests/test_demo_database_counts.py
tests/test_demo_database_integrity.py
tests/test_demo_database_crud.py
tests/test_demo_database_ui.py
tests/test_demo_database_api.py
tests/test_demo_database_ai_rag.py
tests/test_demo_database_performance.py
```

Không bắt buộc đúng tên nếu cấu trúc repository khác.

---

# 14. Mandatory Ollama Review

Sau khi test PASS, chạy Mandatory Ollama Review trên:

* Phase specification.
* Actual Git diff.
* Database validation result.
* Data-integrity findings.
* CRUD results.
* API/UI results.
* AI/RAG results.
* Test output.
* Known limitations.

Bắt buộc:

```text
endpoint_reachable = true
model_available = true
response_received = true
schema_valid = true
fallback_used = false
decision = PASS
critical_findings = 0
high_findings = 0
human_approval_required = true
auto_merge = false
auto_deploy = false
```

Nếu database thực tế không thể kiểm tra, phase phải `BLOCKED`.

---

# 15. File phải tạo

```text
docs/codex-prompts/DEMO_DATABASE_VALIDATION_PHASE.md
docs/reviews/DEMO_DATABASE_VALIDATION_REVIEW.md
docs/reviews/DEMO_DATABASE_VALIDATION_RESULT.json
docs/reviews/DEMO_DATABASE_DATA_QUALITY_REPORT.md
docs/reviews/DEMO_DATABASE_CRUD_REPORT.md
docs/reviews/DEMO_DATABASE_UI_API_REPORT.md
docs/reviews/DEMO_DATABASE_AI_RAG_REPORT.md
docs/evidence/demo-database-validation/
```

Result JSON cần có:

```json
{
  "database_path": "django_backend/db.sqlite3",
  "database_verified": true,
  "original_database_modified": false,
  "expected_counts": {},
  "actual_counts": {},
  "count_status": {},
  "integrity_findings": {},
  "crud_tests": {},
  "ui_tests": {},
  "api_tests": {},
  "ai_rag_tests": {},
  "performance": {},
  "full_regression": {},
  "ollama_review": {},
  "decision": ""
}
```

---

# 16. Evidence bắt buộc

Tạo:

```text
docs/evidence/demo-database-validation/
```

Bao gồm tối thiểu:

```text
environment-summary.txt
git-status-before.txt
baseline-commit.txt
database-path.txt
database-file-metadata.json
database-sha256-before.txt
database-sha256-after.txt
django-database-settings.json
table-inventory.json
orm-record-counts.json
sqlite-record-counts.json
record-count-comparison.json
data-integrity-result.json
crud-test-results.txt
ui-test-results.txt
api-test-results.txt
ai-rag-test-results.txt
performance-results.json
compile-results.txt
django-check-results.txt
migration-check-results.txt
focused-test-results.txt
regression-test-results.txt
security-results.txt
ollama-review-output.json
known-limitations.md
commit-hash.txt
commit-show.txt
```

Nếu database checksum thay đổi:

* Xác định lý do.
* Kiểm tra có phải migration, session, audit log hoặc thao tác ngoài ý muốn.
* Không che giấu.
* Không đánh dấu PASS nếu database gốc bị thay đổi trái phép.

---

# 17. Điều kiện PASS

Chỉ PASS khi:

```text
Database file exists                    PASS
Django uses expected database           PASS
ORM access                              PASS
SQLite/ORM counts consistent            PASS
Expected counts verified/explained      PASS
No runtime hard-coded replacement       PASS
Data integrity Critical findings        0
Data integrity High findings            0
CRUD isolated from original DB          PASS
Admin/UI database consistency           PASS
API/database consistency                PASS
AI Sales database grounding             PASS
RAG citation/database consistency       PASS
Focused tests                           PASS
Full regression                         PASS
Mandatory Ollama review                 PASS
Original database preserved             PASS
```

Nếu số liệu có thay đổi hợp lệ do demo data đã được chỉnh thủ công, có thể dùng:

```text
PASS_WITH_DATA_DRIFT
```

nhưng phải giải thích từng chênh lệch.

---

# 18. Commit Git

Trước commit:

```bash
git status --short
git diff --check
git diff --stat
git diff --cached --check
```

Không stage hoặc commit:

```text
django_backend/db.sqlite3
temporary test databases
database backup
media test files
.env
secret
token
log chứa dữ liệu nhạy cảm
```

Tạo commit riêng:

```text
test(data): validate local demo database and business workflows
```

Sau commit:

```bash
git rev-parse HEAD
git show --stat --oneline --decorate HEAD
git status --short
```

Ghi commit hash vào review và evidence.

---

# 19. Trạng thái cuối

Chỉ sử dụng:

```text
DEMO_DATABASE_VALIDATION_PASS
DEMO_DATABASE_VALIDATION_PASS_WITH_DATA_DRIFT
DEMO_DATABASE_VALIDATION_BLOCKED
DEMO_DATABASE_VALIDATION_FAILED
```

Trạng thái cuối:

```text
WAITING_FOR_HUMAN_APPROVAL
```

Không merge, push, tag hoặc deploy.

## Phản hồi cuối của Codex

```text
STATUS:
BRANCH:
BASELINE COMMIT:
FINAL COMMIT:
DATABASE PATH:
DATABASE SHA-256 BEFORE:
DATABASE SHA-256 AFTER:
ORIGINAL DATABASE MODIFIED:
EXPECTED COUNTS:
ACTUAL COUNTS:
COUNT DIFFERENCES:
INTEGRITY FINDINGS:
CRUD TESTS:
UI TESTS:
API TESTS:
AI/RAG TESTS:
PERFORMANCE RESULTS:
FOCUSED TESTS:
FULL REGRESSION:
OLLAMA REVIEW:
CRITICAL FINDINGS:
HIGH FINDINGS:
FILES CREATED:
REVIEW FILES:
EVIDENCE DIRECTORY:
KNOWN LIMITATIONS:
WORKING TREE STATUS:
NEXT HUMAN ACTION:
```

Bắt đầu ngay.

Không hỏi lại trừ khi:

* Database không tồn tại.
* Có nguy cơ mất dữ liệu.
* Cần credential hoặc secret.
* Cần merge, push, tag hoặc deploy.
