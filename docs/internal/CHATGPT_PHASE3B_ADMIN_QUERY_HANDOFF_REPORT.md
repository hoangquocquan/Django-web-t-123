# CHATGPT PHASE 3B — ADMIN QUERY HANDOFF REPORT

## 1. Kết quả

Phase 3B đã chuyển các Admin list từ mô hình tải toàn bộ dữ liệu sang server-side pagination và query allowlist. Giao diện bảng, route, authentication, permission và response envelope được giữ nguyên.

Không có migration, seed, thay đổi database, Customer schema, Transaction redesign, RFQ, CMS hoặc Chatbot change.

## 2. API changes

Sáu list endpoint tiếp tục hỗ trợ `limit`, `offset`, `count`, `next_offset`, `results` và được bổ sung additive query parameters:

| Endpoint | Search | Filters | Ordering allowlist |
|---|---|---|---|
| `/api/v1/admin/products/` | part code, legacy SKU, name, material code/name | `status`, `active=true/false`, `material` | `created_at`, `product_code`, `name` |
| `/api/v1/admin/customers/` | company name, contact name | `status` | `created_at`, `company_name`, `contact_name` |
| `/api/v1/admin/inventory/items/` | material code, product name | `warehouse`, `availability=positive/zero` | `quantity`, `updated_at` |
| `/api/v1/admin/orders/` | order number, company/contact name | `workflow_status`, `status` | `order_date`, `expected_delivery_date` |
| `/api/v1/admin/workflows/` | order number, requester, reviewer, note | `decision`, `requested_status` | `created_at`, `order` |
| `/api/v1/admin/transactions/` | entity ID, action, actor | `entity_type`, `action` | `created_at` |

Descending sort dùng dấu `-`, ví dụ `ordering=-expected_delivery_date`.

Unknown ordering trả `400 invalid_ordering`. Search dài hơn 200 ký tự trả `400 invalid_search`. Giá trị boolean/availability không hợp lệ trả `400 invalid_filter`. Arbitrary ORM field không được truyền trực tiếp từ client.

### Inventory availability

`availability` là filter số học, không phải stock status:

- `positive`: `quantity > reserved_quantity`.
- `zero`: `quantity <= reserved_quantity`.

Phase 3B không tạo hoặc suy diễn `stock_status`.

InventoryItem không có `created_at`; vì vậy API chỉ allow sort `updated_at`. Không tạo field/migration để giả lập created date.

## 3. Backward compatibility

- Không thay endpoint hoặc HTTP method.
- Không xóa field response Phase 1/3A.
- Request chỉ có `limit/offset` tiếp tục hoạt động.
- Request không có query mới tiếp tục dùng model ordering hiện tại.
- Dashboard API không thay đổi.
- Authentication Bearer token và permission module hiện tại không thay đổi.

## 4. Backend implementation

Tạo helper dùng chung `apps/api/admin_query.py`:

- Ghép search bằng `Q(...__icontains)` trên allowlist.
- Áp dụng filter exact/callback theo từng endpoint.
- Map public ordering name sang ORM field allowlist.
- Trả error envelope hiện tại khi query không hợp lệ.

`admin_interface.py` gọi helper trước `paginated_ok()`. Count được tính sau search/filter, rồi queryset chỉ slice đúng page cần trả.

Các relation optimization từ Phase 3A được giữ lại:

- Product: `select_related("default_material")`.
- Inventory: `select_related("product__default_material", "warehouse")`.
- Order: service đã select related customer/assignee.

## 5. Frontend changes

### Shared query state

Tạo `src/hooks/useAdminTableQuery.ts` với state chung:

```ts
{
  page,
  pageSize,
  search,
  filters,
  ordering
}
```

Reducer dùng chung đảm bảo:

- Search/filter/sort/page-size change reset về page 1.
- Page không nhỏ hơn 1.
- Filter rỗng bị loại khỏi request.
- Query reset khi đổi Admin route.

### API service

`src/services/adminApi.ts` không còn `allPages()`.

Mỗi list call:

1. Tạo `limit` từ `pageSize`.
2. Tạo `offset = (page - 1) * pageSize`.
3. Thêm search/filter/ordering có giá trị.
4. Chỉ gọi một request và map một page.

`AdminCollection<T>` được bổ sung metadata:

- `limit`
- `offset`
- `nextOffset`
- `count`
- `results`

### Table controls

Giữ DataTable và layout hiện tại, bổ sung controls tối thiểu quanh bảng:

- Search input và nút Tìm.
- Filter controls theo từng route.
- Sort tăng/giảm.
- Tổng số record.
- Chỉ báo trang hiện tại/tổng số trang.
- Previous/Next.
- Page size 20/50/100.

Loading, empty và error states hiện tại được giữ nguyên. Empty state vẫn hiển thị cùng query controls để user có thể thay query.

### Dashboard

Dashboard tiếp tục gọi duy nhất `/api/v1/admin/dashboard/`. Không fetch Product/Customer/Inventory/Order datasets và không thêm KPI/tính toán mới.

## 6. Pagination implementation

Default page size: 20.

Ví dụ Product page 2:

```text
GET /api/v1/admin/products/?limit=20&offset=20
```

Ví dụ có query:

```text
GET /api/v1/admin/products/?limit=20&offset=0&search=SUS304&active=true&material=SUS&ordering=-product_code
```

Frontend không dựa vào số rows trả về để xác định tổng trang; sử dụng backend `count`.

## 7. Search implementation

- Search được trim ở frontend và backend.
- Search thay đổi reset page về 1.
- Backend giới hạn 200 ký tự.
- Search chỉ chạy trên field được công bố theo từng endpoint.
- Không search trong Customer notes; không khôi phục logic industry-from-notes.

## 8. Filter implementation

- Product: legacy status, canonical active flag, material.
- Customer: status; không thêm industry/projects/value logic.
- Inventory: warehouse ID/code và available quantity bucket.
- Order: workflow status và legacy status.
- Workflow/Transaction: chỉ query existing entity, không đổi domain semantics.

## 9. Sort implementation

- Public ordering names được map sang ORM field cố định.
- Hỗ trợ ascending và descending.
- Không cho client chỉ định raw relation/path.
- Default model ordering vẫn được giữ khi không có `ordering`.

## 10. Performance comparison

### Trước Phase 3B

Frontend gọi tuần tự mọi page với limit 100, gom toàn bộ rồi mới render:

| Table | Records rendered | Requests đầu tải | JSON toàn bộ xấp xỉ |
|---|---:|---:|---:|
| Products | 601 | 7 | 259.2 KiB |
| Customers | 201 | 3 | 75.1 KiB |
| Inventory | 900 | 9 | 681.4 KiB |
| Orders | 450 | 5 | 181.8 KiB |

### Sau Phase 3B, page size 20

Đo trực tiếp serializer trên local dataset:

| Table | Rows render ban đầu | Requests | JSON page 20 | Local serialize/query time |
|---|---:|---:|---:|---:|
| Products | 20 | 1 | 12.1 KiB | 6.61 ms |
| Customers | 20 | 1 | 7.4 KiB | 1.07 ms |
| Inventory | 20 | 1 | 19.1 KiB | 2.51 ms |
| Orders | 20 | 1 | 9.9 KiB | 4.51 ms |

So với trước:

- Product: 7 request → 1; 601 rows → 20.
- Customer: 3 request → 1; 201 rows → 20.
- Inventory: 9 request → 1; 900 rows → 20.
- Order: 5 request → 1; 450 rows → 20.

Payload measurements chưa gồm envelope/header và network compression, nhưng phản ánh trực tiếp dữ liệu serializer.

## 11. Files changed/created

### Backend

- `django_backend/apps/api/admin_query.py` — new.
- `django_backend/apps/api/views/admin_interface.py`.
- `django_backend/apps/api/tests/test_phase3b_admin_queries.py` — new.

Phase 3A files vẫn chứa canonical contract và relation optimization:

- `django_backend/apps/api/serializers/business_core.py`.
- `django_backend/apps/api/serializers/transaction_domain.py`.
- `django_backend/apps/business_core/services.py`.

### Frontend

- `figma_make_frontend/src/hooks/useAdminTableQuery.ts` — new.
- `figma_make_frontend/src/hooks/useAdminTableQuery.test.ts` — new.
- `figma_make_frontend/src/services/adminApi.ts`.
- `figma_make_frontend/src/services/adminApi.test.ts`.
- `figma_make_frontend/src/types/admin.ts`.
- `figma_make_frontend/src/App.tsx`.
- `figma_make_frontend/package.json`.

## 12. Test coverage

Backend Phase 3B integration tests cover:

- Product page 1/page 2, `next_offset`, search, active/status/material filters và sort.
- Customer search/status/sort.
- Inventory search/warehouse/availability/sort.
- Order search/workflow status/legacy status/sort và persisted progress.
- Workflow/Transaction additive query contract.
- Rejection của unknown ordering và invalid availability.

Frontend tests cover:

- Page state transitions và reset-to-page-1 behavior.
- Product page 1/page 2 query parameters.
- Product search/filter/sort query serialization.
- Inventory pagination/search query.
- Order workflow filter query.
- Canonical response mapping và auth/error regression.

Kết quả:

| Check | Result |
|---|---|
| `npm run typecheck` | PASS |
| `npm run build` | PASS — Vite 8.0.5, 28 modules transformed |
| `npm test` | PASS — 154 passed, 0 failed |
| Phase 3B backend focused tests | PASS — 6 passed |
| Full backend `python -m pytest` | PASS — 279 passed, 151 skipped, 0 failed; 430 collected |

## 13. Database integrity

Phase 3B không chạy migration, seed hoặc business-data write.

Baseline SHA-256:

`01127FB14ADE07A4A476950610F5034C603F942DCB4C1C0776CFAC7FBE7CBB45`

SHA-256 sau implementation và full regression:

`01127FB14ADE07A4A476950610F5034C603F942DCB4C1C0776CFAC7FBE7CBB45`

Checksum trùng khớp: database local không thay đổi.

## 14. Các vấn đề còn lại

1. Inventory không có `created_at`; hiện dùng `updated_at` cho sort thời gian.
2. Material và warehouse filter dùng text/code; chưa có selector endpoint/UI autocomplete.
3. Offset pagination phù hợp quy mô hiện tại; AuditEvent volume lớn trong tương lai có thể cần cursor pagination, nhưng Transaction redesign ngoài scope.
4. Role taxonomy vẫn chưa align; Phase 3B không thay permission.
5. Customer industry/projects/value tiếp tục “Chưa có dữ liệu”.
6. Inventory stock status tiếp tục “Chưa có dữ liệu”.
7. Workflow/Transaction local hiện có 0 rows; query contract có automated fixture coverage nhưng runtime UI vẫn empty đúng dữ liệu thật.
8. Text filter áp dụng khi input mất focus; search áp dụng khi submit để tránh request trên từng phím.

## 15. Stop condition

Phase 3B dừng sau server pagination/query implementation và verification.

Không triển khai role migration, Customer schema migration, Transaction redesign, RFQ, CMS hoặc Chatbot changes. Chờ review trước phase tiếp theo.
