# Phase 5C Corrective Patch Report

## 1. Thông tin thực hiện

- Repository: `Django-web-t-123`
- Branch: `codex/demo-database-validation`
- Phase: Phase 5C — RFQ Draft, Line Editing, and Submission UI
- Ngày báo cáo: 2026-09-13
- Phạm vi: frontend Sales RFQ
- Commit: không tạo commit

## 2. Files được thay đổi bởi corrective patch

- `figma_make_frontend/src/api/rfqCommands.ts`
- `figma_make_frontend/src/components/RfqWorkspace.tsx`
- `figma_make_frontend/src/api/phase5c.test.ts`

Repository đã có các thay đổi/untracked files khác trước corrective patch. Các thay đổi ngoài ba file trên không thuộc patch này và không bị chỉnh sửa trong quá trình sửa lỗi.

## 3. Root cause và corrective fix

### 3.1. Create RFQ kết thúc idempotency attempt quá sớm

#### Root cause

Create flow gọi `createAttempt.settle(true)` ngay sau khi POST create trả RFQ thành công. Idempotency key và retry context bị xóa trước khi GET detail và GET lines hoàn tất. Nếu reconciliation timeout hoặc gặp network error, lần retry tiếp theo có thể tạo key mới và POST create lần nữa, dẫn đến duplicate RFQ.

#### Fix

- Bổ sung create-attempt lifecycle giữ các dữ liệu:
  - payload gốc;
  - idempotency key;
  - RFQ ID sau khi POST create thành công;
  - trạng thái active/reconciled/definitively failed.
- Thêm `executeRfqCreateAttempt()` để điều phối POST và reconciliation như một logical operation duy nhất.
- Chỉ complete và xóa attempt sau khi reconciliation thành công.
- Nếu đã có RFQ ID nhưng reconciliation thất bại, lần retry tiếp theo chỉ reconcile lại đúng RFQ ID đó và không POST create lần hai.
- Nếu POST có ambiguous timeout/network outcome, client giữ nguyên payload và idempotency key cho retry.
- Validation, permission hoặc kết quả definitive khác có thể kết thúc attempt theo error contract hiện có.
- Form create và RFQ navigation bị khóa trong khi còn active create attempt, tránh vô tình thay payload hoặc bắt đầu logical operation khác.
- Cancellation và stale-response checks vẫn được giữ nguyên.

### 3.2. Unsafe retry messaging cho command không-idempotent

#### Root cause

Thông báo timeout/network dùng câu tương đương “có thể thử lại an toàn” cho mọi RFQ command, trong khi backend chỉ chứng minh `Idempotency-Key` cho create RFQ. Update header, add/update/remove line và submit không có idempotency guarantee tương ứng.

#### Fix

- Thay timeout/network message bằng:

  > Không xác định được lệnh RFQ đã được xử lý hay chưa. Hãy tải lại trạng thái RFQ trước khi thử lại.

- Không thêm `Idempotency-Key` vào endpoint chưa hỗ trợ và không thay đổi API contract.
- Sau ambiguous outcome của mutation trên RFQ hiện có, header, line mutations và submit bị khóa.
- UI hiển thị action tải lại trạng thái RFQ để reconciliation trước khi người dùng tiếp tục.
- Create RFQ vẫn có thể retry với đúng idempotency context đã giữ lại.

### 3.3. Selector và workspace dùng chung stale-request guard

#### Root cause

Selector loading và RFQ open/reconciliation cùng tăng một request generation. Open RFQ có thể làm selector response hợp lệ bị coi là stale, khiến selector state mắc ở `loading_selectors`.

#### Fix

- Tách hai request domain độc lập:
  - `selectorGuard` cho selector loading/reloading;
  - `workspaceGuard` cho open, command reconciliation và navigation RFQ.
- Workspace request không invalidate selector request.
- Selector reload mới chỉ invalidate selector reload cũ.
- Workspace navigation/reconciliation mới chỉ invalidate workspace request cũ.
- Unmount vẫn abort active request và invalidate cả hai guard.

### 3.4. Header update thiếu cross-field validation

#### Root cause

`validateRfqUpdatePayload()` chỉ validate từng field có trong patch, trong khi create validation áp dụng date invariants trên toàn bộ form. Vì vậy update có thể tạo effective state với `quote_due_at > required_delivery_date` hoặc required delivery date trong quá khứ trước khi backend reject.

#### Fix

- Update validation nhận current RFQ dates và tính full effective state.
- Reject client-side khi:
  - `quote_due_at > required_delivery_date`;
  - effective `required_delivery_date` nằm trong quá khứ.
- `RfqWorkspace` truyền toàn bộ header form và current canonical dates vào validator.
- Invalid update dừng trước transport và không gọi API.

### 3.5. Line delivery-date validation

Source hiện tại không chứng minh business rule rằng line delivery date phải:

- không được ở quá khứ tại thời điểm chỉnh sửa; hoặc
- nhỏ hơn/bằng header required delivery date.

Backend hiện chỉ kiểm tra khi submit rằng line delivery date không được trước ngày tạo RFQ. Vì vậy corrective patch không thêm rule frontend nghiêm hơn backend. Format validation hiện có được giữ nguyên.

### 3.6. Non-DRAFT fields chưa được khóa nhất quán

#### Root cause

Save button đã bị disable ngoài `DRAFT`, nhưng một số header inputs vẫn chỉ phụ thuộc vào pending state. Người dùng có thể sửa local form dù không thể lưu. Submit cũng được render cho lifecycle không phù hợp dưới dạng disabled control.

#### Fix

- Tập trung lifecycle permissions vào helper thuần `rfqLifecyclePermissions()`.
- Header inputs bị khóa khi RFQ không phải `DRAFT`.
- Add/edit/remove line inputs và controls bị khóa cùng lifecycle.
- Pending và ambiguous reconciliation state đều khóa mutation controls.
- Submit chỉ render khi selected RFQ là `DRAFT`.
- Event handlers tiếp tục kiểm tra lifecycle, không chỉ dựa vào thuộc tính `disabled`.
- Backend vẫn là source of truth; client-side locking chỉ là UX/lifecycle guard.

## 4. Behavioral tests được bổ sung

### A. Create thành công, reconciliation thất bại, rồi retry

- POST create trả RFQ ID thành công.
- Reconciliation lần đầu timeout.
- Retry không POST create lần hai.
- Cùng RFQ ID được reconcile lại.
- Xác nhận create request count bằng 1.

### B. Logical create attempt mới

- Create và reconciliation đầu tiên hoàn tất.
- Logical create operation tiếp theo sử dụng idempotency key mới.

### C. Selector/request race

- Selector request bắt đầu trước.
- Workspace request generation tăng sau đó.
- Selector response vẫn được chấp nhận.
- Selector request mới vẫn invalidate selector request cũ đúng phạm vi.

### D. Header cross-field validation

- `quote_due_at > required_delivery_date` bị reject client-side.
- Invalid payload không gọi transport/API.

### E. Non-DRAFT edit locking

- `SUBMITTED` RFQ không có quyền sửa header.
- Line mutations và submit đều bị khóa.
- Pending state cũng khóa toàn bộ mutation permissions.

### F. Ambiguous timeout/network messaging

- Add-line timeout được mô phỏng ở transport boundary.
- UI state là timeout/unknown outcome.
- Message yêu cầu tải lại trạng thái RFQ.
- Message không chứa khẳng định “thử lại an toàn”.

Ngoài behavioral tests, các source-boundary tests hiện có vẫn được giữ để kiểm tra integration scope, auth-failure handling, không dùng browser token persistence và không mở rộng sang endpoint ngoài Phase 5C.

## 5. Kết quả validation chính xác

Tất cả command sau được chạy sau thay đổi cuối cùng và đều có exit code `0`:

| Command | Kết quả |
| --- | --- |
| `pnpm --dir figma_make_frontend run typecheck` | PASS |
| `pnpm --dir figma_make_frontend run typecheck:phase5a` | PASS |
| `pnpm --dir figma_make_frontend run test:phase5a` | PASS — 12/12 tests |
| `pnpm --dir figma_make_frontend run test:phase5b` | PASS — 18/18 tests |
| `pnpm --dir figma_make_frontend run test:phase5c` | PASS — 29/29 tests |
| `pnpm --dir figma_make_frontend run test` | PASS — 59/59 tests |
| `pnpm --dir figma_make_frontend run build` | PASS — Vite production build hoàn tất |
| `git diff --check` | PASS |

Formatter đã được chạy trên ba file frontend đã sửa:

```text
pnpm run format -- src/api/rfqCommands.ts src/components/RfqWorkspace.tsx src/api/phase5c.test.ts
```

Kết quả: cả ba file đều unchanged sau lần formatter cuối.

`git diff --check` chỉ in cảnh báo line-ending LF → CRLF cho một số tracked files đã tồn tại trước patch; không có whitespace error và exit code vẫn là `0`.

## 6. Xác nhận scope và security boundaries

- Không sửa backend.
- Không sửa migrations.
- Không thay đổi CORS hoặc CSRF.
- Không thay đổi auth persistence.
- Không thêm `localStorage`, `sessionStorage`, cookie hoặc IndexedDB token persistence.
- Không log credentials, authorization headers hoặc raw backend exceptions.
- Không thay đổi endpoint contract.
- Không thêm dependency.
- Không sửa màn hình ngoài Sales RFQ.
- Không mở rộng sang quotation, order, approval, rejection, conversion, progress hoặc audit.
- Không tạo commit.

## 7. Kết luận

Corrective patch đã đóng các lỗi correctness chính của Phase 5C liên quan đến create idempotency boundary, ambiguous command outcomes, selector/workspace races, header date validation và lifecycle locking. Toàn bộ typecheck, Phase 5A/5B/5C tests, aggregate tests, production build, formatter và diff checks đều pass.
