# Phase 5C Canonical RFQ Corrective Patch Report

## 1. Thông tin chung

- Repository: `Django-web-t-123`
- Branch: `codex/demo-database-validation`
- Phạm vi: canonical RFQ frontend và focused Phase 5C tests
- Ngày báo cáo: 2026-09-16
- Trạng thái: hoàn tất
- Commit: không tạo commit

Corrective patch này chỉ xử lý ba vấn đề:

1. cô lập RFQ workspace state giữa các authentication session;
2. bảo vệ canonical RFQ-line unit protocol theo hướng fail-closed;
3. thống nhất business-calendar date theo `Asia/Tokyo`.

Không triển khai Phase 6B và không chỉnh Docker/runtime hoặc các write surface ngoài canonical RFQ Phase 5C.

## 2. Files thay đổi

- `figma_make_frontend/src/api/rfqCommands.ts`
- `figma_make_frontend/src/components/RfqWorkspace.tsx`
- `figma_make_frontend/src/api/phase5c.test.ts`

Các thay đổi khác đang tồn tại trong working tree không thuộc corrective patch này và không bị chỉnh sửa.

## 3. Session-boundary isolation

### Root cause

`RfqWorkspace` có thể tiếp tục được mount khi `authenticated` chuyển từ `true` sang `false`. Nhánh unauthenticated trước đây chỉ reset selector presentation state. Các dữ liệu mutable khác vẫn tồn tại trong component và helper closure:

- selected RFQ;
- RFQ lines;
- header và line forms;
- editing line ID;
- command/reconciliation state;
- active command gate;
- retained create payload;
- retained idempotency key;
- RFQ ID của create attempt đã POST thành công nhưng chưa reconcile xong.

Vì vậy một authentication session mới có khả năng nhìn thấy hoặc retry logical create operation của session cũ.

### Fix

- Thêm operation `clear()` vào `createRfqCreateAttemptManager()`.
- Khi `authenticated === false`, workspace thực hiện:
  - abort active workspace request;
  - xóa active abort reference;
  - invalidate workspace request generation;
  - invalidate selector request generation;
  - clear retained create attempt;
  - thay command gate bằng gate mới để pending state cũ không chặn session mới;
  - clear canonical selectors;
  - clear selected RFQ;
  - clear RFQ lines;
  - clear editing line ID;
  - reset header form;
  - reset line form;
  - reset command state về `initial`;
  - reset selector state về `initial`.
- Request cũ vẫn chịu abort và stale-response guard nên không thể ghi state trở lại sau reset.
- Create attempt cũ không được tự động retry dưới authentication session mới.

### Idempotency guarantees được giữ nguyên

- Ambiguous retry trong cùng session vẫn dùng cùng retained payload và idempotency key.
- Nếu POST create đã trả RFQ ID nhưng reconciliation thất bại, retry vẫn chỉ thực hiện GET reconciliation và không POST create lần hai.
- Session reset chủ động xóa context cũ để không mang idempotency key hoặc payload sang identity mới.

## 4. Canonical RFQ-line unit protocol integrity

### Root cause

Command contract chỉ hỗ trợ bốn RFQ units:

- `PCS`
- `KG`
- `M`
- `MM`

Tuy nhiên `isCanonicalRfqLine()` trước đây chỉ kiểm tra `typeof unit === "string"`. Do đó backend response như `unit: "BOX"` vẫn vượt qua canonical guard. Sau đó `lineFromRfq()` âm thầm đổi unit không nhận diện được thành `PCS`, làm biến đổi server data trước khi đưa vào editable form.

### Fix

- `CanonicalRfqLine.unit` được đổi từ `string` sang `RfqUnit`.
- Thêm internal type guard `isRfqUnit()` sử dụng đúng allowlist hiện có.
- `isCanonicalRfqLine()` chỉ chấp nhận `PCS`, `KG`, `M`, `MM`.
- `lineFromRfq()` dùng trực tiếp canonical unit đã được guard xác nhận.
- Xóa toàn bộ fallback chuyển unit lạ thành `PCS`.
- Invalid unit từ cả GET line page và command response đều phát sinh sanitized canonical protocol error trước khi dữ liệu đi vào form state.

Không thay đổi supported units hoặc command payload contract.

## 5. Business-calendar date handling

### Existing convention được kiểm tra

Backend Django có:

```text
TIME_ZONE = Asia/Tokyo
USE_TZ = True
```

RFQ command service dùng `timezone.localdate()` cho business validation.

Frontend trước đây dùng:

```ts
new Date().toISOString().slice(0, 10)
```

Biểu thức này lấy UTC calendar date. Trong khoảng từ 00:00 đến 08:59 tại Tokyo, UTC date vẫn là ngày hôm trước và có thể làm create/update/submit validation trễ một ngày.

### Fix

- Thêm helper testable:

```ts
businessCalendarDate(instant?, timeZone?)
```

- Default timezone là `Asia/Tokyo`.
- Helper sử dụng `Intl.DateTimeFormat().formatToParts()` để tạo deterministic `YYYY-MM-DD`.
- Không thêm date library hoặc dependency mới.
- Default `today` của create/update validators dùng helper mới.
- `RfqWorkspace` dùng cùng helper cho:
  - create validation;
  - update validation;
  - submit due-date validation.
- Các tham số `today` explicit trong validators vẫn được giữ để tests và callers có thể inject deterministic date.

Lưu ý: `toISOString()` còn xuất hiện bên trong `dateValue()` chỉ để kiểm tra một chuỗi `YYYY-MM-DD` có đại diện cho ngày hợp lệ hay không. Nó không còn được dùng để xác định business “today”.

## 6. Tests bổ sung

### Session isolation

- Active create attempt được tạo với key của session cũ.
- Attempt được đánh dấu là `created but not reconciled`.
- `clear()` xóa:
  - active attempt;
  - unreconciled RFQ identity;
  - retained payload.
- Logical create operation của session mới nhận key mới và payload mới.
- Workspace unauthenticated branch được kiểm tra có đầy đủ abort, guard invalidation và state resets.

### Unit protocol

- `isCanonicalRfqLine()` reject response có `unit: "BOX"`.
- GET RFQ lines với `BOX` trả `invalid_rfq_line_page` protocol error.
- Add-line command response với `BOX` trả `invalid_rfq_line_response` protocol error.
- Không có normalization sang `PCS`.

### Business calendar

Boundary instant:

```text
2026-09-15T15:30:00.000Z
```

Assertions:

- UTC calendar date: `2026-09-15`;
- Asia/Tokyo business date: `2026-09-16`;
- UTC override vẫn trả `2026-09-15`;
- create validation dùng Tokyo date và reject ngày giao `2026-09-15` vì đã thuộc ngày trước theo business calendar.

## 7. Validation results

Tất cả validation được chạy sau thay đổi cuối cùng.

| Validation | Kết quả |
| --- | --- |
| `pnpm run test:phase5c` | PASS — 34/34 tests |
| `pnpm run test` | PASS — 128/128 tests |
| `pnpm run test:phase5a` | PASS — 12/12 tests |
| `pnpm run test:phase5b` | PASS — 18/18 tests |
| `pnpm run typecheck` | PASS |
| Focused formatter check trên ba file | PASS — unchanged |
| `git diff --check` | PASS |

Full frontend suite hiện bao gồm Phase 5A–5E và các config tests đã được repository định nghĩa. Corrective patch không sửa Phase 6 files dù full test script có chạy các config tests hiện có.

`git diff --check` có in cảnh báo LF → CRLF cho các working-tree files hiện có, nhưng không có whitespace error và exit code là `0`.

## 8. Preserved guarantees

- Canonical-only RFQ endpoints được giữ nguyên.
- Same logical ambiguous create retry vẫn dùng cùng idempotency key.
- Create đã thành công nhưng reconciliation thất bại vẫn chỉ GET lại theo RFQ ID đã biết.
- Latest-request stale-response protection được giữ nguyên.
- Authentication failure callback được giữ nguyên.
- DRAFT lifecycle locking được giữ nguyên.
- Backend field errors tiếp tục được sanitize và allowlist.
- Không thêm `localStorage`, `sessionStorage`, IndexedDB hoặc cookie persistence.
- Không persist token, RFQ state, idempotency key hoặc retained payload.
- Không thêm quotation/order/progress/audit write commands.
- Không thêm dependency.

## 9. Git và scope confirmation

- Không stage.
- Không commit.
- Không push.
- Không reset.
- Không clean.
- Không stash.
- Không sửa backend.
- Không sửa migrations.
- Không sửa Docker/runtime.
- Không bắt đầu Phase 6B.

## 10. Kết luận

Ba correctness issue đã được xử lý theo hướng fail-closed và session-safe. Canonical RFQ workflow, request race protection và create idempotency guarantees vẫn được giữ. Focused Phase 5C tests, full frontend suite, typecheck, formatter check và diff check đều pass. Không còn blocker trong phạm vi task này.
