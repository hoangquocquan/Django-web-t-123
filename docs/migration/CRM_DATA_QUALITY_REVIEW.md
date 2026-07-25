# CRM Data Quality Review

## Scope

This review reads the current legacy SQLite CRM data only. It does not modify data.

Tables reviewed:

- `customers`
- `customer_notes`
- `contact_requests`

## Current Snapshot

| Table | Row Count | Notes |
| --- | ---: | --- |
| `customers` | 3 | Core CRM customer records |
| `customer_notes` | 0 | Relationship exists, but demo data is empty |
| `contact_requests` | 6 | Public contact form submissions |

## Customers

### Issue: Duplicate Records

Observed:

- Duplicate email groups: 0
- Duplicate phone groups: 0

Impact:

- Low current duplicate risk based on email/phone.

Recommendation:

- Keep duplicate checks before future CRM write migration.
- Add normalization rules before automatic matching.

### Issue: Missing Fields

Observed:

- Missing company: 0
- Missing email: 0
- Missing phone: 0
- Missing country: 0

Impact:

- Customer records are mostly complete for demo CRM use.

Recommendation:

- Keep required-field validation in future CRM write/API phase.

### Issue: Invalid Email

Observed:

- Customer ID `3` has email value `sdfsadfasd`.

Impact:

- Email-based matching may fail or produce unreliable CRM links.

Recommendation:

- Do not modify data in this phase.
- Add validation rules before enabling future customer write operations.
- Mark invalid email rows for manual cleanup review.

### Issue: Invalid Phone

Observed:

- No automated invalid phone rule was enforced in Phase 5.1.

Impact:

- Phone matching quality is unknown.

Recommendation:

- Define phone normalization in a future CRM matching phase.

## Customer Notes

### Issue: Empty Table

Observed:

- `customer_notes` has 0 rows.

Impact:

- Relationship mapping can be tested, but real note content behavior cannot be validated with current data.

Recommendation:

- Keep row parity and orphan checks.
- Add richer fixture data in a future dedicated test data phase if needed.

### Issue: Orphan Records

Observed:

- Orphan `customer_notes`: 0

Impact:

- No current referential integrity issue.

Recommendation:

- Keep orphan validation before any migration or export.

## Contact Requests

### Issue: Missing Customer Relation

Observed:

- `contact_requests` has no `customer_id` foreign key.

Impact:

- Django cannot safely infer a direct ORM relationship to `Customer`.
- Contact-to-customer linking needs a future strategy.

Recommendation:

- Use documented matching strategy: email, phone, manual verification and optional future relationship table.

### Issue: Duplicate Requests

Observed:

- Duplicate email/phone groups: 0

Impact:

- Low duplicate risk based on currently available contact email/phone.

Recommendation:

- Recheck duplicates after contact forms begin collecting email/phone consistently.

### Issue: Missing Fields

Observed:

- Missing email: 6
- Missing phone: 6
- Missing company: 6
- Missing message: 0

Impact:

- Current contact data is message-focused and difficult to link to customer profiles.

Recommendation:

- Future public contact form should require at least one reliable identifier such as email or phone.
- Do not backfill automatically without manual verification.
