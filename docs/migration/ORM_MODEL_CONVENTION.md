# ORM Model Convention

Phase: 3.1 - Database Mapping Hardening & ORM Preparation Rules  
Rule: Documentation only. No Django models, migrations, or database changes.

## 1. Purpose

This document defines how future read-only Django ORM models should be named and mapped to the legacy SQLite schema.

These rules must be approved before Phase 4 creates unmanaged Django models.

## 2. Model Naming

Legacy table:

```text
products
```

Future Django model:

```text
Product
```

Rules:

- Use singular model names.
- Use PascalCase.
- Preserve business meaning.
- Avoid vague names such as `Item`, `Data`, or `Record`.
- Do not rename a business concept just to make the code look newer.

Examples:

| Legacy Table | Django Model |
|---|---|
| `products` | `Product` |
| `product_categories` | `ProductCategory` |
| `quote_requests` | `QuoteRequest` |
| `quote_request_items` | `QuoteRequestItem` |
| `admin_users` | `AdminUser` |
| `cms_menu_items` | `CmsMenuItem` |
| `ai_translation_cache` | `AiTranslationCache` |

## 3. Table Mapping

Every future read-only model mapped to legacy SQLite must define:

```python
class Meta:
    managed = False
    db_table = "legacy_table_name"
```

Meaning:

- `managed = False`: Django can read the table, but Django must not create, alter, or delete it.
- `db_table`: Django knows the exact legacy table name.

Phase 4 must not transfer database ownership to Django.

## 4. Field Mapping Rules

Initial field mapping should prioritize safety over elegance.

| SQLite Type | Future Django Field | Notes |
|---|---|---|
| `TEXT` short values | `CharField` | Use when max length is known or business value is short. |
| `TEXT` long content | `TextField` | Use for descriptions, HTML/content, JSON text, messages. |
| `INTEGER` IDs | `IntegerField` or `BigAutoField`/PK mapping | Preserve legacy IDs. |
| `INTEGER` boolean flags | `BooleanField` | Confirm legacy uses `0/1`. |
| `INTEGER` timestamps | `IntegerField` first or reviewed `DateTimeField` | Some auth/session timestamps are epoch-like values. |
| `REAL` | `FloatField` or `DecimalField` | Use `DecimalField` for money after precision is approved. |
| SQLite datetime stored as `TEXT` | `DateTimeField` only after format validation | Otherwise keep as `CharField`/`TextField` in first pass. |
| JSON stored as `TEXT` | `TextField` first | Use `JSONField` only after all rows validate as JSON. |

## 5. Primary Key Rules

- Preserve legacy IDs.
- Do not regenerate IDs.
- Do not change primary key type without approval.
- Do not replace integer IDs with UUIDs in Phase 4.
- Use existing text primary keys for tables like sessions/tokens/challenges.
- Composite primary keys require the strategy in `COMPOSITE_KEY_STRATEGY.md`.

Reason:

Existing foreign keys, repository queries, uploaded file references, and admin screens may depend on current IDs.

## 6. Relationship Rules

### ForeignKey

Use a future `ForeignKey` only when:

- referenced table mapping is approved,
- nullability matches SQLite,
- delete behavior is documented,
- relationship is validated with row counts and orphan checks.

Initial delete behavior should mirror legacy DB behavior:

| SQLite On Delete | Django Recommendation |
|---|---|
| `CASCADE` | Use only after delete workflow tests exist. |
| `SET NULL` | Preserve nullable relationship. |
| `NO ACTION` | Prefer protect/restrict behavior until reviewed. |

### ManyToMany

Many-to-many tables should use explicit through models.

Examples:

```text
products -> product_materials -> materials
products -> product_processes -> manufacturing_processes
capabilities -> capability_machines -> machines
news -> news_tags -> tags
```

### Composite Relationship Handling

Do not use a third-party composite key package unless architecture review explicitly approves it.

Preferred Phase 4 approach:

- Create unmanaged explicit link models.
- Preserve `db_table`.
- Preserve both legacy key columns.
- Avoid Django ownership of the table.
- Add validation tests around uniqueness and relationship counts.

## 7. Media Field Rules

Fields containing file paths or URLs must remain plain text in Phase 4.

Do not convert to:

- `ImageField`
- `FileField`
- custom storage fields

until the media migration phase is approved.

## 8. Auth Field Rules

Auth/session/password fields are security-sensitive.

Phase 4 may map them read-only if needed for admin dashboard or audit views.

Do not:

- replace Django auth,
- migrate password hashes,
- migrate sessions,
- change password reset flow,
- change 2FA behavior.

## 9. Validation Rules For Phase 4

Every unmanaged model should have validation against legacy SQLite:

- row count matches,
- primary key values match,
- foreign key relationships resolve,
- representative field values match,
- null/default behavior is understood,
- API output is not changed by model creation.

## 10. Stop Rule

If a table has unclear field meaning, unclear timestamp format, composite key risk, or auth/security risk, Phase 4 should pause and request review before implementing the model.
