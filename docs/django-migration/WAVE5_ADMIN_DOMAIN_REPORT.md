# Wave 5 Admin Domain Report

## Purpose

This report lists the admin business operations moved to Django-owned APIs in Wave 5.

## Implemented Django Admin APIs

| Domain | Endpoint | Django service/model owner |
| --- | --- | --- |
| Dashboard | `GET /api/v1/admin/dashboard/` | Django ORM counters |
| Permissions | `GET /api/v1/admin/permissions/` | `FoundationPermissionService`, `FoundationRole` |
| Products | `GET/POST /api/v1/admin/products/` | `BusinessProductService`, `BusinessProduct` |
| Product detail | `GET/PUT /api/v1/admin/products/<id>/` | `BusinessProductService` |
| Customers | `GET/POST /api/v1/admin/customers/` | `BusinessCustomerService`, `BusinessCustomer` |
| Customer detail | `GET/PUT /api/v1/admin/customers/<id>/` | `BusinessCustomerService` |
| Warehouses | `GET/POST /api/v1/admin/inventory/warehouses/` | `InventoryService`, `InventoryWarehouse` |
| Inventory items | `GET/POST /api/v1/admin/inventory/items/` | `InventoryService`, `InventoryItem` |
| Inventory adjustment | `POST /api/v1/admin/inventory/items/<id>/adjust/` | `InventoryService` |
| Orders | `GET/POST /api/v1/admin/orders/` | `OrderService`, `TransactionOrder` |
| Order detail | `GET/PUT /api/v1/admin/orders/<id>/` | `OrderService` |
| Workflows | `GET/POST /api/v1/admin/workflows/` | `WorkflowService`, `WorkflowApproval` |
| Transaction history | `GET /api/v1/admin/transactions/` | `TransactionHistoryService`, `TransactionHistory` |

## Service Pattern

Admin views do not call legacy repositories or legacy services. They use this flow:

```text
Admin API request
-> Foundation token and permission check
-> Django serializer validation
-> Django service layer
-> Django ORM model
-> JSON response
```

## Database Impact

Wave 5 does not create new database tables. It uses the Django-owned tables created in previous waves:

- Foundation auth/user/permission tables.
- Business core product/customer/inventory tables.
- Transaction domain order/workflow/history tables.

## API Impact

Wave 5 adds new Django admin API endpoints under `/api/v1/admin/`.

It does not remove or reroute existing legacy `/admin` pages.

## Result

Django now owns admin operations for domains that were already migrated to Django ownership.
