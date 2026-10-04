# CHATGPT PHASE 3A — ADMIN API CONTRACT HANDOFF REPORT

## 1. Mục đích báo cáo

Báo cáo này dùng để handoff cho ChatGPT/reviewer sau khi hoàn thành:

- Phase 2: audit và thiết kế Admin data model/API contract.
- Phase 3A: triển khai phần contract an toàn, không cần migration và không cần thay đổi UI layout.

Không xem báo cáo này là phê duyệt cho các thay đổi role, migration Customer, stock-status rule, Transaction domain hoặc redesign Admin table.

## 2. Bối cảnh đã xác nhận

Phase 1 và Phase 1.5 đã kết nối React Admin với Django Admin API thật, sử dụng authentication hiện tại và dữ liệu local:

| Entity | Record count |
|---|---:|
| Products | 601 |
| Customers | 201 |
| Inventory Items | 900 |
| Orders | 450 |
| WorkflowApproval | 0 |
| TransactionHistory | 0 |

Frontend không còn mock fallback cho các màn hình Admin.

## 3. Phase 2 audit đã hoàn thành

Tám báo cáo audit/design nằm tại `reports/phase2/`:

1. `ROLE_PERMISSION_ALIGNMENT_REPORT.md`
2. `PRODUCT_DATA_MODEL_REPORT.md`
3. `CUSTOMER_DATA_MODEL_REPORT.md`
4. `INVENTORY_DATA_MODEL_REPORT.md`
5. `ORDER_DATA_MODEL_REPORT.md`
6. `TRANSACTION_DOMAIN_REPORT.md`
7. `ADMIN_TABLE_PERFORMANCE_REPORT.md`
8. `PHASE2_SUMMARY_REPORT.md`

Các kết luận quan trọng:

- Role canonical `Admin/Manager/Sales` không có permission module legacy mà `/api/v1/admin/*` đang kiểm tra.
- Product và Order đã có đủ field canonical trong database; Admin serializers chỉ chưa expose.
- Customer không có field industry chính thức, không có Project entity, và chưa có định nghĩa duy nhất cho customer value.
- Inventory chưa có stock-status business rule chính thức.
- Admin Transactions hiện dùng `TransactionHistory`, không phải InventoryTransaction hoặc AuditEvent.
- Backend có pagination nhưng frontend gọi tuần tự toàn bộ page rồi render toàn bộ rows.

## 4. Phạm vi Phase 3A đã triển khai

Chỉ triển khai các field đã tồn tại và có nguồn dữ liệu rõ ràng. Tất cả thay đổi API đều additive để giữ backward compatibility.

### 4.1 Product contract

Admin Product response giữ các field legacy và bổ sung:

| API field mới | Database source |
|---|---|
| `part_code` | `BusinessProduct.part_code` |
| `unit` | `BusinessProduct.unit` |
| `default_material.id` | `BusinessProduct.default_material_id` |
| `default_material.material_code` | `BusinessMaterial.material_code` |
| `default_material.name` | `BusinessMaterial.name` |
| `tolerance` | `BusinessProduct.tolerance` |
| `is_active` | `BusinessProduct.is_active` |
| `archived_at` | `BusinessProduct.archived_at` |

Frontend mapping mới:

- `code`: ưu tiên `part_code`, fallback `sku` để tương thích.
- `material`: dùng default material name, fallback material code.
- `tolerance`: dùng field thật từ API.
- `status`: dùng `is_active` khi API cung cấp; fallback legacy `status`.

Kết quả: frontend không còn hiển thị Product code/material/tolerance bằng nguồn legacy rỗng hoặc placeholder khi canonical data có sẵn.

### 4.2 Inventory contract

Inventory response tiếp tục chứa nested Product và bổ sung:

- Nested Product canonical fields như phần Product contract.
- `available_quantity = quantity - reserved_quantity`.

Frontend mapping mới:

- `material code`: `product.default_material.material_code`.
- `description`: `product.name`.
- `quantity`: `InventoryItem.quantity`.
- `unit`: `product.unit`.
- `status`: vẫn hiển thị `Chưa có dữ liệu`.

Không tự suy diễn stock status từ quantity/reorder point vì business rule chưa được phê duyệt.

### 4.3 Order contract

Admin Order response giữ legacy `status` và bổ sung:

| API field mới | Database source |
|---|---|
| `workflow_status` | `TransactionOrder.workflow_status` |
| `progress_percent` | `TransactionOrder.progress_percent` |
| `expected_delivery_date` | `TransactionOrder.expected_delivery_date` |

Frontend mapping mới:

- `progress`: persisted `progress_percent`, định dạng `%`.
- `delivery date`: `expected_delivery_date`.
- `status`: ưu tiên canonical `workflow_status`, fallback legacy `status`.

Không tính progress từ status, số event hoặc vị trí workflow.

### 4.4 Customer safety correction

Đã bỏ việc frontend parse `industry=...` từ `BusinessCustomer.notes`.

Trong khi chưa có schema chính thức:

- `industry`: `Chưa có dữ liệu`.
- `projects`: `Chưa có dữ liệu`.
- `value`: `Chưa có dữ liệu`.

Không có migration hoặc chỉnh sửa Customer data.

### 4.5 Query optimization

- `BusinessProductService.list_products()` dùng `select_related("default_material")`.
- `InventoryService.list_items()` dùng `select_related("product__default_material", "warehouse")`.

Mục tiêu là giữ một query/page khi serializers đọc material relation, tránh N+1.

## 5. API compatibility

Không xóa hoặc đổi tên field cũ:

- Product vẫn trả `sku`, `status`, các legacy fields và SEO block.
- Order vẫn trả `status`, legacy IDs/timestamps và monetary fields.
- Inventory vẫn trả quantity/reserved/reorder và nested warehouse/product.

Client cũ vẫn có thể dùng contract trước Phase 3A. Client mới ưu tiên canonical fields.

Không thay đổi endpoint:

- `GET /api/v1/admin/products/`
- `GET /api/v1/admin/customers/`
- `GET /api/v1/admin/inventory/items/`
- `GET /api/v1/admin/orders/`

Không thay đổi authentication, Bearer token, permission check hoặc routing frontend.

## 6. Files đã sửa/tạo trong Phase 3A

### Backend

- `django_backend/apps/api/serializers/business_core.py`
- `django_backend/apps/api/serializers/transaction_domain.py`
- `django_backend/apps/business_core/services.py`
- `django_backend/apps/api/tests/test_phase3a_admin_contract.py` — file mới

### Frontend

- `figma_make_frontend/src/services/adminApi.ts`
- `figma_make_frontend/src/services/adminApi.test.ts`

### Reports

- `reports/phase2/*.md`
- `CHATGPT_PHASE3A_ADMIN_CONTRACT_HANDOFF_REPORT.md`

Repository đã có các thay đổi khác từ những phase/task trước. Khi review Git diff, chỉ nên quy Phase 3A cho danh sách file nêu trên và các hunk được mô tả trong báo cáo này.

## 7. Runtime evidence trên database thật

Read-only serialization đã xác nhận:

### Product sample

```json
{
  "part_code": "PART-PHASE6B-E2E",
  "default_material": {
    "id": 1,
    "material_code": "MAT-PHASE6B-E2E",
    "name": "Phase 6B Fictional SUS304"
  },
  "unit": "PCS",
  "is_active": true
}
```

### Inventory sample

```json
{
  "material": {
    "id": 2,
    "material_code": "MAT-0001",
    "name": "S45C Demo Lot 1"
  },
  "unit": "PCS",
  "quantity": "26.00",
  "available_quantity": "25.00"
}
```

### Order sample

```json
{
  "order_number": "SO-2026-0403",
  "workflow_status": "IN_PROGRESS",
  "progress_percent": 75,
  "expected_delivery_date": "2026-10-29"
}
```

Các sample chỉ chứng minh mapping runtime; không phải dữ liệu được tạo bởi Phase 3A.

## 8. Test results

### Phase 2 full regression baseline

| Command | Result |
|---|---|
| `npm run typecheck` | PASS |
| `npm run build` | PASS |
| `npm test` | 150 passed, 0 failed |
| Backend `python -m pytest` | 270 passed, 151 skipped, 0 failed; 421 collected |

### Sau thay đổi Phase 3A

| Command/scope | Result |
|---|---|
| `npm run typecheck` | PASS |
| `npm run build` | PASS |
| `npm test` | 152 passed, 0 failed |
| Backend `apps/api` + `apps/business_core` | 81 passed, 50 skipped, 0 failed |
| New Phase 3A contract tests | 3 passed |
| Runtime serialization trên local DB | PASS |
| `git diff --check` cho implementation files | PASS; chỉ có cảnh báo line-ending LF/CRLF của Git trên Windows |

Hai frontend tests mới xác nhận:

- Customer notes không được dùng để suy diễn industry.
- Inventory và Order map đúng canonical contract fields.

Ba backend tests mới xác nhận:

- Product contract additive và không xóa field legacy.
- Inventory trả material/unit/available quantity nhưng không bịa `stock_status`.
- Order trả persisted workflow/progress/delivery date và vẫn giữ legacy status.

## 9. Database integrity

Không chạy migration, không seed, không sửa hoặc xóa business data.

SHA-256 của `django_backend/db.sqlite3`:

- Trước Phase 2/3A: `01127FB14ADE07A4A476950610F5034C603F942DCB4C1C0776CFAC7FBE7CBB45`
- Sau implementation và tests: `01127FB14ADE07A4A476950610F5034C603F942DCB4C1C0776CFAC7FBE7CBB45`

Checksum trùng khớp.

## 10. Những phần cố ý chưa triển khai

### 10.1 Role/permission alignment

Chưa merge/xóa/đổi role và chưa thêm permission migration. Cần review taxonomy canonical trước.

### 10.2 Customer industry/projects/value

Chưa thêm field hoặc model vì cần quyết định:

- Industry thuộc BusinessCustomer hay CRM profile?
- Project là RFQ project, Order project hay entity độc lập?
- Customer value là pipeline, quotation, ordered hay realized value?
- Quy tắc currency và loại trừ cancelled/superseded records?

### 10.3 Inventory status

Chưa expose stock status vì cần chốt:

- Dùng `quantity` hay `quantity - reserved_quantity`?
- `reorder_point = 0` có ý nghĩa gì?
- Product/material/warehouse inactive có override status không?

### 10.4 Admin Transactions

Chưa đổi endpoint/source. Reviewer cần chọn một trong ba nghĩa:

1. Audit Activity → `AuditEvent`.
2. Inventory Movement → `InventoryTransaction`.
3. Financial transaction → cần domain/model riêng.

Không nên union ba nguồn.

### 10.5 Server-side table pagination

Chưa implement vì cần thêm page controls vào UI. Backend đã hỗ trợ limit/offset; frontend vẫn tải toàn bộ page tuần tự.

## 11. Đề xuất thứ tự tiếp theo

1. Runtime browser validation các trang Product, Inventory và Order bằng user hợp lệ.
2. Review và phê duyệt permission taxonomy.
3. Chốt nghĩa trang Transactions.
4. Chốt Inventory stock-status rule.
5. Thiết kế Customer schema/aggregation; chỉ migration sau phê duyệt.
6. Triển khai server pagination/search/filter/sort mà không redesign layout.

## 12. Review checklist cho ChatGPT

- [ ] Xác nhận additive fields không làm lộ dữ liệu không được phép.
- [ ] Xác nhận `is_active` là nguồn status phù hợp cho Product Admin.
- [ ] Xác nhận Product material nên hiển thị name hay code + name.
- [ ] Xác nhận `available_quantity` là field được phép expose.
- [ ] Xác nhận persisted `progress_percent` là nguồn duy nhất cho Admin progress.
- [ ] Chọn permission taxonomy và compatibility window.
- [ ] Chọn nghĩa chính thức của Admin Transactions.
- [ ] Chốt Customer industry/project/value definitions.
- [ ] Chốt Inventory stock-status/reorder rule.
- [ ] Phê duyệt Phase 3B trước khi có migration hoặc thay đổi UI controls.

## 13. Trạng thái handoff

Phase 3A implementation và automated verification đã hoàn tất.

Hệ thống đang dừng tại các decision gates nêu trên. Không nên tự động tiếp tục migration, role alignment hoặc Transaction source replacement nếu chưa có review/phê duyệt rõ ràng.
