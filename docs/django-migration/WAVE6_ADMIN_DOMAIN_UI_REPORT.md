# Wave 6 Admin Domain UI Report

## Migrated Screens

| Screen | Django route | Read owner | Write owner |
| --- | --- | --- | --- |
| Dashboard | `/admin/` | Django ORM counters | Not applicable |
| Products list/create | `/admin/products/` | `BusinessProductService` | `BusinessProductService` |
| Product detail/update | `/admin/products/<id>/` | `BusinessProductService` | `BusinessProductService` |
| Customers list/create | `/admin/customers/` | `BusinessCustomerService` | `BusinessCustomerService` |
| Customer detail/update | `/admin/customers/<id>/` | `BusinessCustomerService` | `BusinessCustomerService` |
| Inventory | `/admin/inventory/` | `InventoryService` | `InventoryService` |
| Stock adjustment | `/admin/inventory/items/<id>/adjust/` | `InventoryService` | `InventoryService` |
| Orders list/create | `/admin/orders/` | `OrderService` | `OrderService` |
| Order detail/update | `/admin/orders/<id>/` | `OrderService` | `OrderService` |
| Workflows | `/admin/workflows/` | `WorkflowService` | `WorkflowService` |
| Transaction history | `/admin/transactions/` | `TransactionHistoryService` | Append-only service history |

## UI Pattern

```text
Template form
-> Django form validation
-> Foundation permission check
-> Django service layer
-> Django ORM
-> Template response with message
```

## Validation Messages

The UI uses Django messages to show:

- success after create/update actions
- permission errors
- validation errors
- missing object errors

## Legacy Calls

Wave 6 UI does not call:

- `backend/services`
- `backend/repositories`
- legacy custom HTTP handlers

## Remaining Legacy Screens

Still not migrated in Wave 6:

- Categories
- News
- Media manager
- Pages
- Menus
- Banners
- Contact/quote legacy UI details
- Newsletter UI
- Settings
- AI admin tools
- Developer tools

## Result

The main migrated admin domains now have Django-owned browser screens.
