# PHASE 1 — ADMIN API INTEGRATION REPORT

Ngày kiểm tra: 2026-09-20 (Asia/Tokyo)

## 1. Kết quả

React Admin đã được chuyển từ dữ liệu mock sang các Admin API thật cho Dashboard,
Products, Customers, Inventory, Orders, Workflows và Transactions. Không thay đổi
Django business logic, model, migration hoặc dữ liệu database. Không triển khai
Create/Edit/Delete và không triển khai Phase 2.

Các list API được đọc theo toàn bộ pagination (`limit=100`, tiếp tục theo
`next_offset`) thay vì chỉ hiển thị page mặc định 20 records. Bearer token tiếp tục
lấy từ `InMemoryAuthSession`; frontend không lưu token và không bypass permission.

## 2. File đã sửa/tạo

| File | Thay đổi |
| --- | --- |
| `figma_make_frontend/src/services/adminApi.ts` | API service layer, auth header, timeout/error handling, full pagination và mapping |
| `figma_make_frontend/src/types/admin.ts` | TypeScript interfaces: Product, Customer, InventoryItem, Order, Workflow, Transaction, Dashboard |
| `figma_make_frontend/src/services/adminApi.test.ts` | Test pagination, mapping, auth, dashboard và lỗi API mô phỏng |
| `figma_make_frontend/src/App.tsx` | Thay nguồn mock Admin bằng API state; giữ DataTable, board, layout và routes hiện tại |
| `figma_make_frontend/.env.example` | Khai báo `VITE_API_BASE_URL=/` theo API-root contract hiện hữu |
| `figma_make_frontend/package.json` | Thêm test Admin API vào full frontend suite |
| `PHASE1_ADMIN_API_INTEGRATION_REPORT.md` | Báo cáo này |

File local `figma_make_frontend/.env.local` (được git-ignore) được đặt
`VITE_API_BASE_URL=/` để chạy qua Vite proxy tại local. Production/staging phải
cấp biến này từ environment tương ứng.

## 3. Endpoint đã dùng

| Màn hình | Method/endpoint |
| --- | --- |
| Dashboard | `GET /api/v1/admin/dashboard/` |
| Products | `GET /api/v1/admin/products/` |
| Customers | `GET /api/v1/admin/customers/` |
| Inventory | `GET /api/v1/admin/inventory/items/` |
| Orders | `GET /api/v1/admin/orders/` |
| Workflows | `GET /api/v1/admin/workflows/` |
| Transactions | `GET /api/v1/admin/transactions/` |

Mọi request đều gửi `Authorization: Bearer <token>` từ auth flow hiện tại. Kiểm
tra runtime không có token cho thấy cả 7 endpoint trả `403`; UI hiển thị error
state “Vui lòng đăng nhập để tải dữ liệu.”

## 4. Mapping frontend/backend

Giá trị `Chưa có dữ liệu` được dùng khi API không trả field tương ứng; không tạo
hoặc tự tính dữ liệu giả.

| Frontend | Backend | Ghi chú |
| --- | --- | --- |
| Product.code | `sku` | DB hiện có nhiều SKU rỗng |
| Product.name | `name` | Mapping trực tiếp |
| Product.material | Không có | `Chưa có dữ liệu`; không dùng nhầm category làm material |
| Product.tolerance | Không có | `Chưa có dữ liệu` |
| Product.status | `status` | Mapping trực tiếp |
| Customer.name | `company_name`, fallback `contact_name` | Mapping trực tiếp |
| Customer.industry | `notes` với marker `industry=...` | Dữ liệu seed thật, không tạo mới |
| Customer.projects | Không có trong response | `Chưa có dữ liệu` |
| Customer.value | Không có trong response | `Chưa có dữ liệu` |
| Customer.status | `status` | Mapping trực tiếp |
| Inventory.materialCode | `product.sku` | Mapping trực tiếp |
| Inventory.description | `product.name` | Mapping trực tiếp |
| Inventory.quantity | `quantity` | Mapping trực tiếp |
| Inventory.unit | Không có | `Chưa có dữ liệu` |
| Inventory.status | Không có | `Chưa có dữ liệu`; không tự suy diễn từ reorder point |
| Order.orderNumber | `order_number` | Mapping trực tiếp |
| Order.customer | `customer_name` | Mapping trực tiếp |
| Order.progress | Không có | `Chưa có dữ liệu` |
| Order.deliveryDate | Không có | `Chưa có dữ liệu` |
| Order.status | `status` | Mapping trực tiếp |
| Workflow | `order_id`, `requested_status`, `decision`, `requested_by`, `reviewed_by`, `note` | Group board theo decision thật |
| Transaction.code | `legacy_event_id`, fallback `id` | Không thêm prefix giả |
| Transaction.date | `created_at` | Format `vi-VN` |
| Transaction.type | `action` | Mapping trực tiếp |
| Transaction.partner | `actor` | Field gần nhất API cung cấp |
| Transaction.value | `payload.value` | Thiếu thì `Chưa có dữ liệu` |
| Transaction.status | `payload.status` | Thiếu thì `Chưa có dữ liệu` |
| Dashboard | `metrics.*` | Hiển thị đủ 6 count backend; xóa KPI 8,42 tỷ/38/87,6%/98,7% |

## 5. Loading, empty và error state

- Loading: hiển thị `Đang tải dữ liệu…` trong khung nội dung hiện tại.
- Empty: message riêng cho từng module; workflow và transactions có 0 record nên
  không còn card/row mock.
- Error/auth/permission/network/timeout: message được sanitize và hiển thị bằng
  `role="alert"`; không render mock fallback.
- Dashboard chart “Sản lượng 30 ngày” và “Cảnh báo” giữ khung layout nhưng hiển
  thị `Chưa có dữ liệu` vì endpoint chưa cung cấp hai dataset này.

## 6. Vấn đề phát hiện

1. Admin API thiếu nhiều field mà UI đang có cột: material, tolerance, project
   count/value, inventory unit/status, order progress/delivery date và transaction
   partner/value/status có cấu trúc rõ ràng. Phase 1 không sửa backend nên các ô
   này hiển thị `Chưa có dữ liệu`.
2. Local database đọc ngày 2026-09-20 có: Products 601, Customers 201, Inventory
   Items 900, Orders 450, WorkflowApproval 0, TransactionHistory 0.
3. Flow auth hiện hữu cố ý giữ token trong memory. Hard refresh xóa token, vì vậy
   người dùng phải đăng nhập lại trước khi API được tải lại. Không thêm
   localStorage/sessionStorage vì sẽ thay đổi security contract hiện tại và làm
   hỏng test Phase 5B/6C về memory-only auth.
4. Local hiện không có `PHASE6B_E2E_PASSWORD` hoặc credential login-ready được
   phê duyệt. Không reset password, không tạo user và không seed thêm dữ liệu để
   phục vụ test.

## 7. Screenshot trước/sau

### Trước

Không có runtime đang chạy tại thời điểm `SYSTEM_DATA_FLOW_AUDIT.md`, nên không có
ảnh “trước” hợp lệ để lưu. Bằng chứng trước thay đổi là source/audit: Products 4
rows, Customers 4 rows, Inventory 4 rows, Orders 3 rows, Workflow 9 mock cards,
Transactions 3 rows và 4 KPI hard-code. Không dựng lại ảnh giả sau khi code đã đổi.

### Sau

Đã chụp trực tiếp bằng Codex in-app browser tại
`http://127.0.0.1:8443/#/admin-products`. Ảnh runtime cho thấy layout Admin cũ,
route cũ và error state rõ ràng “Vui lòng đăng nhập để tải dữ liệu.”, không còn 4
product mock xuất hiện khi chưa authenticated. Ảnh được đính kèm inline trong task
review; công cụ browser hiện tại không xuất ảnh chụp thành file workspace.

Ảnh dữ liệu sau đăng nhập chưa thể chụp vì thiếu credential usable nêu ở mục 6;
không bypass permission để tạo ảnh.

## 8. Test result

| Test | Kết quả |
| --- | --- |
| `npm run typecheck` | PASS |
| `npm run build` | PASS |
| `npm test` | PASS — 150/150 |
| `node --test src/services/adminApi.test.ts` | PASS — 5/5 |
| `python -m pytest apps/api/tests -q` | PASS — 69 passed, 49 skipped |
| Read-only DB count | PASS — 601 / 201 / 900 / 450 / 0 / 0 |
| Live endpoint request không token | PASS — 7/7 trả 403 |
| Products không còn 4 mock | PASS bằng source/test; UI unauth không render mock fallback |
| Customers không còn 4 mock | PASS bằng source/test |
| Orders phản ánh DB | PASS ở service pagination contract; live authenticated browser bị chặn bởi credential |
| Refresh browser | PARTIAL — UI reload đúng nhưng token memory-only bị xóa; cần login lại |
| API error simulation | PASS — HTTP 500 được map thành server error và UI error state |

## 9. Kết luận review

Implementation Phase 1 đã hoàn tất trong phạm vi frontend và không làm thay đổi
database/Django business logic. Review cần quyết định riêng về (a) bổ sung các
field còn thiếu vào API ở phase sau và (b) chiến lược auth qua hard refresh. Không
tự mở rộng hai nội dung này trong Phase 1.
