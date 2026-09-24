# Wave 2 Inventory Report

## Ownership Result

Django now owns the inventory domain.

Implemented:

- `InventoryWarehouse`
- `InventoryItem`
- `InventoryTransaction`
- `InventoryService`
- `/api/v1/inventory/warehouses/`
- `/api/v1/inventory/items/`
- `/api/v1/inventory/items/<id>/adjust/`

## Legacy Compatibility

The legacy database has no dedicated inventory, stock, or warehouse tables. Wave 2 therefore creates Django-owned inventory tables and links stock balances to `BusinessProduct`.

## Transaction Safety

`InventoryService.adjust_stock()` runs inside a database transaction, locks the item row, prevents negative stock, and writes an append-only transaction record.

## Safety

No legacy schema is modified. Inventory starts as Django-owned demo stock generated from migrated products.
