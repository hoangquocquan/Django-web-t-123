# Sales Data Quality Review

## Scope

This review reads the current legacy SQLite sales data only. It does not modify data.

Tables reviewed:

- `quote_requests`
- `quote_request_items`
- `quote_files`

## Current Snapshot

| Table | Row Count | Notes |
| --- | ---: | --- |
| `quote_requests` | 1 | Quote header records |
| `quote_request_items` | 1 | Quote line items |
| `quote_files` | 1 | Uploaded quote file metadata |

## Quote Requests

### Issue: Missing Customer References

Observed:

- Missing customer references: 0

Impact:

- Current quote header can resolve CRM customer relationship.

Recommendation:

- Keep FK validation before any future data migration.

### Issue: Invalid Status

Observed:

- Quote ID `1` has status `assigned`.

Impact:

- `assigned` may be valid in the legacy CMS, but the future Sales workflow needs an approved status vocabulary.

Recommendation:

- Do not modify data in Phase 6.1.
- Define final status set before creating write APIs or workflow automation.

### Issue: Incomplete Fields

Observed:

- Missing project name: 0
- Missing message: 0

Impact:

- Current demo quote has enough basic context.

Recommendation:

- Add required-field policy in future write migration.

## Quote Request Items

### Issue: Invalid Product References

Observed:

- Invalid product references: 0

Impact:

- Current quote item can resolve catalog product relationship.

Recommendation:

- Keep validation before snapshot migration.

### Issue: Invalid Material References

Observed:

- Invalid material references: 0

Impact:

- Current quote item can resolve catalog material relationship.

Recommendation:

- Keep validation before snapshot migration.

### Issue: Missing Quantities

Observed:

- Quantity values less than or equal to 0: 0

Impact:

- Current item quantity is usable.

Recommendation:

- Future writes must require positive quantity.

### Issue: Pricing Issues

Observed:

- Current legacy `quote_request_items` table does not store unit price.

Impact:

- Historical quote value cannot be reconstructed from item rows alone.

Recommendation:

- Add approved snapshot fields in a future write-enabled quotation migration.

## Quote Files

### Issue: Missing Paths

Observed:

- Missing `file_name` or `file_url`: 0

Impact:

- Current file metadata can be displayed or reviewed.

Recommendation:

- Preserve file paths exactly until file lifecycle migration is approved.

### Issue: Invalid References

Observed:

- Quote files pointing to missing quote requests: 0

Impact:

- Current file metadata has valid parent quote relationship.

Recommendation:

- Keep orphan validation before storage migration.
