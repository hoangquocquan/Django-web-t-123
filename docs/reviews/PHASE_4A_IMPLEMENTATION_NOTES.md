# Phase 4A Implementation Notes

## 1. Objective

Implement the first read-only unmanaged Django ORM migration slice for catalog data.

Scope:

- categories
- materials
- machines
- manufacturing processes
- capabilities
- products
- product images
- product specs
- catalog relationship tables

No write APIs, serializers, migrations, legacy data migration, or legacy backend replacement were implemented.

## 2. Models Created

All catalog models are unmanaged and read-only.

| Model | Legacy Table | Notes |
|---|---|---|
| `Category` | `product_categories` | Product category reference data |
| `Material` | `materials` | Manufacturing material reference data |
| `Machine` | `machines` | Manufacturing machine reference data |
| `ManufacturingProcess` | `manufacturing_processes` | Manufacturing process reference data |
| `Capability` | `capabilities` | Manufacturing capability content |
| `Product` | `products` | Main product catalog table |
| `ProductImage` | `product_images` | Product gallery image rows |
| `ProductSpec` | `product_specs` | Product technical specification rows |
| `ProductMaterial` | `product_materials` | Composite key product/material relation |
| `ProductProcess` | `product_processes` | Composite key product/process relation |
| `CapabilityMachine` | `capability_machines` | Composite key capability/machine relation |

## 3. Table Mapping

Every legacy catalog model follows:

```python
class Meta:
    managed = False
    db_table = "legacy_table_name"
```

Composite relationship tables use Django's `CompositePrimaryKey` support instead of adding surrogate IDs.

## 4. Relationship Decisions

Foreign keys were added where safe:

- `Product.category -> Category`
- `ProductImage.product -> Product`
- `ProductSpec.product -> Product`
- `ProductMaterial.product -> Product`
- `ProductMaterial.material -> Material`
- `ProductProcess.product -> Product`
- `ProductProcess.process -> ManufacturingProcess`
- `CapabilityMachine.capability -> Capability`
- `CapabilityMachine.machine -> Machine`

Automatic `ManyToManyField` was not used.

Relationship tables remain explicit unmanaged models.

## 5. Read-Only Protection

Created:

```text
apps/common/models.py
```

Read-only protection includes:

- `LegacyReadOnlyModel.save()` disabled.
- `LegacyReadOnlyModel.delete()` disabled.
- read-only QuerySet `.update()` disabled.
- read-only QuerySet `.delete()` disabled.
- legacy SQLite alias configured as read-only URI.

## 6. Repository Design

Created repository adapters:

```text
apps/catalog/repositories/category_repository.py
apps/catalog/repositories/product_repository.py
```

Rules:

- repositories use `.objects.using("legacy")`.
- API code should not access ORM directly.
- services call repositories only.

## 7. Service Layer

Created:

```text
apps/catalog/services/catalog_service.py
```

Methods:

- `list_products()`
- `get_product_detail()`

No business transformation was added in Phase 4A.

## 8. Test Strategy

Created:

```text
apps/catalog/tests/test_catalog_orm.py
```

Tests cover:

- legacy database connection,
- product table mapping,
- product/category relationship,
- composite relationship model,
- instance save/delete blocking,
- bulk update/delete blocking,
- category repository,
- product image repository,
- catalog service.

Important test design:

`pytest-django` would normally create a test database for the `legacy` alias. Phase 4A tests intentionally use `django_db_blocker.unblock()` to access the external legacy read-only database without running migrations or creating a fake legacy schema.

## 9. Known Limitations

- No API endpoints were created.
- No serializers were created.
- No admin UI was created.
- No business CRUD was created.
- No legacy repositories were replaced.
- Media fields remain plain text paths/URLs.
- Auth/session tables are untouched.
- Write behavior is intentionally blocked.

## 10. Validation

Commands:

```text
python manage.py check
pytest
```

Result:

```text
PASS
10 passed
```
