# N8N + DJANGO AI SALES + LINE APPROVAL GATE — UAT DRY-RUN REPORT

**Timestamp:** 2026-09-26 22:09:17 +09:00

**Repository:** `https://github.com/hoangquocquan/Django-web-t-123.git`

**Worktree:** `C:\Users\hoang\Documents\Codex\n8n-line-uat-demo`

**Branch:** `feature/n8n-line-uat-demo`

**Tested HEAD:** `c15f235b588e6a33a8bfd1e62485edab9a22c184`

**Required hardening commit present:** `c429b585f2ce038010aefef6b36677665caa5c67`

**Workflow:** `automation/n8n/line_uat_approval_demo.json`

**n8n version:** `2.37.10`

> THIS WORKFLOW IS UAT ONLY. NO REAL CUSTOMER DATA. NO PRODUCTION SENDING.

## 1. Executive result

Hai scenario bắt buộc đã được chạy qua n8n Manual Trigger và Human Approval Gate thực tế trên local runtime:

- Scenario A: human chọn `REJECT`; execution kết thúc ở reject branch.
- Scenario B: human đọc exact proposed message, chọn `APPROVE`, xác nhận synthetic UAT; Django send endpoint trả kết quả dry-run do kill switch tắt.

Một compatibility bug của n8n Wait Form đã được phát hiện trong lần chạy đầu, sửa bằng patch nhỏ, thêm regression test và commit riêng. Sau fix, hai execution chính thức đều có trạng thái n8n `success`.

Không có LINE provider request trong toàn bộ dry-run.

## 2. Repository pre-flight

Pre-flight xác nhận:

- Branch đúng: `feature/n8n-line-uat-demo`.
- HEAD chứa hardening commit `c429b585...`.
- Không merge `main`.
- Không push remote.
- Không reset hoặc overwrite thay đổi ngoài scope.
- Workflow ở trạng thái `active=false` khi import và chạy manual.

## 3. Safe runtime configuration

Django được bind cục bộ tại `127.0.0.1:8000` với database SQLite UAT tạm riêng.

Runtime safety configuration:

```text
LINE_SEND_ENABLED=false
LINE_UAT_CHANNEL_ACCESS_TOKEN=
LINE_UAT_CHANNEL_SECRET=
LINE_UAT_RECIPIENT_USER_ID=UAT-LINE-USER-SYNTHETIC-001
```

Không sử dụng token LINE thật, LINE user ID thật hoặc dữ liệu khách hàng thật.

n8n được bind tại `127.0.0.1:5678`, dùng database/user folder tạm riêng. Foundation bearer token và n8n owner đều là synthetic, local-only, short-lived và không được ghi vào repository.

## 4. Django startup evidence

Migration được chạy trên database UAT tạm:

```text
Applying ai_agent.0004_line_uat_send_hardening... OK
Applying foundation.0011_line_uat_permissions... OK
System check identified no issues (0 silenced).
```

Django development server chỉ listen trên `127.0.0.1:8000`.

## 5. Temporary authorization

Một Foundation principal tạm role `manager` được tạo trong database UAT với đúng bốn permission:

- `ai_sales:read`
- `sales:read`
- `line_uat:read`
- `line_uat:approve`

Token raw không được lưu trong repository. Foundation chỉ lưu SHA-256 token hash. Token tạm được gia hạn một lần khi phiên dry-run kéo dài quá thời hạn ban đầu.

## 6. n8n startup and import

Isolated n8n instance khởi động local với version `2.37.10`.

Import result:

```text
Importing 1 workflows...
Successfully imported 1 workflow.
```

Tên workflow được xác minh trong UI:

```text
UAT - AI Sales LINE Approval Demo
```

## 7. Topology pre-flight

Workflow JSON được kiểm tra trước execution:

- Không chứa `api.line.me`.
- Không chứa `LINE_UAT_CHANNEL_ACCESS_TOKEN`.
- Không chứa `LINE_UAT_CHANNEL_SECRET`.
- Không có LINE node hoặc LINE credential.
- Chỉ có Authorization expression trỏ tới temporary Django bearer token.
- Send path là `n8n -> Django send endpoint`; n8n không gọi provider trực tiếp.

## 8. Network instrumentation

Django được chạy với `HTTPS_PROXY=http://127.0.0.1:18081`, trỏ vào một local proxy spy chỉ ghi số kết nối. Spy bắt đầu với:

```text
PROXY_SPY_READY provider_call_count=0
```

Trong Scenario A, Scenario B và negative runtime check, spy không ghi nhận bất kỳ `PROXY_SPY_CONNECTION` nào. Do đó provider call count cuối cùng là `0`.

n8n có các background attempt riêng tới `api.n8n.io`/n8n community metadata và bị môi trường chặn `EACCES`. Những attempt này không liên quan LINE và không đi qua Django provider adapter. Không có log hoặc network evidence nào chứa `api.line.me`.

## 9. Scenario A — human REJECT

### Steps

1. Chạy workflow bằng Manual Trigger.
2. Workflow tạo draft mới từ fixture cố định:
   - `rfq_id=UAT-RFQ-001`
   - `synthetic=true`
   - `environment=uat`
3. Draft qua validation với `status=PENDING` và `autonomous_action=false`.
4. Human Approval Gate hiển thị exact proposed message.
5. Human chọn `REJECT`.
6. n8n đi vào `Persist REJECTED - No Send` và không có edge tiếp theo tới send node.

### Runtime identity

```text
n8n execution ID: 5
approval UUID: 3b4a49c5-73c7-4e08-b64b-86e8350564f6
```

### Final database state

```json
{
  "status": "REJECTED",
  "line_result_status": "REJECTED_NO_SEND",
  "send_attempted": false,
  "send_claimed_at": null,
  "sent_at": null,
  "provider_message_id": null
}
```

n8n execution `5` kết thúc `success`.

### Provider evidence

- Provider call count: `0`.
- Proxy spy connection count: `0`.
- Send endpoint không nằm trên reject branch.

## 10. Scenario B — human APPROVE with kill switch disabled

### Steps

1. Chạy Manual Trigger lần mới; không reuse record REJECTED.
2. Workflow tạo draft mới cho cùng synthetic fixture.
3. Human đọc exact proposed LINE message.
4. Human chọn `APPROVE`.
5. Human chủ động bỏ rồi tick lại acknowledgement `I confirm this is synthetic UAT data`.
6. Workflow gọi Django approve endpoint, re-fetch record và kiểm tra safety state.
7. Workflow gọi Django send endpoint.
8. Django thấy `LINE_SEND_ENABLED=false`, trả `SEND_DISABLED` trước provider adapter.

### Runtime identity

```text
n8n execution ID: 6
approval UUID: 26aa4f92-e627-4f9e-9b32-b3be3804c2ba
```

### Final database state

```json
{
  "status": "APPROVED",
  "line_result_status": "SEND_DISABLED",
  "send_attempted": false,
  "send_claimed_at": null,
  "sent_at": null,
  "provider_message_id": null,
  "provider_response": {
    "mode": "DRY_RUN",
    "send_attempted": false
  }
}
```

n8n execution `6` kết thúc `success`.

### Provider evidence

- Provider call count: `0`.
- Proxy spy connection count: `0`.
- Không tạo send claim.
- Không có provider request ID.

## 11. Approved text integrity

Exact message human đã nhìn thấy và record lưu sau approve:

```text
[UAT / SYNTHETIC — NO REAL CUSTOMER]
UAT Tanaka Manufacturing 様
SUS304 Precision Bracket 100個のお問い合わせありがとうございます。内容を確認し、担当者よりご案内いたします。
社内確認区分: ESCALATE_ENGINEERING_REVIEW
※これはUATテストメッセージです。
```

Approved content hash:

```text
4972db168edbf5435b25456712fe6f1126e8f60587cca71586b9eee7f970418f
```

Hash được tính lại sau execution từ channel, environment, exact message, recipient reference, RFQ ID và synthetic marker. Kết quả `hash_recomputed_match=true`.

Không có regenerate hoặc mutate message sau approval.

## 12. Negative runtime check

Gọi Django send endpoint cho Scenario A đã `REJECTED`:

```json
{
  "http_status": 409,
  "error_code": "not_approved"
}
```

Record không bị mutate và provider call count vẫn là `0`.

## 13. Log and secret review

Django console log chỉ ghi safe route/status events, ví dụ draft, approve, reject, re-fetch và send endpoint status.

Không quan sát thấy:

- LINE access token
- LINE channel secret
- Foundation bearer token đầy đủ
- Authorization header

Raw-byte scan trên Django UAT SQLite và n8n SQLite cho synthetic Foundation bearer token đều trả `False`.

Approval UUID, route, HTTP status và safe application warnings có xuất hiện như dự kiến.

## 14. Runtime finding and root cause

Lần Scenario B đầu tiên trước fix đã fail-closed vào reject branch dù human chọn approve.

Runtime evidence từ n8n `2.37.10` cho thấy Wait Form trả payload theo label:

```text
Decision = "APPROVE"
I confirm this is synthetic UAT data = [""]
Review note = "..."
```

Workflow cũ chỉ đọc:

```text
decision
uat_acknowledged == true
review_note
```

Vì vậy boolean strict condition không match. Record bị REJECTED an toàn; không có send attempt hoặc provider request.

## 15. Fix applied

Fix nhỏ nhất:

- Decision condition hỗ trợ cả `decision` và runtime label `Decision`.
- Acknowledgement hỗ trợ boolean field-name output và checked array label output.
- Reject reason hỗ trợ cả `review_note` và label `Review note`.
- Vẫn yêu cầu decision chính xác `APPROVE` và acknowledgement có giá trị.
- Bổ sung regression assertions cho runtime label compatibility.

Fix commit:

```text
c15f235b588e6a33a8bfd1e62485edab9a22c184
fix(line-uat): address dry-run UAT finding
```

## 16. Non-product runtime interruptions

Hai lần chạy không được tính là Scenario A/B chính thức:

- Một execution dừng trước draft vì Django local process đã kết thúc giữa hai task turns.
- Một execution dừng trước draft vì temporary bearer token hết hạn.

Cả hai đều fail trước khi tạo approval/send attempt, không gọi LINE và không phải defect sản phẩm. Django được restart local và token synthetic được gia hạn trong database UAT tạm trước khi chạy execution `5` và `6`.

## 17. Automated verification

Full relevant test run:

```text
83 passed in 15.81s
```

Command:

```text
python -m pytest tests/test_line_uat_approval.py tests/test_ai_sales_mvp.py tests/test_sales_crm_ai.py -q
```

Additional checks:

```text
python django_backend/manage.py check
System check identified no issues (0 silenced).

python -m ruff check tests/test_line_uat_approval.py django_backend/apps/ai_agent/services/line_uat.py django_backend/apps/ai_agent/line_uat_views.py
All checks passed!

python -m json.tool automation/n8n/line_uat_approval_demo.json
PASS
```

Focused test run immediately after fix:

```text
54 passed in 16.02s
```

## 18. Bugs and fixes summary

| Severity | Finding | Safety outcome | Resolution |
|---|---|---|---|
| Medium | n8n 2.37.10 Wait Form returns label keys and checkbox array | Fail-closed to REJECT; zero send | Fixed and regression-tested in `c15f235` |

Không có Critical hoặc High finding trong runtime dry-run.

## 19. Unresolved risks

- n8n imports made before owner initialization can emit local project-permission warnings. Manual executions vẫn chạy thành công; production-like deployment cần import vào đúng owner/project.
- n8n attempted optional metadata/community registry requests at startup. Network policy blocked them. A hardened UAT deployment should explicitly disable all optional outbound metadata services supported by its n8n version.
- This run proves kill-switch-off behavior only. It does not authorize enabling LINE or prove delivery behavior with a real LINE credential.
- The previously documented at-most-once `SENDING` reconciliation risk applies only when sending is explicitly enabled; it was not exercised here.

## 20. Safety assertions

- `LINE_SEND_ENABLED` was never set to `true`.
- No LINE access token was configured.
- No real LINE recipient was configured.
- No real customer data was used.
- No request to `api.line.me` was observed.
- No merge was performed.
- No push was performed.

## 21. Final verdict

```text
SCENARIO A: PASS

SCENARIO B: PASS

NO LIVE LINE REQUEST OBSERVED: YES

READY FOR LINE UAT MANUAL CONFIGURATION: YES
```

`READY FOR LINE UAT MANUAL CONFIGURATION: YES` chỉ có nghĩa là dry-run safety gate đã đạt và có thể chuyển sang bước cấu hình thủ công có kiểm soát. Nó không phải authorization để bật `LINE_SEND_ENABLED=true`, nhập credential thật hoặc gửi LINE.
