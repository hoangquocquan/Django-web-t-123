# Database View Strategy

Phase: 3.1 - Database Mapping Hardening & ORM Preparation Rules  
Rule: Documentation only. No Django models, migrations, or database changes.

## 1. Purpose

This document defines how Django should handle legacy SQLite database views.

Views are useful for reporting/read convenience, but they should not become write targets.

## 2. Current Views

| View | Purpose | Recommendation |
|---|---|---|
| `product_overview` | Read-only product summary view from legacy schema/migrations | Do not map in first Phase 4 pass unless explicitly needed for read-only reporting. |

## 3. Rules

- Views are read-only.
- No write operations through a view.
- Use `managed = False` if a future Django model points to a view.
- `db_table` must point to the exact view name.
- Do not use a view-backed model for admin create/update/delete.
- Do not let serializers save to a view-backed model.

Example future model convention:

```python
class Meta:
    managed = False
    db_table = "product_overview"
```

## 4. When To Create A Django Model For A View

Create a view model only when:

- the view is needed by a read-only dashboard/report,
- the view output is stable,
- every selected column is documented,
- there is a clear primary key or stable identifier,
- the model is explicitly blocked from write flows,
- architecture review approves the view mapping.

Good candidates:

- dashboard summary,
- reporting tables,
- read-only export preview,
- legacy compatibility query where direct table joins are too risky.

## 5. When Not To Create A Django Model For A View

Do not create a view model when:

- normal table models can produce the data safely,
- the view has no stable identifier,
- the view hides important relationship logic,
- admin users need to create/update/delete the data,
- the view is only a convenience for one legacy query,
- field types are ambiguous.

## 6. product_overview Decision

Initial Phase 4 decision:

```text
Do not map product_overview first.
```

Reason:

- `products`, `product_categories`, `product_images`, and `product_specs` should be mapped directly first.
- Direct table mapping gives better validation and clearer ownership.
- The view can be revisited after product read models pass parity checks.

## 7. Validation Requirements

If a view-backed model is approved later:

- Compare row count with direct SQL.
- Compare important fields with source tables.
- Confirm the model is not registered for admin write operations.
- Confirm serializers are read-only.
- Confirm no migration is generated for the view.
