# Admin Table Frontend Implementation Report

## Delivery identity

- BASE SHA: `e92e98ad1476b34084745399bd82137c1e8d06dd`
- BRANCH: `feat/admin-table-query-frontend`
- Feature: authenticated, allowlisted Admin table queries against the already-merged Admin Query UX backend

## Exact changed files

- `figma_make_frontend/package.json` — appends the new tests to the existing full test command; no dependency change
- `figma_make_frontend/src/App.tsx` — minimal integration replacing six mock admin lists only
- `figma_make_frontend/src/components/AdminTablePage.tsx`
- `figma_make_frontend/src/components/adminTableView.ts`
- `figma_make_frontend/src/components/AdminTablePage.test.ts`
- `figma_make_frontend/src/hooks/useAdminTableQuery.ts`
- `figma_make_frontend/src/hooks/useAdminTableQuery.test.ts`
- `figma_make_frontend/src/services/adminApi.ts`
- `figma_make_frontend/src/services/adminApi.test.ts`
- `figma_make_frontend/src/types/admin.ts`
- `ADMIN_TABLE_FRONTEND_IMPLEMENTATION_REPORT.md`

## Backend contract consumed

| Resource | Endpoint | Filters | Ordering |
| --- | --- | --- | --- |
| Products | `/api/v1/admin/products/` | `status`, `active`, `material` | `created_at`, `product_code`, `name` |
| Customers | `/api/v1/admin/customers/` | `status` | `created_at`, `company_name`, `contact_name` |
| Inventory | `/api/v1/admin/inventory/items/` | `warehouse`, `availability` | `quantity`, `updated_at` |
| Orders | `/api/v1/admin/orders/` | `workflow_status`, `status` | `order_date`, `expected_delivery_date` |
| Workflows | `/api/v1/admin/workflows/` | `decision`, `requested_status` | `created_at`, `order` |
| Transactions | `/api/v1/admin/transactions/` | `entity_type`, `action` | `created_at` |

All resources use only the shared `limit`, `offset`, `search`, and `ordering` keys plus their listed filters. Descending ordering is represented by a leading `-` on an allowlisted ordering value.

## Client query allowlists and pagination

- The resource name selects a static endpoint and static filter/ordering vocabulary.
- The serializer iterates the known filter list; keys supplied only at runtime cannot escape to the URL.
- Tests explicitly prove `customer__email`, `role__permissions`, and `user__password` are not serialized.
- Page is normalized to at least 1.
- Page size is clamped to 1–100, including arbitrary numeric reducer input.
- Offset is deterministically `(page - 1) * pageSize` and cannot be negative.
- Search, filter, ordering, page-size, and resource reset behavior returns to page 1.
- Visible page sizes are 20, 50, and 100.

## Authentication, errors, and privacy

- The client reads the bearer token from the existing `InMemoryAuthSession`.
- Missing token fails before `fetch`; there is no anonymous retry or fallback.
- HTTP 400, 401, 403, and 5xx remain distinct sanitized client/UI errors.
- Timeout, caller cancellation, network failure, malformed JSON, and malformed response shape are distinct.
- A 403 is rendered as an explicit error, never an empty table.
- No token, search term, response, customer, stock, workflow, or transaction data is persisted to `localStorage`, `sessionStorage`, IndexedDB, cookies, or a cache library.
- The transaction parser intentionally excludes the raw backend `payload` from frontend state/rendering.

## Response-shape alignment

Rendering uses only fields already returned by current main:

- Product: `sku`, `name`, `category_name`, `price`, `status`
- Customer: `company_name`, `contact_name`, `country`, `status`
- Inventory: product name, warehouse name, `quantity`, `reserved_quantity`, `reorder_point`
- Order: `order_number`, `customer_name`, `project_name`, `total_amount`, `status`
- Workflow: `order_id`, `requested_status`, `decision`, `requested_by`, `reviewed_by`
- Transaction: `entity_type`, `entity_id`, `action`, `actor`, `created_at`

Intentionally not rendered or assumed: product material/tolerance/activity/archive additions, inventory `available_quantity`, order progress/workflow display expansion, expected-delivery response data, transaction raw payload, or any anonymous/demo/RAG response.

## Dependency and backend impact

- Dependency versions: unchanged.
- `pnpm-lock.yaml`: unchanged.
- `package.json`: test command only; every pre-existing test remains and three focused test files were appended.
- Backend source, serializers, models, routes, permissions, and migrations: unchanged.
- New migration: none.

## Validation

- Focused Admin frontend tests: PASS (`19 passed`)
- Full frontend test suite: PASS (`174 passed`)
- TypeScript typecheck: PASS
- Vite production build: PASS
- Scoped oxfmt check for all new Admin files: PASS. Current-main `App.tsx` and the surgically edited `App.tsx` both report the repository's pre-existing whole-file format debt; CI does not run a whole-App oxfmt check, and this feature intentionally avoids a broad unrelated reformat.
- Backend Admin Query regression: PASS (`22 passed`)
- Django system check: PASS
- `makemigrations --check --dry-run`: PASS (`No changes detected`)
- `git diff --check`: PASS
- Scope/backend/lockfile scan: PASS
- Secret/runtime and browser-persistence scan: PASS

The final pre-commit recheck confirmed these results.

## Scope review

The implementation is limited to the Admin table hook/client/types/UI/tests and this report. It does not include Knowledge adapter, public catalog rollout, anonymous demo/chatbot, AI Sales changes, RAG changes, LINE/n8n, demo seed, deferred serializers, backend changes, migration changes, dependency changes, env files, or runtime/build artifacts.

ADMIN TABLE FRONTEND IMPLEMENTATION: PASS
CURRENT BACKEND CONTRACT ALIGNED: YES
CLIENT QUERY ALLOWLIST: PASS
ARBITRARY QUERY ESCAPE: BLOCKED
PAGINATION BOUNDED: YES
AUTH CONTRACT: PASS
400/401/403 HANDLING: PASS
DEFERRED FIELDS USED: NO
BROWSER STORAGE RISK: NONE
BACKEND CHANGE: NONE
PACKAGE CHURN: NONE
MIGRATION REQUIRED: NO
SCOPE CLEAN: YES
READY TO COMMIT: YES
