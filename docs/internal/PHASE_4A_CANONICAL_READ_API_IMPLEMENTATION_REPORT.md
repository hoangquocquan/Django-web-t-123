# Phase 4A Canonical Read API and Authorization Boundary Report

Date: 2026-09-13 (Asia/Tokyo)

## Final verdict

`READY_FOR_PHASE_4B`

The Phase 4A implementation passed the required static, SQLite, isolated
PostgreSQL 16, Phase 3 preservation, concurrency, rollback, duplicate, and full
backend regression validation. The task-owned PostgreSQL container, network,
volume, and database were removed after ownership verification; port 55436 is
free again.

## Project isolation and baseline

- Working directory: `C:\Users\hoang\Documents\ChatGPT\WEB Ô TÔ DJANGO`
- Git root: `C:/Users/hoang/Documents/ChatGPT/WEB Ô TÔ DJANGO`
- Branch: `codex/demo-database-validation`
- Verified baseline HEAD: `2d90dd027c3c61224759679c24dc6150004a7cda`
- Expected baseline: `2d90dd027c3c61224759679c24dc6150004a7cda`
- Origin: `https://github.com/hoangquocquan/Django-web-t-123.git`
- `django_backend/` and `figma_make_frontend/`: present.
- Initial `git status --short`: empty.

AI FACTORY, n8n, Zalo, 9Router, CODEX_A, CODEX_B, their files, processes,
ports, containers, and configuration were not read, inspected, started,
stopped, or modified. No frontend file was changed. No commit, push, merge,
rebase, reset, stash, deploy, or branch change was performed.

## Authoritative inputs reviewed

- `docs/business/MINI_ENTERPRISE_BUSINESS_SPEC_V1.md`
- `PHASE_2_BUSINESS_DOMAIN_CONTRACT_REPORT.md`
- `docs/database/PHASE_3A_SCHEMA_AND_MIGRATION_PLAN.md`
- `PHASE_3B_MASTER_DATA_RFQ_IMPLEMENTATION_REPORT.md`
- `PHASE_3B_POSTGRESQL_VALIDATION_FINAL_REPORT.md`
- `PHASE_3C_QUOTATION_IMPLEMENTATION_REPORT.md`
- `PHASE_3D_ORDER_PROGRESS_AUDIT_IMPLEMENTATION_REPORT.md`
- `PHASE_3D_GIT_CHECKPOINT_REPORT.md`

The approved read matrix is retained: authenticated Admin, Sales, and Manager
may read Customer, Part, Material, RFQ, Quotation, and Sales Order records. All
three roles may read an entity-scoped audit timeline for an entity they may
read. Only Admin and Manager may read the global audit list.

## Read-only API preflight inventory

The existing API uses Django REST Framework function views, the common
`{"success": true, "data": ...}` envelope, limit/offset pagination, and several
legacy/service-specific permission conventions. Foundation Bearer tokens are
stored as SHA256 hashes and resolved to `FoundationUser` plus role. Existing
`FoundationPermissionService` accepts wildcard grants, so Phase 4A deliberately
uses a separate exact-role/exact-permission boundary.

Relevant routes before Phase 4A:

| Existing route | Methods | Representation/shape | Existing authorization |
| --- | --- | --- | --- |
| `/api/v1/catalog/products/` | GET, POST | Legacy catalog list envelope / replacement write | GET public; replacement write validation |
| `/api/v1/catalog/products/{id}/` | GET, PUT, DELETE | Legacy product detail | GET public; replacement write validation |
| `/api/v1/catalog/materials/` | GET | Legacy material list envelope | Read-only permission class, effectively public |
| `/api/v1/crm/customers/` | GET, POST | Legacy-or-managed CRM customer list | Optional Foundation CRM read; fallback behavior |
| `/api/v1/crm/customers/{id}/` | GET | CRM detail and notes | Optional Foundation CRM read; fallback behavior |
| `/api/v1/business/customers/` | GET, POST | Managed customer list/create | Foundation `customers:read/write` |
| `/api/v1/business/customers/{id}/` | GET, PUT | Managed customer detail/update | Foundation `customers:read/write` |
| `/api/v1/business/products/` | GET, POST | Managed product list/create | Foundation `products:read/write` |
| `/api/v1/business/products/{id}/` | GET, PUT | Managed product detail/update | Foundation `products:read/write` |
| `/api/v1/sales/quotes/` | GET, POST | Legacy `QuoteRequest` list / public replacement intent | GET public; POST replacement validation |
| `/api/v1/sales/quotes/{id}/` | GET | Legacy `QuoteRequest` with items/files | Public read-only |
| `/api/v1/sales/quotes/{id}/files/` | GET | Legacy file metadata list | Public read-only |
| `/api/v1/sales/quotations/` | GET, POST | Existing managed quotation list/create with legacy lowercase fields | Foundation `sales:read/write` |
| `/api/v1/sales/dashboard/` | GET | Persisted sales metrics envelope | Foundation `sales:read` |
| `/api/v1/orders/` | GET, POST | Existing order list/create | Foundation `orders:read/write` |
| `/api/v1/orders/{id}/` | GET, PUT | Existing order detail/update | Foundation `orders:read/write` |
| `/api/v1/workflows/` | GET, POST | Legacy workflow approval list/transition | Foundation `workflows:read/write` |
| `/api/v1/transactions/` | GET | Fragmented legacy transaction history | Foundation `transactions:read` |
| `/api/v1/admin/dashboard/` | GET | Admin dashboard envelope | Foundation `dashboard:read` |
| `/api/v1/admin/customers/`, `/products/`, `/orders/`, `/workflows/` | GET plus legacy writes | Admin interface representations | Plural module `read/write` checks |
| `/api/v1/knowledge/documents/` | GET, POST | Knowledge metadata/upload | Foundation knowledge permission |
| `/api/v1/knowledge/documents/{id}/download/` | GET | Binary download | Foundation knowledge permission |

Terminology collision confirmed: legacy `/sales/quotes/` means customer
`QuoteRequest`, while `/sales/quotations/` means the pre-Phase-4 managed
commercial quotation API. Phase 4A does not rename, replace, or modify either
route and introduces a collision-free `/api/v1/canonical/` namespace.

## Implemented canonical endpoint table

Every endpoint below exposes only GET, HEAD, and authenticated OPTIONS. Unsafe
methods return a canonical 405 response and never reach a domain command.

| Route under `/api/v1/canonical/` | Data | Exact permission |
| --- | --- | --- |
| `customers/`, `customers/{id}/` | Customer list/detail | `customer:view` |
| `parts/`, `parts/{id}/` | Part/Product list/detail | `part:view` |
| `materials/`, `materials/{id}/` | Material list/detail | `material:view` |
| `rfqs/`, `rfqs/{id}/` | Canonical RFQ list/detail | `rfq:view` |
| `rfqs/{id}/lines/` | RFQ lines | `rfq:view` |
| `rfqs/{id}/documents/` | Safe document metadata only | `rfq:view` |
| `rfqs/{id}/technical-reviews/` | Append-only technical review evidence | `rfq:view` |
| `quotation-families/`, `quotation-families/{family}/` | Quotation families | `quotation:view` |
| `quotation-families/{family}/revisions/` | Family revision list | `quotation:view` |
| `quotations/`, `quotations/{id}/` | Global revision list/detail | `quotation:view` |
| `quotations/{id}/lines/` | Immutable commercial lines | `quotation:view` |
| `quotations/{id}/approval-decisions/` | Approval/rejection evidence | `quotation:view` |
| `quotations/{id}/customer-decisions/` | Redacted customer decision evidence | `quotation:view` |
| `orders/`, `orders/{id}/` | Sales Order list/detail | `order:view` |
| `orders/{id}/lines/` | Immutable order snapshot lines | `order:view` |
| `orders/{id}/progress/` | Append-only progress timeline | `order:view` |
| `timelines/{entity_type}/{entity_id}/` | Entity-scoped canonical audit timeline | Entity's exact view permission |
| `audit-events/` | Bounded global audit list | `audit:view`; Admin/Manager only |

## Authentication and RBAC boundary

| Role | Customer/Part/Material | RFQ/review/docs | Quotation | Order/progress | Entity timeline | Global audit |
| --- | --- | --- | --- | --- | --- | --- |
| Admin | Read | Read | Read | Read | Read | Read |
| Sales | Read | Read all in MVP | Read all revisions | Read | Read for permitted entity | Denied |
| Manager | Read | Read | Read | Read | Read | Read |

Each request must authenticate a non-expired Foundation Bearer token. The user
must be active, the role name must be exactly `Admin`, `Sales`, or `Manager`,
the role must be approved for the resource, and the role must hold the exact
`module:action` permission row. Wildcard permissions are never consulted.
Inactive, unassigned, malformed-role, and wildcard-only users fail closed. No
role or user assignment is inferred or created by the API.

## Response and error contract

Successful reads use:

```json
{"success": true, "data": {}}
```

List `data` contains `count`, `limit`, `offset`, `next_offset`,
`previous_offset`, and `results`. Errors use one envelope:

```json
{
  "success": false,
  "error": {
    "code": "stable_machine_code",
    "message": "safe message",
    "details": {}
  }
}
```

Stable codes exercised include `authentication_required`,
`authentication_failed`, `permission_denied`, `not_found`,
`method_not_allowed`, `invalid_query_parameter`, `unsupported_filter`,
`unsupported_ordering`, and `unsupported_entity_type`.

Canonical workflow status tokens remain uppercase. Legacy records expose a
null canonical status plus an explicit `compatibility` object containing the
unchanged legacy status; reads never promote `LEGACY` to `MVP_V1`. Decimal
money and quantity are strings, not floats. Datetimes are timezone-aware ISO
8601 strings.

## Pagination, filtering, and ordering

- Default page size: 20.
- Maximum page size: 100; larger or invalid values return 400.
- Offset must be a nonnegative integer.
- Unknown query parameters return `unsupported_filter`.
- Unknown ordering fields return `unsupported_ordering`.
- Only model-specific allowlists are mapped to ORM fields.
- Common allowlists include contract/status/currency/customer/assignee/source
  identifiers and safe business dates/codes. Nested line/event endpoints allow
  only relevant identifiers/status/action and stable ordering.
- No caller-provided ORM lookup or serializer field name is evaluated.

## Query-count and ORM evidence

All ORM access is isolated in `CanonicalReadService`; API views contain no
direct `.objects` access. List/detail querysets use explicit `select_related`
and quotation families use a controlled `Prefetch`. The focused query-count
test compares a one-row customer list with a six-row list: query count remains
identical and at most four queries, including token authentication, exact
permission lookup, count, and page fetch.

## Security and redaction evidence

- Password hashes, token hashes/raw tokens, idempotency keys, request hashes,
  and credential material are not serialized.
- RFQ document `storage_key` is never serialized; original names are reduced to
  a basename, and no download endpoint is added.
- Quotation customer snapshots omit email and phone.
- Customer decision contact/evidence text is not returned; only evidence-
  present booleans and the decision record are exposed.
- Audit metadata is reduced to a fixed safe allowlist; arbitrary metadata is
  never returned.
- No uncontrolled model serializer or ORM field exposure is used.

## Compatibility and mutation evidence

Legacy route names, method sets, callbacks, and representations remain
unchanged. Resolver regression tests confirm `/sales/quotes/` and
`/sales/quotations/` still expose their prior GET/POST contracts. Full backend
regression tests exercise the existing endpoint behavior.

Canonical read tests snapshot order, quotation, progress, and audit counts and
statuses before and after multiple reads; all values remain identical and no
`AuditEvent` is created. Authenticated POST, PUT, PATCH, and DELETE requests to
canonical routes return 405 with `method_not_allowed`. No Phase 3 migration was
modified and no Phase 4B/4C/4D command or frontend binding was implemented.

## Changed files and SHA256

```text
6cad09607afdc25f930f0a2f7e859325d35bdb88231550ff3e94a7b54d98c6a7  django_backend/apps/api/urls.py
08e4a7e2d112c4dabc8495cae68d40ca00316a3b0ca2296d39be534f66a43ea7  django_backend/apps/api/canonical_contract.py
d961c8f1a9f9798b540e910f2ccda7c4e399f72ccce34fdb0dc99c08c5a31b47  django_backend/apps/api/canonical_permissions.py
36d48b6c9a7ff90e6396e095bea5c24b7abe889900a2735a5102ff3b7598474f  django_backend/apps/api/canonical_urls.py
da66e733bd9037ec854c634f3cfbf7395df2e8d1a29b94bcfde17ce112b77f03  django_backend/apps/api/serializers/canonical.py
103088e6e5e18a9597f3df6ba2f038955e00da4331b95994095696b2456ad605  django_backend/apps/api/services/canonical_read_service.py
d4d83832841946af7fe817b1cf576a2435c7383b413132a898f04671446e56ee  django_backend/apps/api/views/canonical.py
3dd1107e7ed886176ee568dff3d5e8dc6998fd79e9838e4b0e7619da667a503c  django_backend/apps/api/tests/test_phase4a_canonical_read_api.py
```

This report omits its own hash because embedding it would change its digest.

## Validation results

### Static and SQLite validation

- `python manage.py check`: passed, zero issues.
- `python manage.py makemigrations --check --dry-run`: passed, no changes detected.
- Python bytecode/parser check for all changed Python files: passed.
- `git diff --check`: passed; only informational Windows LF-to-CRLF notice.
- Focused Phase 4A API suite: **16 passed in 6.11s**.
- Full backend SQLite suite: **172 passed, 143 skipped in 46.24s**.

The focused suite covers unauthenticated/inactive/unassigned/malformed/
wildcard denial, role matrix, all endpoint groups, object visibility,
uppercase statuses, aware datetimes, exact Decimal strings, bounded
pagination, allowlisted filtering/ordering, unsupported query denial,
redaction, read non-mutation, no read audit creation, stable query counts,
RFQ/Quotation terminology, legacy compatibility, global/entity audit rules,
safe methods, method denial, and error codes.

### PostgreSQL 16 and preservation validation

- Clean `python manage.py migrate --noinput`: passed from zero tables through
  all Phase 3D migrations.
- `python manage.py migrate --check`: passed.
- Focused Phase 4A API suite: **16 passed in 12.33s**.
- Phase 3B preservation suite: **26 passed, 1 skipped in 31.43s**.
- Phase 3C preservation suite: **18 passed in 31.19s**.
- Phase 3D preservation suite: **15 passed in 33.62s**.
- Full backend PostgreSQL suite: **174 passed, 141 skipped in 74.29s**.

The authoritative Phase 3 suites were executed in separate fresh pytest
database lifecycles because each migration-state suite intentionally migrates
the database to its own phase boundary. A diagnostic command that concatenated
all three phase suites in one pytest lifecycle produced 57 passes, 1 skip, and
2 order-dependent failures after the Phase 3B and Phase 3C migration tests left
the shared test schema at their respective historical endpoints. Rerunning
each phase in its correct isolated lifecycle passed, and the independently
collected full suite also passed. No source or migration change was made for
this orchestration artifact.

PostgreSQL-specific concurrency passed: simultaneous quotation revision
allocation produced one winner without duplicate revisions, and 20 concurrent
idempotent quotation conversions produced one order. Idempotency hash conflict,
effective quotation/order duplicate, database constraint, invalid transition,
maker-checker, rejection-reason, and failure-injection rollback cases also
passed in the Phase 3C and Phase 3D preservation suites.

## Docker and port isolation

- Host port `127.0.0.1:55436` was verified free before resource creation.
- Docker Client: 29.4.3, API 1.54, windows/amd64, context `desktop-linux`.
- Docker Server: Docker Desktop 4.74.0, Engine 29.4.3, API 1.54,
  linux/amd64.
- PostgreSQL: **16.14 (Debian 16.14-1.pgdg13+1), 64-bit**.
- Task label: `com.openai.task=django-phase4a-20260913-2d90dd01`.
- Repository label: `com.openai.repo=Django-web-t-123`.
- Container:
  `django-phase4a-postgres16-validation-20260913-2d90dd01`, ID
  `707d05c6237f2b176d59f5cab26d0f6b704eaaad6138fdc0bedfc034cca13c72`,
  image `postgres:16`.
- Network: `django-phase4a-validation-net-20260913-2d90dd01`, ID
  `eef97a4fdef0502142479b524fb52fbc97f521db019732466e1c5ae55c7b2636`.
- Volume: `django-phase4a-postgres16-data-20260913-2d90dd01`.
- Database: `django_phase4a_validation_20260913`.
- The only published mapping was `127.0.0.1:55436 -> 5432/tcp`.
- Exact-name inspection proved the container used only the task network and
  task volume and that all three resources carried both ownership labels.
- Cleanup removed exactly the task-owned container, network, and volume.
  Exact-name post-cleanup inspection returned not found for all three.
- Port 55436 was verified free after cleanup.
- Ports 5678, 5680, 5681, 5682, and 20128 were not used or inspected.

## Final Git status

```text
 M django_backend/apps/api/urls.py
?? PHASE_4A_CANONICAL_READ_API_IMPLEMENTATION_REPORT.md
?? django_backend/apps/api/canonical_contract.py
?? django_backend/apps/api/canonical_permissions.py
?? django_backend/apps/api/canonical_urls.py
?? django_backend/apps/api/serializers/canonical.py
?? django_backend/apps/api/services/canonical_read_service.py
?? django_backend/apps/api/tests/test_phase4a_canonical_read_api.py
?? django_backend/apps/api/views/canonical.py
```

The Phase 3 checkpoint commit remains unchanged. These are the only worktree
changes.

## Remaining blocker and exact next scope

No Phase 4A blocker remains. PostgreSQL validation is closed and all task-owned
Docker resources have been removed.

Only after that succeeds, the recommended Phase 4B scope is canonical Customer,
Part, Material, and RFQ command APIs with exact action permissions,
idempotency, audit, and legacy-write preservation. No Phase 4B work is included
here.

`READY_FOR_PHASE_4B`
