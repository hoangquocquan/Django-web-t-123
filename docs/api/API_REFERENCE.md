# API Reference

## Scope

This reference covers the Django read-only API layer prepared in Phase 9.1 and
hardened in Phase 9.2. These APIs read from the legacy SQLite database through
service and repository boundaries.

## Common Response Format

Success:

```json
{
  "success": true,
  "data": {}
}
```

List success:

```json
{
  "success": true,
  "data": {
    "count": 25,
    "limit": 20,
    "offset": 0,
    "next_offset": 20,
    "results": []
  }
}
```

Error:

```json
{
  "success": false,
  "error": {
    "code": "not_found",
    "message": "Product was not found."
  }
}
```

## Pagination

List endpoints support:

| Parameter | Type | Default | Maximum | Description |
|---|---:|---:|---:|---|
| `limit` | integer | 20 | 100 | Number of rows returned |
| `offset` | integer | 0 | n/a | Row offset from the start |

Invalid pagination returns `400` with error code `invalid_pagination`.

## Endpoints

| Endpoint | Method | Request format | Response format | Permissions | Legacy dependency | Migration status |
|---|---|---|---|---|---|---|
| `/api/health` | GET | none | legacy health JSON | public read | legacy database file check | cutover |
| `/api/v1/health` | GET | none | legacy health JSON | public read | legacy database file check | cutover |
| `/api/v1/catalog/products/` | GET | `limit`, `offset` | paginated products | read-only | `products`, `product_categories` | cutover-ready |
| `/api/v1/catalog/products/<id>/` | GET | path id | product detail | read-only | `products`, `product_images` | cutover-ready |
| `/api/v1/catalog/categories/` | GET | `limit`, `offset` | paginated categories | read-only | `product_categories` | cutover-ready |
| `/api/v1/catalog/materials/` | GET | `limit`, `offset` | paginated materials | read-only | `materials` | cutover-ready |
| `/api/v1/crm/customers/` | GET | `limit`, `offset` | paginated customers | read-only | `customers`, `customer_notes` | cutover-ready |
| `/api/v1/crm/customers/<id>/` | GET | path id | customer detail | read-only | `customers`, `customer_notes` | cutover-ready |
| `/api/v1/crm/contact-requests/` | GET | `limit`, `offset` | paginated contacts | read-only | `contact_requests` | cutover-ready |
| `/api/v1/sales/quotes/` | GET | `limit`, `offset` | paginated quotes | read-only | `quote_requests`, `customers` | cutover-ready |
| `/api/v1/sales/quotes/<id>/` | GET | path id | quote detail | read-only | `quote_requests`, `quote_request_items`, `quote_files` | cutover-ready |
| `/api/v1/sales/quotes/<id>/files/` | GET | `limit`, `offset` | paginated file metadata | read-only | `quote_files` | cutover-ready |
| `/api/v1/cms/pages/` | GET | `limit`, `offset` | paginated pages | read-only | `cms_pages` | cutover-ready |
| `/api/v1/cms/pages/<slug>/` | GET | path slug | page detail | read-only | `cms_pages` | cutover-ready |
| `/api/v1/cms/menu/` | GET | `location`, `limit`, `offset` | paginated nested menu items | read-only | `cms_menu_items` | cutover-ready |
| `/api/v1/auth/profile/` | GET | `admin_id` or `X-Demo-Admin-Id` | safe profile fields | read-only | `admin_users` | preparation only |
| `/api/v1/auth/permissions/` | GET | `role` | permission matrix | read-only | static matrix | preparation only |

## Permission Policy

Only safe HTTP methods are allowed for business APIs. `POST`, `PUT`, `PATCH`,
and `DELETE` are rejected until write API transaction design is approved.
