# API Cutover Matrix

## Purpose

Phase 9.1 prepares Django as the read-only application API layer for migrated
business modules. The legacy database remains the source of data and all access
must pass through service and repository boundaries.

## Matrix

| Domain | Endpoint | Service used | Read/Write status | Legacy dependency | Migration status |
|---|---|---|---|---|---|
| Catalog | `GET /api/v1/catalog/products/` | `CatalogService.list_products()` | Read-only | `products`, `product_categories` | Cutover-ready |
| Catalog | `GET /api/v1/catalog/products/<id>/` | `CatalogService.get_product_detail()` | Read-only | `products`, `product_images` | Cutover-ready |
| Catalog | `GET /api/v1/catalog/categories/` | `CatalogService.list_categories()` | Read-only | `product_categories` | Cutover-ready |
| Catalog | `GET /api/v1/catalog/materials/` | `CatalogService.list_materials()` | Read-only | `materials` | Cutover-ready |
| CRM | `GET /api/v1/crm/customers/` | `CrmService.list_customer_profiles()` | Read-only | `customers`, `customer_notes` | Cutover-ready |
| CRM | `GET /api/v1/crm/customers/<id>/` | `CrmService.get_customer_profile()` | Read-only | `customers`, `customer_notes` | Cutover-ready |
| CRM | `GET /api/v1/crm/contact-requests/` | `CrmService.list_contact_requests()` | Read-only | `contact_requests` | Cutover-ready |
| Sales | `GET /api/v1/sales/quotes/` | `QuotationService.list_quotes()` | Read-only | `quote_requests`, `customers` | Cutover-ready |
| Sales | `GET /api/v1/sales/quotes/<id>/` | `QuotationService.get_quote_detail()` | Read-only | `quote_requests`, `quote_request_items`, `quote_files` | Cutover-ready |
| Sales | `GET /api/v1/sales/quotes/<id>/files/` | `QuotationService.list_quote_files()` | Read-only | `quote_files` | Cutover-ready |
| CMS | `GET /api/v1/cms/pages/` | `CmsService.list_public_pages()` | Read-only | `cms_pages` | Cutover-ready |
| CMS | `GET /api/v1/cms/pages/<slug>/` | `CmsService.get_public_page()` | Read-only | `cms_pages` | Cutover-ready |
| CMS | `GET /api/v1/cms/menu/` | `CmsService.list_navigation()` | Read-only | `cms_menu_items` | Cutover-ready |
| Auth | `GET /api/v1/auth/profile/` | `AuthCompatibilityService.get_user_auth_profile()` | Read-only | `admin_users` | Preparation only |
| Auth | `GET /api/v1/auth/permissions/` | `AuthCompatibilityService.get_permissions_for_role()` | Read-only | static role matrix | Preparation only |

## Architecture Rule

```text
API View
  -> Service Layer
  -> Repository Layer
  -> Django ORM using("legacy")
  -> Legacy SQLite
```

No API view may call `.objects` or `.using("legacy")` directly.

## Cutover Boundary

Phase 9.1 does not introduce write APIs, login cutover, session mutation, token
generation, or database ownership migration.
