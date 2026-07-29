# Wave 3 Order Report

## Ownership Result

Django now owns new order writes through `apps.transaction_domain`.

Implemented:

- `TransactionOrder`
- `TransactionOrderItem`
- `OrderService`
- `/api/v1/orders/`
- `/api/v1/orders/<id>/`

## Legacy Compatibility

Legacy quote models in `apps.sales` remain unmanaged and read-only. Existing quote read APIs remain available.

## Data Migration

Migration `transaction_domain.0002_seed_transaction_domain_from_legacy` copies legacy `quote_requests` and `quote_request_items` into Django-owned order tables using legacy reference IDs.

## Inventory And Customer Integration

Orders reference `BusinessCustomer`. Order items can reference `BusinessProduct` and `InventoryItem`. Creating an order can reserve inventory inside the same database transaction.

## Safety

Legacy quote tables are not updated or deleted. Payment processing is not migrated.
