# Quotation Snapshot Strategy

## Problem

Products, materials and prices can change over time.

A quotation must preserve what the customer was quoted at the time of creation, approval or conversion. If quote items only point to live product/material rows, old quotes may appear to change when catalog data changes.

## Current Phase 6.1 State

Current legacy quote items store:

- `product_id`
- `material_id`
- `drawing_code`
- `quantity`
- `tolerance`
- `note`

They do not yet store a full historical snapshot of product name, material name, specification or price.

## Future Snapshot Fields

Recommended future fields for quote item snapshot:

- `product_name_snapshot`
- `product_sku_snapshot`
- `material_name_snapshot`
- `material_standard_snapshot`
- `specification_snapshot`
- `drawing_code_snapshot`
- `unit_price_snapshot`
- `currency_snapshot`
- `quantity_snapshot`
- `tolerance_snapshot`
- `lead_time_snapshot`
- `catalog_version_snapshot`

## When Snapshot Happens

Quote creation:

- Capture initial customer request context.
- Snapshot product/material names if selected.
- Snapshot uploaded drawing metadata.

Quote approval:

- Capture approved price, lead time and final technical assumptions.
- This is the most important commercial snapshot point.

Quote conversion:

- Capture final state before converting to order/project.
- Preserve quote-to-order audit trace.

## Recommendation

Do not implement database changes in Phase 6.1.

Before write migration, create an approved schema plan for snapshot fields and decide which snapshot event is legally/commercially authoritative.
