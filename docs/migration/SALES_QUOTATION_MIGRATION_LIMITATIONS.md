# Sales / Quotation Migration Limitations

## Scope In Phase 6

Phase 6 only implements the sales/quotation read-only ORM slice in Django.

Mapped tables:

- `quote_requests`
- `quote_request_items`
- `quote_files`

## What Is Intentionally Not Included

- No quote write API.
- No serializer.
- No CRUD workflow.
- No public quote form behavior change.
- No legacy database write.
- No file migration or file storage rewrite.
- No business workflow status transition change.

## Relationship Boundary

`quote_requests.customer_id` links to CRM `customers`.

`quote_request_items.product_id` optionally links to catalog `products`.

`quote_request_items.material_id` optionally links to catalog `materials`.

`quote_files.quote_request_id` links to `quote_requests`.

Phase 6 maps these relationships faithfully but keeps every model unmanaged and read-only.

## File Path Preservation

`quote_files.file_url` is treated as legacy data.

Django must preserve this value exactly. Phase 6 does not move files into Django media storage.

## Future Readiness

The read-only service/repository boundary prepares future phases for:

- quote detail API,
- quotation dashboard,
- quote workflow status tracking,
- file review UI,
- transaction-safe quote creation in a dedicated write migration phase.
