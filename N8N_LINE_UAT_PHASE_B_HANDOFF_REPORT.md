# N8N + LINE UAT — Phase B Handoff Report

**Ngày báo cáo:** 2026-09-27 (Asia/Tokyo)

**Repository:** `https://github.com/hoangquocquan/Django-web-t-123.git`

**Worktree:** `C:\Users\hoang\Documents\Codex\n8n-line-uat-demo`

**Branch bắt buộc:** `feature/n8n-line-uat-demo`

**Commit sửa runtime builder:** `f81a98a fix(line-uat): repair live runtime workflow builder`

**Commit sửa Foundation bootstrap:** `e134278 fix(line-uat): bootstrap foundation role for isolated UAT runtime`

**Commit sửa n8n CLI resolution:** `6fc347f fix(line-uat): resolve n8n cli dynamically on windows`

**Commit harden NVM discovery:** `8be071e fix(line-uat): support nvm windows cli discovery`

> Đây là báo cáo bàn giao giữa chừng. Phase B live E2E chưa gửi LINE và chưa được phép kết luận PASS.

> Final review note (2026-09-27): báo cáo này là lịch sử điều tra. Quy trình isolated runtime cuối cùng đã được harden thành hai bước: `start_live_runtime.ps1` khởi động n8n để operator tạo owner, sau đó `attach_runtime_workflow.ps1` import workflow inactive vào đúng personal project và xác minh ownership. Xem `FINAL_REVIEW_REPORT.md` và báo cáo Phase C cho trạng thái cuối.

## 1. Trạng thái hiện tại

- Đúng worktree và branch bắt buộc.
- Không merge `main`.
- Không push remote.
- Working tree chỉ có file báo cáo này chưa được track sau commit `8be071e`; không có thay đổi code chưa commit.
- Ba Windows User Environment Variables đã được người vận hành nhập và script tương tác xác nhận `configured=yes`.
- Giá trị credential không xuất hiện trong báo cáo, source, Git hoặc command-line argument.
- Dedicated LINE Official Account UAT: `Hoangjp`.
- Messaging API channel UAT thuộc provider `Bang Gia Thuoc Automation`.
- Recipient là user ID của tài khoản LINE test do người vận hành chọn.
- LINE `GET profile` đã trả kết quả xác minh recipient thành công trước khi lỗi workflow builder xảy ra.
- `LINE_SEND_ENABLED=false` trong toàn bộ quá trình debug và verification.
- LINE provider send count hiện tại: `0`.
- Chưa gọi Django LINE send endpoint trong quá trình sửa lỗi.

## 2. Lỗi đã gặp

Lệnh khởi động:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\hoang\Documents\Codex\n8n-line-uat-demo\scripts\line_uat\start_live_runtime.ps1"
```

đã nhận đủ credential và xác minh recipient, nhưng fail ở bước build runtime workflow với:

```text
SyntaxError: '{' was never closed
Failed to build runtime-only interlocked workflow.
```

## 3. Root cause

`start_live_runtime.ps1` trước đó nhúng một Python dictionary lớn trong PowerShell here-string rồi truyền nội dung qua `python -c`.

Nội dung Python tự thân hợp lệ, nhưng đường truyền:

```text
Windows PowerShell 5.1 -> native argument marshalling -> python -c
```

không bảo toàn ổn định dấu quote và cấu trúc multiline. Python nhận nội dung dictionary không nguyên vẹn và báo dấu `{` chưa đóng.

Inline Foundation-token creator dùng cùng mô hình `python -c`, nên cũng được loại bỏ chủ động để tránh lỗi kế tiếp cùng loại.

## 4. Fix đã áp dụng

### Workflow builder độc lập

Thêm:

```text
scripts/line_uat/build_live_workflow.py
```

Helper này:

- nhận source workflow và destination bằng hai argument riêng;
- đọc source bằng `json.load()`;
- fail-closed nếu source workflow đang active;
- fail-closed nếu source chứa `api.line.me`;
- fail-closed nếu source chứa biến LINE access token;
- xác nhận các safety node bắt buộc tồn tại;
- thêm `Final Runtime Send Interlock` sau `Verify APPROVED Safety State`;
- nối interlock tới `Django Kill Switch + LINE Send`;
- giữ workflow runtime `active=false`;
- ghi JSON bằng `json.dump()`.

### Foundation token helper độc lập

Thêm:

```text
scripts/line_uat/create_foundation_token.py
```

Token Foundation tạm được PowerShell capture trực tiếp vào memory và bảo vệ bằng Windows DPAPI trong runtime directory. Token không được in trong report hoặc commit.

### Launcher đã sửa

`scripts/line_uat/start_live_runtime.ps1` hiện gọi hai helper `.py` bằng file path và argument riêng, không còn truyền dictionary/JSON qua `python -c`.

### Regression coverage

Thêm test xác nhận runtime builder:

- tạo JSON hợp lệ;
- giữ `active=false`;
- không chứa direct LINE endpoint;
- không chứa access-token variable;
- đặt interlock chính xác giữa verify và send;
- send node lấy approval ID từ record đã được verify.

## 5. Verification đã PASS

```text
POWERSHELL_PARSE=PASS
PYTHON_COMPILE=PASS
SOURCE_JSON=PASS
RUNTIME_WORKFLOW_JSON=PASS
RUNTIME_ACTIVE=False
INTERLOCK_TYPE=n8n-nodes-base.wait
VERIFY_NEXT=Final Runtime Send Interlock
INTERLOCK_NEXT=Django Kill Switch + LINE Send
DIRECT_LINE_CALL=False
TOKEN_VAR_PRESENT=False
```

Relevant suite sau cả hai bản sửa:

```text
86 passed
```

Các kiểm tra khác:

```text
Django system check: PASS
Ruff: PASS
PowerShell parse: PASS
Python py_compile: PASS
Source workflow JSON validation: PASS
Runtime workflow JSON validation: PASS
```

## 6. Lỗi Foundation role trên isolated UAT DB

Sau khi runtime builder được sửa, launcher tiếp tục đến bước tạo Foundation token nhưng fail với:

```text
apps.foundation.models.FoundationRole.DoesNotExist
FoundationRole matching query does not exist.
```

### Root cause

Migration Phase 3D tạo role chuẩn `Manager` với bộ business permissions rộng. Trong khi đó, token helper tìm exact lowercase `manager`, nhưng role UAT tối thiểu này chưa tồn tại trong SQLite database mới. Đổi lookup sang role `Manager` hiện có sẽ cấp quyền vượt quá phạm vi UAT và vi phạm least privilege.

### Fix đã áp dụng

Thêm `scripts/line_uat/bootstrap_foundation_uat.py`, tái sử dụng đúng Foundation models và các permission record do migrations định nghĩa. Helper:

- tạo deterministic role lowercase `manager` chỉ dành cho isolated LINE UAT;
- cấp chính xác bốn permissions:
  - `ai_sales:read`
  - `sales:read`
  - `line_uat:read`
  - `line_uat:approve`
- không cấp superuser, wildcard hoặc permission ngoài scope;
- idempotent khi chạy launcher lần hai;
- fail-closed nếu role lowercase đã tồn tại nhưng không phải role UAT do helper quản lý, hoặc permission set khác chính xác bốn quyền trên;
- không tạo hệ thống role song song: helper dùng chính Foundation role/permission/role-permission models hiện hữu;
- không in Foundation bearer token.

`create_foundation_token.py` cũng được harden để xác minh exact role identity và exact permission set trước khi tạo temporary principal. Launcher hiện chạy theo thứ tự:

```text
migrations -> UAT role bootstrap -> temporary token creation -> isolated services
```

### Regression và fresh-database evidence

```text
Fresh UAT DB without lowercase role: PASS
Exact four permissions and no wildcard: PASS
Second bootstrap run/idempotency: PASS
Temporary principal/token creation after bootstrap: PASS
FRESH_DB_BOOTSTRAP=PASS
IDEMPOTENT_BOOTSTRAP=PASS
FOUNDATION_UAT_TOKEN_READY=yes
LINE_SEND_ENABLED=false
```

## 7. Lỗi n8n CLI resolution trên Windows

Launcher trước đó gọi trực tiếp `n8n` và khởi động `n8n.cmd`, khiến Windows dùng một npm shim cũ trỏ về `%APPDATA%\npm\node_modules\n8n\bin\n8n`. Cài đặt thực tế trên máy nằm dưới NVM for Windows.

Điều tra an toàn xác nhận:

```text
N8N INSTALL LOCATION: C:\nvm4w\nodejs\n8n.cmd
N8N VERSION: 2.37.10
npm global root: C:\nvm4w\nodejs\node_modules
```

Thêm `scripts/line_uat/N8nCliResolver.psm1`. Resolver:

- hỗ trợ explicit process/user override `N8N_UAT_CLI_PATH`;
- kiểm tra `Get-Command n8n` và `Get-Command n8n.cmd`;
- kiểm tra project-local `node_modules`;
- lấy npm prefix động bằng `npm config get prefix`;
- lấy npm global root động bằng `npm root -g`;
- kiểm tra `NVM_SYMLINK` và các PATH entries đang active;
- bỏ qua shim tồn tại nhưng không chạy được để tiếp tục tới candidate hợp lệ;
- không giả định `%APPDATA%\npm`;
- xác minh CLI thực thi được và đọc semantic version;
- fail-closed với `N8N CLI NOT FOUND` nếu không resolve được;
- yêu cầu đúng version UAT `2.37.10` trước khi tiếp tục;
- dùng cùng descriptor đã resolve cho cả workflow import và isolated runtime start.

Regression tests cho process override, NVM for Windows symlink, stale AppData shim, wrong version, missing binary và loại bỏ hard-coded AppData assumption đều PASS. Isolated workflow import bằng CLI đã resolve cũng PASS; thao tác này không có credential, không khởi động workflow và không gửi LINE.

## 8. Safety assertions

- Source n8n workflow vẫn `active=false`.
- Runtime workflow builder không bỏ hoặc bypass Human Approval Gate.
- Runtime-only interlock bổ sung một điểm dừng sau approval re-fetch/verification và trước send.
- n8n không gọi `api.line.me` trực tiếp.
- LINE credential chỉ được Django runtime nhận qua process environment.
- Không hard-code LINE credential.
- Không in Authorization header.
- Không dùng customer data thật.
- Không dùng production LINE channel.
- Không gửi broadcast, multicast hoặc autonomous message.
- Không có provider send trong lúc debug.

## 9. Bước tiếp theo bắt buộc

Do Codex executor chạy dưới Windows sandbox account khác, launcher phải được chạy từ PowerShell của người vận hành để đọc đúng User Environment Variables:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\hoang\Documents\Codex\n8n-line-uat-demo\scripts\line_uat\start_live_runtime.ps1"
```

Chỉ tiếp tục nếu output có đầy đủ:

```text
LINE_UAT_CHANNEL_ACCESS_TOKEN: configured=yes
LINE_UAT_CHANNEL_SECRET: configured=yes
LINE_UAT_RECIPIENT_USER_ID: configured=yes
LINE_UAT_RECIPIENT_PROFILE: verified=yes
FOUNDATION_UAT_ROLE_READY=yes
FOUNDATION_UAT_TOKEN_READY=yes
N8N_CLI_FOUND=yes
N8N_CLI_PATH=C:\nvm4w\nodejs\n8n.cmd
N8N_VERSION=2.37.10
RUNTIME_UAT_READY=yes
DJANGO_LISTENING_127_0_0_1_8000=yes
N8N_LISTENING_127_0_0_1_5678=yes
LINE_SEND_ENABLED=false
WORKFLOW_ACTIVE=false
```

Sau đó:

1. Mở isolated n8n tại `http://127.0.0.1:5678`.
2. Chạy workflow bằng Manual Trigger.
3. Chờ Human Approval Gate.
4. Hiển thị exact proposed LINE message cho người vận hành.
5. Dừng để người vận hành tự chọn APPROVE và xác nhận synthetic UAT.
6. Không bật send switch trước khi record đã APPROVED, được re-fetch và content hash/safety state được xác minh.

Nếu launcher không đạt toàn bộ trạng thái trên, fail-closed và không gửi.

## 10. Handoff status

```text
ROOT CAUSE 1: Windows PowerShell 5.1 python -c quoting/marshalling corrupted inline Python
FIX 1: Standalone Python helpers + argument-based paths + regression test
ROOT CAUSE 2: Fresh isolated DB lacked the exact lowercase least-privilege UAT role; canonical Manager was intentionally too broad
FIX 2: Deterministic idempotent Foundation UAT bootstrap with exactly four migration-defined permissions
ROOT CAUSE 3: Resolver stopped on the first stale PATH shim and the launcher masked all resolver errors as N8N CLI NOT FOUND, preventing fallback to the valid NVM installation
FIX 3: Candidate-by-candidate fail-closed discovery across process/user overrides, Get-Command -All, npm prefix/root, NVM_SYMLINK and active PATH; the same resolved descriptor is used by import and runtime start
N8N INSTALL LOCATION: C:\nvm4w\nodejs\n8n.cmd
N8N VERSION: 2.37.10
TESTS: 91 PASSED; Django check PASS; Ruff PASS; PowerShell parse PASS; Python compile PASS; workflow JSON PASS; isolated n8n import PASS
FOUNDATION ROLE BOOTSTRAP: PASS
FOUNDATION TOKEN CREATION: PASS
RUNTIME WORKFLOW JSON: PASS
LINE_SEND_ENABLED: false
LINE PROVIDER SEND COUNT: 0
CURRENT BRANCH: feature/n8n-line-uat-demo
MAIN MERGED: NO
REMOTE PUSH: NO
READY FOR HUMAN APPROVAL STAGE: NO — operator runtime restart after commit 8be071e is still required because the Codex sandbox cannot read the user's credential environment
LIVE LINE UAT E2E: NOT RUN
```
