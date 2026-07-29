# Wave 2 Database Report

## New Managed Tables

- `business_products`
- `business_customers`
- `inventory_warehouses`
- `inventory_items`
- `inventory_transactions`

## Seed Strategy

Products and customers are copied from the legacy SQLite database in read-only mode.

Inventory has no legacy source table, so Wave 2 creates a `MAIN` demo warehouse and initial balances for the first migrated products.

## Compatibility Strategy

Legacy tables remain unchanged:

- `products`
- `product_categories`
- `customers`
- related legacy catalog and CRM tables

## Destructive Change Review

No destructive migration was created. No legacy table is dropped, renamed, or altered.

## Validation Strategy

Tests verify:

- migrated product rows exist
- migrated customer rows exist
- inventory rows exist
- negative stock is blocked and rolled back
- legacy Product and Customer models remain read-only
