# CRM Migration Limitations

## Scope In Phase 5

Phase 5 only implements the CRM read-only slice in Django.

Mapped tables:

- `customers`
- `customer_notes`
- `contact_requests`

## What Is Intentionally Not Included

- No CRM API.
- No serializer.
- No CRUD.
- No public contact form behavior change.
- No legacy database write.
- No data migration into the new Django database.
- No mapping for `quote_requests`, `quote_request_items` or `quote_files` because those tables belong to Phase 6 Sales / Quotation Migration.

## Contact Request Relationship Note

`contact_requests` is currently an independent public form table. It has no foreign key to `customers`.

Because of that, Django must not create a fake relationship between `ContactRequest` and `Customer`.

Future linking requires a separate approved phase for:

- matching by email, phone and company,
- manual verification,
- duplicate customer review,
- optional Django-owned relationship table,
- rollback strategy.

## Customer Notes Relationship

`customer_notes.customer_id` has a foreign key to `customers.id`.

Phase 5 maps this relationship as:

```python
Customer.notes
```

The current demo database has 0 customer notes, so tests can verify mapping and prefetch behavior but cannot validate real note content quality.

## Read-Only Rule

All CRM models inherit `LegacyReadOnlyModel`.

This blocks:

- `save()`
- `delete()`
- bulk `update()`
- bulk `delete()`

## Phase 5.1 Follow-Up

Phase 5.1 keeps the same read-only boundary.

Additional decisions:

- `contact_requests` remains independent because the legacy table has no `customer_id`.
- Future matching should use email first, phone second and manual verification before saving any permanent link.
- If durable linking is required, prefer a new Django-owned relationship table in a future approved phase.
- Current demo data has one invalid customer email and contact requests currently miss email/phone/company fields, so automatic matching is not safe yet.

## Future Readiness

Phase 5 creates a pattern that can later support:

- CRM read-only API,
- customer detail screen,
- contact management screen,
- customer merge workflow,
- integration with quotation in Phase 6.
