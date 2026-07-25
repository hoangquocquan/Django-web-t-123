# CRM Migration Limitations

## Scope In Phase 5

Phase 5 chỉ triển khai lát cắt CRM read-only trong Django.

Các bảng được map:

- `customers`
- `customer_notes`
- `contact_requests`

## What Is Intentionally Not Included

- Không tạo API CRM.
- Không tạo serializer.
- Không tạo CRUD.
- Không thay đổi form liên hệ public.
- Không ghi database legacy.
- Không migrate dữ liệu sang database Django mới.
- Không map `quote_requests`, `quote_request_items`, `quote_files` vì các bảng này thuộc Phase 6 Sales / Quotation Migration.

## Contact Request Relationship Note

`contact_requests` hiện là bảng form liên hệ độc lập, không có khóa ngoại tới `customers`.

Vì vậy Django không tạo quan hệ giả giữa `ContactRequest` và `Customer`.
Nếu sau này muốn liên kết contact với customer, cần có phase riêng để thiết kế:

- matching rule theo email/phone/company,
- quy trình merge duplicate customer,
- migration hoặc bảng liên kết mới,
- rollback strategy.

## Customer Notes Relationship

`customer_notes.customer_id` có foreign key tới `customers.id`.

Phase 5 đã map quan hệ này bằng:

```python
Customer.notes
```

Hiện database demo có thể chưa có nhiều note, nhưng relationship vẫn được test bằng row parity và prefetch behavior.

## Read-Only Rule

Tất cả CRM models kế thừa `LegacyReadOnlyModel`.

Điều này chặn:

- `save()`
- `delete()`
- bulk `update()`
- bulk `delete()`

## Future Readiness

Phase 5 tạo pattern để các module CRM sau này có thể mở rộng:

- CRM API read-only,
- customer detail screen,
- contact management screen,
- customer merge workflow,
- integration với quotation trong Phase 6.
