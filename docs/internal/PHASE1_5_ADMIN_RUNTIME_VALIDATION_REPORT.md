# PHASE 1.5 — ADMIN AUTHENTICATED RUNTIME VALIDATION REPORT

Ngày kiểm tra: 2026-09-20 (Asia/Tokyo)

## 1. Kết luận

React Admin đã được xác nhận chạy authenticated end-to-end với Django Admin API
thật. Sau khi đăng nhập hợp lệ, cả bảy route Admin đều tải được response backend;
Products, Customers, Inventory và Orders hiển thị đúng số record trong database.
Dashboard hiển thị đúng sáu counters từ API. Workflows và Transactions không còn
mock, hiển thị empty state tương ứng với database có 0 record.

Không sửa backend/API, migration, auth security model hoặc kiến trúc frontend.
Không dùng `localStorage`/`sessionStorage`, không bypass permission và không tạo
user mới.

## 2. Authentication flow hiện tại

### Login endpoint React đang dùng

```text
POST /api/v1/foundation/auth/login/
Content-Type: application/json

{
  "email": "<email>",
  "password": "<password>"
}
```

Backend cũng có `POST /api/v1/admin/login/`, nhưng React hiện tại không gọi endpoint
này. React dùng `createFoundationAuthClient()` và Foundation login endpoint.

### Tạo và xác thực token

1. `FoundationAuthService.login()` lấy active user theo email.
2. Mật khẩu được kiểm tra bằng Django `check_password()`.
3. Backend tạo raw token bằng `secrets.token_urlsafe(32)`.
4. Database chỉ lưu SHA-256 hash của token trong `foundation_auth_tokens`.
5. Token có TTL mặc định 8 giờ và chịu giới hạn active token hiện tại.
6. API request gửi header `Authorization: Bearer <token>`.
7. `FoundationBearerAuthentication` và `FoundationAuthService` kiểm tra token chưa
   hết hạn/chưa revoked trước khi permission service chạy.

### Frontend lưu token

Token chỉ được giữ trong private field của `InMemoryAuthSession`. Không có
`localStorage`, `sessionStorage`, cookie auth fallback hoặc log token. Reload cứng
trình duyệt làm mất session theo đúng security contract hiện tại.

### Permission Admin API

Các GET endpoint yêu cầu:

| Endpoint group | Permission |
| --- | --- |
| Dashboard | `dashboard:read` |
| Products | `products:read` |
| Customers | `customers:read` |
| Inventory | `inventory:read` |
| Orders | `orders:read` |
| Workflows | `workflows:read` |
| Transactions | `transactions:read` |

Role local `admin` (chữ thường) đã tồn tại và có wildcard `*:*`, vì vậy đáp ứng
toàn bộ permission trên.

## 3. Chuẩn bị môi trường test

Tài khoản E2E hiện hữu:

```text
phase6b.admin@example.invalid
```

Không tạo tài khoản mới. Trước validation, database đã có đủ ba user Phase 6B và
đủ ba fixture master-data liên quan. Tuy nhiên user trên đang gắn role `Admin`
(chữ hoa), role này chỉ có permission canonical mới và không có
`dashboard/products/customers/inventory/orders/workflows/transactions:read`.

Để tạo môi trường test hợp lệ mà không bypass permission, chỉ tài khoản E2E hiện
hữu được:

- gắn sang role `admin` đã tồn tại;
- refresh password local test bằng Django `make_password()`;
- giữ `is_active=true`;
- xóa các failed login-attempt của chính fixture email để không bị lockout.

Không thêm role, permission, user hoặc business record. Password không được ghi
vào báo cáo.

Runtime topology:

```text
Browser -> http://127.0.0.1:8443 (Vite)
        -> /api proxy
        -> http://127.0.0.1:8000 (Django development)
        -> django_backend/db.sqlite3
```

## 4. API response sample

Login response đã xác nhận HTTP 200, email đúng fixture và role `admin`. Token đã
được redacted hoàn toàn.

Dashboard response sample:

```json
{
  "success": true,
  "data": {
    "metrics": {
      "products": 601,
      "customers": 201,
      "inventory_items": 900,
      "orders": 450,
      "workflow_approvals": 0,
      "transaction_history": 0
    },
    "ownership": "django"
  }
}
```

Product page sample rút gọn:

```json
{
  "count": 601,
  "limit": 100,
  "offset": 0,
  "next_offset": 100,
  "results": [
    {
      "id": 1,
      "sku": "",
      "name": "Phase 6B Fictional Precision Bracket",
      "status": "draft"
    }
  ]
}
```

Order sample rút gọn:

```json
{
  "id": 403,
  "order_number": "SO-2026-0403",
  "customer_name": "[PDV1] Fictional Precision Buyer 23",
  "status": "new"
}
```

## 5. Runtime route validation

| Route | Kết quả browser | Evidence |
| --- | --- | --- |
| `#/admin` | PASS | 601 Products, 201 Customers, 900 Inventory, 450 Orders, 0 Workflows, 0 Transactions |
| `#/admin-products` | PASS | 601 table rows; first/last đều là DB records, không có bốn mock rows cũ |
| `#/admin-customers` | PASS | 201 table rows |
| `#/admin-inventory` | PASS | 900 table rows |
| `#/admin-orders` | PASS | 450 table rows; order number thật dạng `SO-2026-*` |
| `#/admin-workflows` | PASS | 0 rows và message `Chưa có dữ liệu quy trình.` |
| `#/admin-transactions` | PASS | 0 rows và message `Chưa có dữ liệu giao dịch.` |

Không route nào render mock fallback sau khi authenticated.

## 6. Pagination và record count

Frontend gọi Admin list API với `limit=100`, bắt đầu `offset=0` và tiếp tục theo
`next_offset` cho đến `null`. Sau đó DataTable hiện tại render toàn bộ kết quả.

| Dataset | DB count | API `count` | Page requests | Frontend DOM rows | Kết quả |
| --- | ---: | ---: | ---: | ---: | --- |
| Products | 601 | 601 | 7 | 601 | PASS |
| Customers | 201 | 201 | 3 | 201 | PASS |
| Inventory | 900 | 900 | 9 | 900 | PASS |
| Orders | 450 | 450 | 5 | 450 | PASS |
| Workflows | 0 | 0 | 1 | 0 | PASS — empty state |
| Transactions | 0 | 0 | 1 | 0 | PASS — empty state |

Như vậy Phase 1 đang “load đủ dữ liệu qua backend pagination”, chưa có pagination
controls ở UI.

## 7. Screenshot sau đăng nhập

Đã chụp trực tiếp bằng Codex in-app browser trong phiên validation:

1. Dashboard authenticated: hiển thị counters 601 / 201 / 900 / 450 / 0 / 0.
2. Products authenticated: hiển thị các row thật như
   `Phase 6B Fictional Precision Bracket`, `[PDV1] Precision bracket 1`, trạng thái
   `DRAFT`; không còn bốn sản phẩm mock cũ.

Hai ảnh được đính kèm inline trong task review. Browser capture tool hiện tại
không xuất screenshot thành file workspace; báo cáo không tạo lại ảnh giả.

## 8. Field còn thiếu

| Screen | Field UI chưa có nguồn backend tương ứng |
| --- | --- |
| Products | material, tolerance; nhiều record có `sku` rỗng |
| Customers | projects, value; industry chỉ có trong marker của `notes` ở một số seed records |
| Inventory | material code khi product SKU rỗng, unit, status |
| Orders | progress, delivery date |
| Transactions | partner/value/status chưa có contract rõ ràng; hiện DB cũng có 0 record |
| Dashboard | production 30 days và alerts |

Frontend hiển thị `Chưa có dữ liệu` cho các field này và không tự sinh giá trị.

## 9. Vấn đề phát hiện

### Role naming split

Database có đồng thời hai nhóm role:

- `Admin`, `Manager`, `Sales`: permission canonical Phase 3–6;
- `admin`, `editor`, `viewer`: permission cho Admin API legacy/Wave 5.

Tài khoản demo/production seed hiện chủ yếu dùng nhóm chữ hoa, trong khi Admin API
Phase 1 yêu cầu module permission thuộc nhóm role chữ thường. Đây là nguyên nhân
authenticated user `Admin` ban đầu vẫn bị 403; không phải lỗi token hoặc frontend.

### Rendering toàn bộ rows

API pagination hoạt động đúng, nhưng frontend gom toàn bộ page rồi render 900 rows
trong một table. Đúng yêu cầu Phase 1 về count, nhưng không tối ưu thời gian tải,
DOM size hoặc thao tác trên dataset lớn hơn.

### Header identity chưa bind session user

Header Admin vẫn hiển thị literal `Hoàng Quốc Quân` dù user authenticated thực tế
là `phase6b.admin@example.invalid` với role `admin`. Việc này không ảnh hưởng API
authorization, nhưng có thể gây hiểu nhầm khi review role/user trên UI.

## 10. Đề xuất Phase 2

1. Chuẩn hóa một permission matrix duy nhất cho Admin API và canonical API; xử lý
   rõ migration/alias giữa `Admin` và `admin` thay vì sửa từng user.
2. Bổ sung các field backend có schema chính thức: product material/tolerance,
   inventory unit/status, order progress/delivery date và transaction value/status.
3. Thêm server-side pagination controls cho DataTable; giữ `count`, `limit`,
   `offset`, `next_offset` làm source of truth thay vì tải toàn bộ dataset.
4. Thêm authenticated browser E2E dành riêng cho bảy Admin routes, với fixture
   credential được cấp qua secret environment và tuyệt đối không log token/password.
5. Quyết định riêng về reload/session UX. Nếu tiếp tục memory-only, UI cần giải
   thích rõ phải đăng nhập lại sau hard refresh; không tự thêm browser storage.
6. Bổ sung API contract tests bảo đảm Dashboard counters khớp list counts và field
   mapping không bị thay đổi âm thầm.
7. Bind badge header vào `session.user.full_name`/role thay cho literal hiện tại,
   nhưng giữ nguyên visual design.

## 11. Final status

`PASS_WITH_FINDINGS`

Authenticated React Admin data flow đã được chứng minh end-to-end. Các finding về
role split, missing fields và client-side full rendering cần được review trước khi
bắt đầu Phase 2; không có thay đổi Phase 2 nào được thực hiện trong đợt này.
