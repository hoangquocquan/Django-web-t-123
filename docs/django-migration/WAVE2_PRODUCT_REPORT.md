# Wave 2 Product Report

## Ownership Result

Django now owns new product writes through `apps.business_core`.

Implemented:

- `BusinessProduct`
- `BusinessProductService`
- `/api/v1/business/products/`
- `/api/v1/business/products/<id>/`

## Legacy Compatibility

Legacy catalog models in `apps.catalog` remain unmanaged and read-only. Existing read endpoints under `/api/v1/catalog/` remain available.

## Data Migration

Migration `business_core.0002_seed_business_core_from_legacy` copies legacy `products` rows into `business_products` using `legacy_product_id`.

## Safety

Legacy product tables are not updated or deleted. Django-owned product rows can be created without touching legacy data.
