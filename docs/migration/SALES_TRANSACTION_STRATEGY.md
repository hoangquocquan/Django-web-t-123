# Sales Transaction Strategy

## Purpose

Future quotation writes will be multi-step and must be transaction-safe.

Phase 6.1 does not introduce write transactions. It only defines the future boundary.

## Future Workflow

```text
Customer creation/linking
        |
        v
Quote creation
        |
        v
Quote items creation
        |
        v
File metadata creation
```

## Atomic Transaction Requirement

Future quote creation must use a single database transaction for database records:

```python
with transaction.atomic():
    customer = customer_service.resolve_customer(...)
    quote = quotation_repository.create_quote(...)
    quotation_repository.create_items(quote, ...)
    quotation_repository.create_file_metadata(quote, ...)
```

If any required database step fails, all database changes in the transaction must rollback.

## Rollback Strategy

Rollback inside database transaction:

- customer link created only for this quote,
- quote header,
- quote items,
- quote file metadata,
- audit/event rows if they are part of the same database transaction.

Do not rely on database rollback for:

- physical files already written to disk,
- files uploaded to S3/CDN/external storage,
- emails already sent,
- external notifications already dispatched.

## Failure Scenarios

Customer validation fails:

- Do not create quote.
- Return validation error.

Quote item validation fails:

- Rollback quote header and previous items.
- Keep uploaded temp files in quarantine until cleanup job runs.

File metadata insert fails:

- Rollback quote header and items.
- Schedule physical file cleanup if file upload already happened.

Notification fails:

- Quote may still be valid if notification is non-critical.
- Use outbox or queue pattern for retry.

## External File Handling

Recommended future flow:

1. Upload physical file to temporary storage.
2. Validate file type, size and scan result.
3. Start database transaction.
4. Create quote, items and file metadata.
5. Move file from temporary to permanent storage after database success.
6. Run cleanup job for abandoned temporary files.

## Current Recommendation

Keep Phase 6.1 read-only.

Require architecture approval before introducing write APIs, transactions or file storage changes.
