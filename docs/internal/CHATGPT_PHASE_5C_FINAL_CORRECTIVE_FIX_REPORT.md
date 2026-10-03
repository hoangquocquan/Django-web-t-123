# ChatGPT Phase 5C Final Corrective Fix Report

## Mục đích

Báo cáo này bàn giao cho ChatGPT phần final corrective fix của Phase 5C. Phạm vi implementation chỉ gồm customer selector trong create retry flow và regression test tương ứng.

## Repository state

- Repository: `Django-web-t-123`
- Branch: `codex/demo-database-validation`
- HEAD: `2f4d8d87d11b41b944ad750cc643e5104e27b694`
- HEAD subject: `phase5b: connect foundation login and rfq read screen`
- Commit mới cho corrective fix: không
- Staged files: không

## Bug đã sửa

Khi một logical create attempt vẫn còn active sau lỗi ambiguous của POST create hoặc reconciliation, các header fields thông thường đã bị khóa nhưng customer selector vẫn có thể thay đổi.

Retry vẫn sử dụng payload và idempotency key được lưu trong active create attempt. Vì vậy customer hiển thị trên UI có thể khác với `customer_id` thực sự được gửi lại, phá vỡ invariant giữa UI state và retained retry payload.

## Exact files changed cho corrective fix

1. `figma_make_frontend/src/components/RfqWorkspace.tsx`
2. `figma_make_frontend/src/api/phase5c.test.ts`

File báo cáo này được tạo riêng theo yêu cầu bàn giao và không phải implementation change.

## Exact code fix

Customer selector trước đây dùng:

```tsx
disabled={!selectorsReady || selectedRfq !== null || pending}
```

Sau corrective fix:

```tsx
disabled={
  !selectorsReady ||
  selectedRfq !== null ||
  pending ||
  activeCreateAttempt
}
```

Kết quả:

- Selector tiếp tục bị khóa trong lúc selector data chưa sẵn sàng.
- Selector tiếp tục bị khóa khi đang xem hoặc sửa một selected RFQ.
- Selector tiếp tục bị khóa khi command đang pending.
- Selector mới được khóa thêm trong toàn bộ thời gian logical create attempt còn active.
- Normal create flow không đổi semantics.
- Edit mode của selected DRAFT RFQ không bị ảnh hưởng.
- Selector loading behavior không bị thay đổi.

## Regression test đã thêm

Test mới:

```text
active create attempt locks the customer selector to its retained payload
```

Test xác nhận:

- `createRfqCreateAttemptManager.begin(payload)` tạo active attempt.
- `hasActiveAttempt()` trả về `true`.
- `activePayload()` vẫn là payload gốc được giữ cho retry.
- Customer selector trong `RfqWorkspace` sử dụng `activeCreateAttempt` trong điều kiện `disabled`.

Test component tương tác trực tiếp không được thêm vì test architecture hiện tại sử dụng Node test thuần và không có DOM/jsdom hoặc component renderer. Regression test vì vậy kết hợp behavior thật của create-attempt manager với kiểm tra wiring giới hạn đúng customer-selector block.

Toàn bộ test hiện có được giữ lại.

## Validation results

Các lệnh yêu cầu đã chạy thành công sau khi format:

- `pnpm --dir figma_make_frontend run typecheck`: PASS
- `pnpm --dir figma_make_frontend run typecheck:phase5a`: PASS
- `pnpm --dir figma_make_frontend run test:phase5a`: PASS, 12/12
- `pnpm --dir figma_make_frontend run test:phase5b`: PASS, 18/18
- `pnpm --dir figma_make_frontend run test:phase5c`: PASS, 30/30
- `pnpm --dir figma_make_frontend run test`: PASS, 60/60
- `pnpm --dir figma_make_frontend run build`: PASS
- `git diff --check`: PASS
- `oxfmt --check` trên hai implementation/test files: PASS

## Scope confirmations

- Backend changes cho corrective fix: không
- Migration changes: không
- API contract changes: không
- Dependency hoặc lockfile changes cho corrective fix: không
- Các màn hình khác bị sửa bởi corrective fix: không
- Commit được tạo: không
- Existing working-tree changes ngoài scope: được giữ nguyên, không chỉnh sửa hoặc hoàn tác

## Invariant sau fix

Khi `activeCreateAttempt === true`, customer selector và các header fields thuộc logical create payload đều không thể bị user thay đổi. Payload hiển thị trên UI vì vậy tiếp tục khớp với retained payload mà retry sử dụng.
