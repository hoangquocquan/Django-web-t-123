# Sales Transaction Strategy

## Purpose

Future quotation writes will be multi-step.

For example:

1. Create or link customer.
2. Create quote request header.
3. Create quote line items.
4. Store uploaded file metadata.
5. Add audit log or notification.

If step 4 fails, steps 1 to 3 may need rollback. Phase 6 does not implement writes, but it documents the transaction boundary now.

## Current Phase 6 Rule

Phase 6 is read-only.

No `transaction.atomic()` write flow is introduced yet.

## Future Write Boundary

When write migration is approved, quote creation should run inside one transaction:

```python
with transaction.atomic():
    customer = customer_service.get_or_create_customer(...)
    quote = quotation_repository.create_quote(...)
    quotation_repository.create_items(quote, ...)
    quotation_repository.create_files(quote, ...)
```

## Rollback Rule

If any required step fails:

- rollback quote header,
- rollback quote items,
- rollback file metadata,
- keep physical uploaded file cleanup as a separate safe cleanup task,
- record failure in audit log if the audit system is outside the transaction.

## Validation Before Write Migration

Before enabling writes:

- Define required quote fields.
- Define file validation rules.
- Define max file size and allowed extensions.
- Decide whether files are stored in local media, S3-compatible storage or external storage.
- Add integration tests for rollback behavior.

## Current Recommendation

Keep Phase 6 read-only and use repository/service tests as the baseline for future transaction-safe write migration.
