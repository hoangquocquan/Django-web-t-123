# Catalog ORM Migration Plan

Phase: 3.2 - ORM Implementation Readiness & Legacy Database Integration Design  
Rule: Documentation only. No Django models are created in this phase.

## 1. Purpose

This document defines the detailed Phase 4A order for catalog read-only unmanaged ORM models.

## 2. Phase 4A.1 Foundation Reference Models

### ProductCategory

- Legacy table: `product_categories`
- Django model: `ProductCategory`
- Dependencies: none
- Risk: Low/Medium
- Validation:
  - row count matches SQLite,
  - `id`, `name`, `slug`, `sort_order` read correctly,
  - slug uniqueness preserved.

### Material

- Legacy table: `materials`
- Django model: `Material`
- Dependencies: none
- Risk: Low
- Validation:
  - row count matches SQLite,
  - `name` uniqueness preserved,
  - product/quote references resolve later.

### Machine

- Legacy table: `machines`
- Django model: `Machine`
- Dependencies: none
- Risk: Low
- Validation:
  - row count matches SQLite,
  - `machine_type` and `status` values preserved.

### ManufacturingProcess

- Legacy table: `manufacturing_processes`
- Django model: `ManufacturingProcess`
- Dependencies: none
- Risk: Low
- Validation:
  - row count matches SQLite,
  - `name` uniqueness preserved,
  - `sort_order` preserved.

## 3. Phase 4A.2 Product Models

### Product

- Legacy table: `products`
- Django model: `Product`
- Dependencies:
  - `ProductCategory`
- Risk: High
- Validation:
  - row count matches SQLite,
  - category FK resolves,
  - slug and status values preserved,
  - media/path fields remain text,
  - price field mapping reviewed,
  - SEO fields preserved.

### ProductImage

- Legacy table: `product_images`
- Django model: `ProductImage`
- Dependencies:
  - `Product`
- Risk: Medium
- Validation:
  - child count per product matches SQLite,
  - image URL preserved exactly,
  - `sort_order` preserved.

### ProductSpec

- Legacy table: `product_specs`
- Django model: `ProductSpec`
- Dependencies:
  - `Product`
- Risk: Medium
- Validation:
  - child count per product matches SQLite,
  - spec name/value/unit preserved,
  - ordering preserved.

## 4. Phase 4A.3 Relationship Models

### ProductMaterial

- Legacy table: `product_materials`
- Django model: `ProductMaterial`
- Dependencies:
  - `Product`
  - `Material`
- Risk: Medium/High
- Validation:
  - pair count matches SQLite,
  - product/material FKs resolve,
  - duplicate pairs do not exist,
  - no surrogate ID introduced.

### ProductProcess

- Legacy table: `product_processes`
- Django model: `ProductProcess`
- Dependencies:
  - `Product`
  - `ManufacturingProcess`
- Risk: Medium/High
- Validation:
  - pair count matches SQLite,
  - `step_order` and `note` preserved,
  - workflow order matches legacy output,
  - no surrogate ID introduced.

### CapabilityMachine

- Legacy table: `capability_machines`
- Django model: `CapabilityMachine`
- Dependencies:
  - `Capability`
  - `Machine`
- Risk: Medium
- Validation:
  - pair count matches SQLite,
  - capability/machine FKs resolve,
  - no surrogate ID introduced.

## 5. Supporting Catalog Model

### Capability

- Legacy table: `capabilities`
- Django model: `Capability`
- Dependencies: none
- Risk: Low/Medium
- Validation:
  - row count matches SQLite,
  - title/content/sort order preserved,
  - relationship to machines validates through `CapabilityMachine`.

## 6. Recommended Implementation Order

```text
1. ProductCategory
2. Material
3. Machine
4. ManufacturingProcess
5. Capability
6. Product
7. ProductImage
8. ProductSpec
9. ProductMaterial
10. ProductProcess
11. CapabilityMachine
```

## 7. Phase 4A Exit Criteria

Phase 4A is complete only when:

- all models are unmanaged,
- all table counts match,
- all FK relationships validate,
- read-only protection tests pass,
- no migration files are created,
- no database file changes occur,
- no public API behavior changes.
