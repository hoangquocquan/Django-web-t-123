# CRM Notes Validation

## Table Structure

Legacy table: `customer_notes`

| Column | Type | Required | Purpose |
| --- | --- | --- | --- |
| `id` | INTEGER | Primary key | Unique note ID |
| `customer_id` | INTEGER | Yes | References `customers.id` |
| `note` | TEXT | Yes | CRM note content |
| `created_by` | TEXT | No | Admin/user label who created the note |
| `created_at` | TEXT | Yes | Creation timestamp |

## Relationship Mapping

Django model:

```python
class CustomerNote(LegacyReadOnlyModel):
    customer = models.ForeignKey(
        Customer,
        db_column="customer_id",
        on_delete=models.CASCADE,
        related_name="notes",
    )
```

Access pattern:

```python
customer.notes.all()
```

## Current Data Status

Current row count:

- `customer_notes`: 0

Observed orphan rows:

- 0

## Testing Limitation

Because the table currently has no rows, tests can validate:

- model maps to the table,
- row count parity,
- relationship manager exists,
- prefetch query pattern works,
- orphan query returns no invalid rows.

Tests cannot yet validate real note content ordering or text quality.

## Future Migration Considerations

Before CRM notes become write-enabled:

- Add validation for non-empty `note`.
- Decide whether `created_by` should link to future Django users.
- Preserve existing note IDs if migrating data.
- Define audit log behavior for note creation and updates.
- Add rollback strategy before migrating note data.
