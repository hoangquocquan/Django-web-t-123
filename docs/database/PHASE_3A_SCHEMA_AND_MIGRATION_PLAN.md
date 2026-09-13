# Phase 3A Schema and Migration Plan R2

Status: **R2 DESIGN COMPLETE — NO SCHEMA OR DATA CHANGE EXECUTED**

Date: 2026-09-09
Input contract: `docs/business/MINI_ENTERPRISE_BUSINESS_SPEC_V1.md`
Checkpoint base: `41753f485f437ecde2cf19e3101d856e7e96a54c`

## 1. Scope and non-actions

This document fixes the persistence choices and migration order for the MVP flow
Customer → RFQ → Technical Review → Quotation → Approval → Customer
Decision → Sales Order → Progress → Audit.

Phase 3A is design-only. It does not change `models.py`, create or edit a
migration, run `migrate`, import or mutate data, change API behavior, or change
the React application. The inventory below is based on Django model metadata,
current migrations, repositories, services, tests, admin/server-rendered views,
and `/api/v1/` routes.

## 2. Definitive source-of-truth decisions

| Domain concept | Canonical model decision | Target table | Decision |
| --- | --- | --- | --- |
| Customer | Extend `business_core.BusinessCustomer`; do not create a third customer model | `business_customers` | `KEEP_AND_EXTEND` |
| Part/Product | Extend `business_core.BusinessProduct`, presented canonically as Part | `business_products` | `KEEP_AND_EXTEND` |
| Material | Create `business_core.BusinessMaterial`; legacy `catalog.Material` is import/reference only | `business_materials` | `CREATE_NEW` |
| RFQ | Create `sales.SalesRfq` | `sales_rfqs` | `CREATE_NEW` |
| RFQLine | Create `sales.SalesRfqLine` | `sales_rfq_lines` | `CREATE_NEW` |
| RFQDocument | Create `sales.SalesRfqDocument`; do not reuse generic `KnowledgeDocument` | `sales_rfq_documents` | `CREATE_NEW` |
| TechnicalReview | Create append-oriented `sales.SalesTechnicalReview` | `sales_technical_reviews` | `CREATE_NEW` |
| Quotation family/revision | Extend `sales.SalesQuotation`; one row is one immutable revision and `rfq_id` is the family key | `sales_platform_quotations` | `KEEP_AND_EXTEND` |
| QuotationLine | Extend `sales.SalesQuotationLine` into an immutable snapshot line | `sales_platform_quotation_lines` | `KEEP_AND_EXTEND` |
| ApprovalDecision | Create `sales.SalesQuotationApprovalDecision`; do not reuse order `WorkflowApproval` | `sales_quotation_approval_decisions` | `CREATE_NEW` |
| CustomerDecision | Create `sales.SalesQuotationCustomerDecision` | `sales_quotation_customer_decisions` | `CREATE_NEW` |
| SalesOrder | Extend `transaction_domain.TransactionOrder`; no parallel order header | `transaction_orders` | `KEEP_AND_EXTEND` |
| SalesOrderLine | Extend `transaction_domain.TransactionOrderItem` as the frozen order line | `transaction_order_items` | `KEEP_AND_EXTEND` |
| OrderProgressEvent | Create `transaction_domain.OrderProgressEvent`; retain old status history for historic reads | `transaction_order_progress_events` | `CREATE_NEW` |
| AuditEvent | Create `transaction_domain.AuditEvent`; old fragmented histories remain historic | `transaction_audit_events` | `CREATE_NEW` |
| Role/Permission | Extend `FoundationRole`, `FoundationPermission`, and the through table | existing foundation tables | `KEEP_AND_EXTEND` |

The quotation choice is final: **extend `SalesQuotation`**. A separate family
table is unnecessary in V1 because the RFQ is the stable family boundary;
`UniqueConstraint(rfq, revision)` provides revision identity. The order choice
is also final: **extend `TransactionOrder`** and make its source quotation
unique. Existing primary keys and foreign keys are therefore preserved.

## 3. Current model inventory

Consumer labels are intentionally compact: API means DRF endpoints/serializers;
Django UI means `admin_ui`, `business_ui`, or `website`; service includes domain
services and AI/knowledge adapters; legacy repository always uses the explicit
`legacy` alias. All omitted primary keys are Django `BigAutoField id`.

| Model | App | Managed? | DB table | PK | Business key | Relations | Consumer | Decision |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| `FoundationPermission` | foundation | Yes | `foundation_permissions` | id | `code`; `(module, action)` | roles M2M | foundation/API permission checks, all protected modules | `KEEP_AND_EXTEND` |
| `FoundationRole` | foundation | Yes | `foundation_roles` | id | `name` | permissions M2M, users | foundation service/API, admin UI | `KEEP_AND_EXTEND` |
| `FoundationRolePermission` | foundation | Yes | `foundation_role_permissions` | id | `(role, permission)` | role, permission CASCADE | foundation service | `KEEP_AND_EXTEND` |
| `FoundationUser` | foundation | Yes | `foundation_users` | id | `email`, optional `legacy_admin_id` | role PROTECT | authentication, all actor/owner consumers | `KEEP_AND_EXTEND` |
| `FoundationUserProfile` | foundation | Yes | `foundation_user_profiles` | id | one-to-one user | user CASCADE | foundation API/service | `KEEP_AND_EXTEND` |
| `FoundationAuthToken` | foundation | Yes | `foundation_auth_tokens` | id | `token_hash` | user CASCADE | authentication service | `KEEP_AND_EXTEND` |
| `FoundationLoginAttempt` | foundation | Yes | `foundation_login_attempts` | id | none | none | authentication/security | `KEEP_AND_EXTEND` |
| `FoundationTwoFactorChallenge` | foundation | Yes | `foundation_two_factor_challenges` | id | `challenge_id` | user CASCADE | authentication/security | `KEEP_AND_EXTEND` |
| `BusinessProduct` | business_core | Yes | `business_products` | id | `slug`, optional `legacy_product_id`; SKU not unique | inventory, quote/order lines | business/admin APIs, Django UI, services, AI/knowledge | `KEEP_AND_EXTEND` |
| `BusinessCustomer` | business_core | Yes | `business_customers` | id | optional `legacy_customer_id`; no current code | CRM, sales, orders | business/admin APIs, Django UI, services, AI/knowledge | `KEEP_AND_EXTEND` |
| `InventoryWarehouse` | business_core | Yes | `inventory_warehouses` | id | `code` | inventory items | inventory API/UI/service | `DEFERRED` |
| `InventoryItem` | business_core | Yes | `inventory_items` | id | `(product, warehouse)` | product/warehouse PROTECT | inventory and current order service | `DEFERRED` |
| `InventoryTransaction` | business_core | Yes | `inventory_transactions` | id | none | item CASCADE | inventory service/API | `DEFERRED` |
| `Category` | catalog | No | `product_categories` | id | `slug` | products | legacy catalog repository/API | `RETAIN_LEGACY_READ_ONLY` |
| `Material` | catalog | No | `materials` | id | `name` | product/RFQ join rows | legacy catalog repository/API | `RETAIN_LEGACY_READ_ONLY` |
| `Machine` | catalog | No | `machines` | id | none | capability join rows | legacy catalog API/service | `RETAIN_LEGACY_READ_ONLY` |
| `ManufacturingProcess` | catalog | No | `manufacturing_processes` | id | `name` | product process join rows | legacy catalog API/service | `RETAIN_LEGACY_READ_ONLY` |
| `Capability` | catalog | No | `capabilities` | id | none | machine join rows | legacy catalog/API/public UI | `RETAIN_LEGACY_READ_ONLY` |
| `Product` | catalog | No | `products` | id | `slug`; SKU not constrained | category, images/specs/material/process | legacy catalog repository/API/public UI | `RETAIN_LEGACY_READ_ONLY` |
| `ProductImage` | catalog | No | `product_images` | id | none | product CASCADE | legacy product detail | `RETAIN_LEGACY_READ_ONLY` |
| `ProductSpec` | catalog | No | `product_specs` | id | none | product CASCADE | legacy product detail | `RETAIN_LEGACY_READ_ONLY` |
| `ProductMaterial` | catalog | No | `product_materials` | `(product, material)` | composite PK | product/material CASCADE | legacy product detail/tests | `RETAIN_LEGACY_READ_ONLY` |
| `ProductProcess` | catalog | No | `product_processes` | `(product, process)` | composite PK | product/process CASCADE | legacy product detail/tests | `RETAIN_LEGACY_READ_ONLY` |
| `CapabilityMachine` | catalog | No | `capability_machines` | `(capability, machine)` | composite PK | capability/machine CASCADE | legacy capability detail/tests | `RETAIN_LEGACY_READ_ONLY` |
| `Customer` | crm | No | `customers` | id | none | notes, quote requests | legacy CRM repository/API | `RETAIN_LEGACY_READ_ONLY` |
| `CustomerNote` | crm | No | `customer_notes` | id | none | customer CASCADE | legacy CRM repository/API | `RETAIN_LEGACY_READ_ONLY` |
| `ContactRequest` | crm | No | `contact_requests` | id | none | none | legacy CRM/public contact API | `RETAIN_LEGACY_READ_ONLY` |
| `CrmCustomerProfile` | crm | Yes | `crm_platform_customer_profiles` | id | one-to-one customer | customer CASCADE, owner SET_NULL | CRM service/API | `DEFERRED` |
| `CrmInteraction` | crm | Yes | `crm_platform_interactions` | id | none | customer CASCADE | CRM service/API | `DEFERRED` |
| `CrmNote` | crm | Yes | `crm_platform_notes` | id | none | customer CASCADE | CRM service | `DEFERRED` |
| `CrmTask` | crm | Yes | `crm_platform_tasks` | id | none | customer CASCADE, owner SET_NULL | CRM service | `DEFERRED` |
| `CrmTimelineEvent` | crm | Yes | `crm_platform_timeline_events` | id | none | customer CASCADE | CRM service | `DEFERRED` |
| `QuoteRequest` | sales | No | `quote_requests` | id | none | legacy customer DO_NOTHING | legacy sales repository/API | `RETAIN_LEGACY_READ_ONLY` |
| `QuoteRequestItem` | sales | No | `quote_request_items` | id | none | request CASCADE, product/material DO_NOTHING | legacy sales repository/API | `RETAIN_LEGACY_READ_ONLY` |
| `QuoteFile` | sales | No | `quote_files` | id | none | request CASCADE | legacy sales repository/API | `RETAIN_LEGACY_READ_ONLY` |
| `SalesLead` | sales | Yes | `sales_platform_leads` | id | none | owner SET_NULL | sales API/service/dashboard | `DEFERRED` |
| `SalesOpportunity` | sales | Yes | `sales_platform_opportunities` | id | none | lead/customer/owner SET_NULL | sales API/service/dashboard | `DEFERRED` |
| `SalesQuotation` | sales | Yes | `sales_platform_quotations` | id | `quotation_number`; current `version` unconstrained per family | opportunity/customer/creator SET_NULL | sales API/service, Django UI, AI, dashboard | `KEEP_AND_EXTEND` |
| `SalesQuotationLine` | sales | Yes | `sales_platform_quotation_lines` | id | none | quotation CASCADE, product SET_NULL | sales service/API serialization | `KEEP_AND_EXTEND` |
| `SalesFollowUp` | sales | Yes | `sales_platform_follow_ups` | id | none | lead/opportunity/customer/owner | sales service | `DEFERRED` |
| `SalesActivity` | sales | Yes | `sales_platform_activities` | id | none | lead/opportunity/customer | sales service/approval history | `DEPRECATE_LATER` |
| `TransactionOrder` | transaction_domain | Yes | `transaction_orders` | id | `order_number`, optional `legacy_quote_request_id` | customer PROTECT, assignee SET_NULL | orders API/service, admin UI, dashboard/knowledge | `KEEP_AND_EXTEND` |
| `TransactionOrderItem` | transaction_domain | Yes | `transaction_order_items` | id | optional `legacy_quote_item_id` | order CASCADE, product/inventory PROTECT | order service/API serialization | `KEEP_AND_EXTEND` |
| `OrderStatusHistory` | transaction_domain | Yes | `order_status_history` | id | none | order CASCADE | workflow service/order detail | `DEPRECATE_LATER` |
| `WorkflowApproval` | transaction_domain | Yes | `workflow_approvals` | id | none | order CASCADE | workflow API/service/admin | `DEPRECATE_LATER` |
| `TransactionHistory` | transaction_domain | Yes | `transaction_history` | id | optional `legacy_event_id` | order SET_NULL | transaction API/admin/dashboard/service | `DEPRECATE_LATER` |
| `DocumentCategory` | knowledge | Yes | `knowledge_document_categories` | id | `name`, `slug` | documents | knowledge API/service | `DEFERRED` |
| `KnowledgeDocument` | knowledge | Yes | `knowledge_documents` | id | none | category SET_NULL, versions/chunks | knowledge/AI API and services | `DEFERRED` |
| `DocumentPermission` | knowledge | Yes | `knowledge_document_permissions` | id | none | document CASCADE | knowledge authorization | `DEFERRED` |
| `DocumentVersion` | knowledge | Yes | `knowledge_document_versions` | id | `(document, version)` | document CASCADE | knowledge service | `DEFERRED` |
| `KnowledgeChunk` | knowledge | Yes | `knowledge_chunks` | id | `(document, chunk_index)` | document CASCADE | search/index service | `DEFERRED` |
| `KnowledgeEmbedding` | knowledge | Yes | `knowledge_embeddings` | id | one-to-one chunk | chunk CASCADE | search/index service | `DEFERRED` |
| `KnowledgeAssistantLog` | knowledge | Yes | `knowledge_assistant_logs` | id | none | none | assistant service | `DEFERRED` |

`SalesActivity` may continue to hold lead/opportunity notes, but it is not the
canonical approval or audit record. `WorkflowApproval`, `OrderStatusHistory`,
and `TransactionHistory` stay queryable for historic records; new core-flow
commands stop writing them only after Phase 4 consumers use the new event
contracts.

## 4. Current persistence and migration graph

There is no `DATABASE_ROUTERS` setting and no router implementation. Unmanaged
legacy models inherit `LegacyReadOnlyModel`, which blocks instance and bulk
writes. Their repositories explicitly bind querysets to the optional `legacy`
database alias. Phase 3 must not make those models managed or copy from an
implicit local file.

Relevant current graph:

```text
foundation 0001 -> 0002 legacy seed -> 0003 AI permissions
           -> 0004 sales/CRM permissions -> 0005 sales approval -> 0006 auth hardening

business_core 0001 -> 0002 optional legacy seed

business_core 0002 + foundation 0003 -> crm 0001
business_core 0002 + crm 0001 + foundation 0003 -> sales 0001
business_core 0002 + foundation 0002 -> transaction_domain 0001
transaction_domain 0001 + business_core 0002 -> transaction_domain 0002 legacy seed

knowledge 0001 -> 0002 -> 0003 (independent of the core flow)
```

The migration listing was inspected read-only with `showmigrations --plan`.
No migration was applied. Catalog and unmanaged legacy models have no migration
package because Django does not own those tables.

Current database protections are limited: unique user/role/permission tokens,
customer/product legacy IDs and product slug, quotation/order numbers, several
legacy IDs, M2M uniqueness, inventory uniqueness, and indexes for common status,
lookup, and audit fields. There are no current `CheckConstraint` objects for
positive quantities, money equations, lifecycle validity, required company,
date order, or maker-checker rules.

## 5. R1 target summary (superseded)

This section is retained only as review history. It is not executable guidance.
The exact R2 field catalog, constraints, mappings, and phase boundaries in
sections 12–22 are authoritative wherever R1 lacks detail or differs.

### 5.1 Master data

Extend `BusinessCustomer` with `customer_code`, required `company_name`,
uppercase `status` (`ACTIVE`, `INACTIVE`), normalized `phone`, `created_by`,
`updated_by`, and optional `archived_at`. Keep `legacy_customer_id` immutable.
Add unique `customer_code`, an index on `(status, company_name)`, and a check
that an active customer has nonblank email or phone.

Extend `BusinessProduct` with unique `part_code`, required `revision`, controlled
`unit`, optional `default_material` (`PROTECT`), `tolerance`,
`technical_requirements`, `is_active`, actor metadata, and optional
`archived_at`. Preserve `slug`, SKU, content fields, and `legacy_product_id` for
existing consumers. Add indexes on `(is_active, part_code)` and material.

Create `BusinessMaterial` with unique immutable `material_code`, required
`name`, optional `standard`, `grade`, `description`, `is_active`, actor metadata,
and timestamps. Add `(is_active, name)` index. Archive rather than delete a
referenced material.

### 5.2 RFQ and technical review

Create `SalesRfq` with unique immutable `rfq_number`; `customer` PROTECT;
uppercase lifecycle status; quote due and required delivery dates; creator,
updater, optional assignee; timestamps; project/notes/closure reason; and
optional `legacy_quote_request_id` unique for audited imports. Index
`(status, quote_due_at)`, customer, and assignee. Check required delivery is not
before creation date at service level and `quote_due_at <= required_delivery`
at database level where both are represented as dates/timestamps.

Create `SalesRfqLine` with parent RFQ CASCADE, `line_number`, optional Part and
Material PROTECT, required description, positive Decimal quantity, controlled
unit, required delivery date, tolerance and technical notes, and a
`drawing_required` flag. Unique `(rfq, line_number)`; checks for quantity > 0
and delivery date presence.

Create `SalesRfqDocument` with RFQ CASCADE, optional RFQ line CASCADE,
`document_group_id` UUID, positive version, original filename metadata,
non-public unique `storage_key`, allowlisted extension and MIME, positive size,
SHA-256 checksum, optional document revision, uploader PROTECT, uploaded time,
and optional `replaces` self-PROTECT. Unique `(document_group_id, version)` and
checksum/search indexes. A service must enforce that an attached line belongs
to the same RFQ; SQL cannot express that cross-row invariant portably.

Create immutable `SalesTechnicalReview` rows with RFQ PROTECT, reviewer PROTECT,
decision (`STARTED`, `NEEDS_INFORMATION`, `READY_TO_QUOTE`, `DECLINED`), reason,
notes, requested-fields JSON, and timestamp. Conditional constraints require a
reason for `NEEDS_INFORMATION`/`DECLINED`. Only the domain service changes RFQ
status; review rows are never updated or deleted.

### 5.3 Quotation revision and decisions

Extend `SalesQuotation`; keep its table and PK. Add required-for-V1 `rfq`
PROTECT, zero-based `revision`, canonical lifecycle status, ISO currency,
`valid_from`, `valid_until`, `tax_amount`, terms, sent metadata, customer/RFQ
snapshots, actor metadata, and immutable timestamp fields. Keep `opportunity`,
`customer`, current `version`, `status`, and `approval_status` during the
compatibility period. New code derives customer from RFQ, uses `revision`, and
never trusts client totals.

Add unique `(rfq, revision)`, unique quotation number, date-order and nonnegative
money checks, `discount_total <= subtotal`, exact total equation, and a
conditional unique constraint allowing only one effective revision per RFQ for
the statuses `APPROVED`, `SENT`, or `ACCEPTED`. Index `(rfq, revision)`, status,
validity, and creator. Effective-revision transitions also lock all rows for the
RFQ because a constraint alone does not perform supersession.

Extend `SalesQuotationLine` with `line_number`, optional source RFQ line
PROTECT, part/material/code/description/unit snapshots, positive quantity and
unit price, `line_subtotal`, and snapshot timestamps. Preserve current product,
description, discount, and line total columns until consumers move. Unique
`(quotation, line_number)` with positive/nonnegative money checks and an exact
line calculation check.

Create immutable `SalesQuotationApprovalDecision`: quotation PROTECT and
unique, reviewer PROTECT, `APPROVED`/`REJECTED`, reason, notes, decided time.
Rejection requires a reason. Maker-checker (`reviewer_id != created_by_id`) is
enforced in the transactional service because it crosses the related header.

Create immutable `SalesQuotationCustomerDecision`: quotation PROTECT and unique,
recorder PROTECT, `ACCEPTED`/`DECLINED`, customer contact/evidence snapshot,
reason, decided time. Decline requires a reason. The service verifies the
quotation is `SENT` and not expired.

### 5.4 Sales order, progress, and audit

Extend `TransactionOrder`; keep its table and PK. Add unique nullable
`source_quotation` PROTECT, source RFQ PROTECT, canonical workflow status,
customer/RFQ/quotation snapshots, currency, subtotal/discount/tax/total,
`ordered_at`, required expected delivery date for V1 rows, progress percent,
hold/cancel reasons, completion timestamp, and actor metadata. Preserve current
legacy source IDs and text date/status fields during compatibility. New order
creation is private to the conversion service and allocates `SO-*` numbers.

Extend `TransactionOrderItem` with unique-per-order line number, source
quotation line PROTECT, and complete immutable part/material/description/unit/
price snapshots. Inventory linkage stays optional and deferred; conversion must
not reserve inventory in the MVP unless a later approved contract adds it.

Create append-only `OrderProgressEvent`: order PROTECT, from/to statuses,
0–100 progress, milestone note, reason, stable actor PROTECT, and timestamp.
Checks enforce progress range and a nonblank reason for hold/cancel. Index order
and descending timestamp plus target status.

Create append-only `AuditEvent`: required stable `actor_ref` and display
snapshot, optional `actor_user` PROTECT for human principals, required action,
entity type/ID, timestamp, optional old/new status and reason, safe metadata,
and correlation ID. System events use `actor_ref="system"` rather than a fake
user. Index `(entity_type, entity_id, created_at)`, action/time, actor/time, and
correlation ID. Model manager/admin/API must expose no update or delete path.

### 5.5 Roles and permissions

Create canonical roles named exactly `Admin`, `Sales`, and `Manager` and
action-specific permission codes from the Phase 2 matrix, including at minimum
`customer:view/change/archive`, `part:view/manage`, `material:view/manage`,
`rfq:view/create/change/archive/submit/review`,
`quotation:view/create_revision/change/submit/approve/reject/send/decide/convert`,
`order:view/progress`, `audit:view`, and `user:manage`.

Do not infer that legacy `editor` means Sales or `viewer` means Manager. Keep
legacy `admin/editor/viewer` roles and their existing permissions until an
Owner-reviewed user-to-role assignment exists. New Phase 4 commands fail closed
for users without a canonical action. Historic audit keeps its actor snapshots.

## 6. R1 migration outline (withdrawn)

Do not implement this outline. It is retained to show why R2 was required; the
non-overlapping R2 sequence in section 18 replaces it completely.

Each step is a separate reviewed migration boundary. Names are proposed and may
receive the next generated numeric prefix, but their dependencies and contents
are fixed by this plan.

1. **Preflight, no mutation.** Export counts and collision reports for blank/
   duplicate customer codes, part codes/SKUs, material names, quotation/order
   numbers, status values, orphan legacy IDs, invalid quantities/money, and text
   dates. Record the database engine and verify backup/restore. Abort on unknown
   statuses, duplicate proposed keys, or dangling foreign keys.
2. **`foundation` additive/data migration.** Depend on `foundation.0006`.
   Insert action permissions and the three canonical roles idempotently, without
   reassigning users or deleting old roles. Reverse removes only rows created by
   this migration and only when unreferenced.
3. **`business_core` additive migration.** Depend on
   `business_core.0002` and the new foundation migration. Create Material and add
   all Customer/Part fields as nullable or safely defaulted shadow fields. Add
   non-unique indexes only; do not enforce required/unique constraints yet.
4. **Master-data backfill migration.** Backfill only deterministic mappings.
   Existing immutable legacy IDs may generate stable provisional codes such as
   `CUS-L<id>`/`PART-L<id>`; rows without provenance receive no fabricated code
   and remain `data_contract=LEGACY`. Unresolved rows go to an external data
   exception report. Schema/data migrations never read a legacy database.
5. **Master-data constraint migration.** Run only after the review query returns
   zero invalid canonical rows. Enforce uniqueness/checks for canonical rows;
   `data_contract=LEGACY` rows remain grandfathered until
   Owner-approved remediation is complete.
6. **`sales` additive migration.** Depend on `sales.0001`, the constrained
   business-core migration, and the new foundation migration. Create RFQ,
   document, review, and decision tables; add nullable/shadow quotation fields;
   add indexes and constraints that are safe with existing rows.
7. **Quotation compatibility migration.** Preserve original `status`,
   `approval_status`, and `version` values. Populate canonical fields only when
   evidence is unambiguous. Do not automatically turn `accepted` into a valid
   customer decision or invent an RFQ. Existing rows lacking source/evidence are
   tagged `LEGACY`; new rows are `MVP_V1` and must satisfy the complete contract.
8. **Quotation constraint migration.** Add `(rfq, revision)`, effective-revision,
   date, quantity, and money constraints for `MVP_V1` rows after collision and
   equation queries are clean. A later remediation migration can broaden
   constraints after every legacy row has an approved mapping.
9. **`transaction_domain` additive migration.** Depend on
   `transaction_domain.0002`, the final sales constraint migration, business
   core, and foundation. Extend order/header lines and create progress/audit
   tables. Add the nullable unique source quotation first.
10. **Order compatibility migration.** Preserve old order status/text dates and
    legacy quote IDs. Because legacy `TransactionOrder` rows were seeded from
    `QuoteRequest`, do not assume they are confirmed sales orders. Tag them
    `data_contract=LEGACY`; do not invent accepted quotations or financial
    evidence. Only `MVP_V1` conversion creates canonical `CONFIRMED` orders.
11. **Order constraint migration.** Enforce one-order-per-source quotation,
    snapshot equations, dates, line uniqueness, progress range, and required
    reasons for `MVP_V1` rows after preflight succeeds.
12. **Post-migration verification.** Run `check`, migration drift, full pytest,
    migration forward/reverse tests on disposable databases, invariant SQL
    queries, and API compatibility tests. Compare before/after row counts and
    checksums for untouched legacy/history tables.

Migrations must not read an author-machine path, contact production, or silently
open/create SQLite. Data migrations use historical models from `apps` and are
idempotent. Large backfills are batched and transaction boundaries are explicit.

## 7. Consumer compatibility and cutoff plan

| Stage | Existing consumer behavior | New behavior/cutoff |
| --- | --- | --- |
| Phase 3B schema rollout | Existing APIs/UI/services continue using current fields; legacy endpoints keep explicit read-only alias | New tables/fields are additive and not exposed |
| Phase 4 dual-read | Existing list/detail responses remain stable; serializers can expose opt-in V1 fields | Add `/rfqs/` and command endpoints; use canonical services for all new records |
| Phase 4 write cutoff | `POST /orders/` and generic `/workflows/` writes are deprecated and return a documented conflict/retirement response after the compatibility window | Only accepted-quotation conversion and explicit progress commands write V1 orders |
| Phase 4 terminology cutoff | `/sales/quotes/*` remains a versioned legacy RFQ read API, clearly marked legacy; no writes | Canonical request endpoints use RFQ; `/sales/quotations/*` means commercial quotation |
| Phase 6 UI cutoff | Django/React screens may read old records through compatibility serializers | All new workflow actions use V1 endpoints; hard-coded React data is removed |
| Post-telemetry cleanup | Old rows and endpoints remain readable; no table drop | Remove old write code only after zero-use telemetry, regression tests, and Owner approval |

Direct consumers requiring explicit adapters are `SalesPlatformService`,
`OrderService`, `WorkflowService`, transaction/sales API serializers and views,
`admin_ui`, `business_ui`, dashboard services, AI sales tools, knowledge business
connectors, and `demo_data`. Legacy catalog/CRM/sales repositories are not
redirected to managed tables; they stay clearly named read-only compatibility
sources until separately retired.

Do not dual-write old and new approval/audit rows indefinitely. During the
short Phase 4 compatibility window, one command transaction may write canonical
events and a derived legacy projection for unchanged readers. The canonical row
is authoritative; projection failure rolls back the command. Cut off projection
after all known readers migrate.

## 8. Rollback and recovery

- Additive schema migrations reverse by dropping only newly added empty tables/
  columns on a disposable verification database. Production rollback normally
  rolls application code back while leaving additive schema in place.
- Every data migration has a reverse mapping based on stored source identifiers
  and never deletes the source row. Ambiguous/manual mappings are exported and
  are not auto-reversed.
- Do not reverse after V1 writes exist unless those rows have been exported and
  the Owner explicitly approves data loss. Prefer forward fixes.
- Constraint migrations are last in each app slice and can be reversed without
  removing data. No legacy table, current history table, PK, or source column is
  dropped in Phase 3.
- Before every production-like run, capture backup identifier, row counts, key
  collision report, and restoration evidence. Stop on mismatch.

## 9. Required tests for implementation

- Migration tests from a clean database and from a fixture representing current
  Phase 2 rows; forward and safe reverse for every boundary.
- Legacy-disabled fresh-clone suite remains `0 failed / 0 errors`; optional
  legacy tests retain their explicit skip contract.
- Database tests for unique codes/revisions/source order, positive quantities,
  dates, money equations, one effective revision, progress range, and reasons.
- Service tests for every RFQ/quotation/order transition and every negative
  scenario in the Phase 2 contract, including maker-checker, expiry,
  idempotent conversion, and immutable snapshots/events.
- Concurrency tests for number allocation, revision creation, approval/
  supersession, customer decision, and order conversion.
- Upload tests for allowlist, MIME/content mismatch, traversal, double extension,
  size/count, generated storage keys, checksum, versioning, and authorization.
- Compatibility tests proving current list/detail consumers still read legacy
  and grandfathered managed rows while retired writes fail explicitly.

## 10. Risks and stop conditions

| Risk | Control / stop condition |
| --- | --- |
| Legacy `QuoteRequest` is not a commercial quotation | Never map it to `SalesQuotation`; it may seed/import RFQ only with explicit source evidence |
| Existing `TransactionOrder` originated from quote requests | Do not auto-classify as confirmed order; keep `data_contract=LEGACY` and report unresolved evidence separately |
| Text dates and free-form statuses | Preserve raw values; abort automatic canonical mapping on parse/status ambiguity |
| Missing company/contact or duplicate codes | Report and remediate before required/unique constraints |
| Current accepted/lost quotation lacks decision evidence | Do not fabricate decision rows; keep legacy contract marker |
| Money precision differs from legacy float | Recalculate from Decimal source lines; stop on unexplained delta |
| Partial unique/check support differs by database | Verify generated SQL on SQLite test and target PostgreSQL; PostgreSQL is production authority |
| Generic KnowledgeDocument appears reusable | Keep it separate; RFQ documents require domain FK, version, checksum, and authorization |
| Role aliases over-grant access | No automatic user-role mapping; V1 commands fail closed until reviewed assignment |
| Consumer writes old tables after rollout | Instrument and block old write endpoints at Phase 4 cutoff before removing projection code |

Phase 3B must stop before applying constraints or switching consumers if any
preflight query is nonzero, backup/restore evidence is missing, target database
identity is uncertain, migration SQL drops/renames current data, or a required
mapping would fabricate business evidence.

## 11. R1 entry-gate summary (superseded)

Implementation may start only when the Owner approves this schema plan and the
target database/environment. The implementation PR must contain reviewed model
changes, generated migrations, migration tests, preflight evidence, and no API/
React expansion beyond the compatibility work explicitly assigned. This plan's
decisions are complete; remaining work is implementation and data review, not
domain-model selection.

## 12. R2 record contract and canonical status rules

`data_contract` is persistence provenance, never a lifecycle status. Its exact
type is `CharField(max_length=16, choices=[("LEGACY", "Legacy"),
("MVP_V1", "MVP V1")], db_index=True)`. On populated extended header/detail
tables its additive default is `LEGACY`; on newly created V1-only tables its
default is `MVP_V1`. Future V1 services always set `MVP_V1` explicitly. No
migration promotes an old row to `MVP_V1`.

If review tracking is later required, it lives outside lifecycle as an export
with `model`, `pk`, `issue_code`, `observed_value`, `review_state`, and evidence.
No review-state column is required by Phase 3B–3D. The token formerly proposed
for pending review is not a valid value in any model or migration state.

Canonical choices are fixed:

- Customer `status`: `ACTIVE`, `INACTIVE` only.
- Part and Material: `is_active: BooleanField`, not a status string.
- RFQ `status`: `DRAFT`, `SUBMITTED`, `UNDER_REVIEW`, `NEEDS_INFORMATION`,
  `READY_TO_QUOTE`, `QUOTED`, `DECLINED`, `CLOSED`.
- Quotation `workflow_status`: `DRAFT`, `PENDING_APPROVAL`, `APPROVED`,
  `REJECTED`, `SENT`, `ACCEPTED`, `DECLINED`, `EXPIRED`, `SUPERSEDED`.
- Order `workflow_status`: `CONFIRMED`, `IN_PROGRESS`, `ON_HOLD`, `COMPLETED`,
  `CANCELLED`.

Constraints that would reject valid historic values use
`condition=Q(data_contract="MVP_V1")` or the logically equivalent implication.
Uniqueness for any non-null business code applies to all rows, because two
identical issued codes are never safe regardless of provenance.

## 13. Exact compatibility and shadow-field contract

| Model | Existing field retained | Canonical field | Write policy |
| --- | --- | --- | --- |
| `SalesQuotation` | `status` (`draft/review/approved/sent/accepted/lost`) | `workflow_status` | R1/Phase 3C: old field unchanged; Phase 4 dual-write only through adapter; after Phase 4 cutoff, canonical writes only and `status` read-only |
| `SalesQuotation` | `version` (one-based prototype integer) | `revision` (zero-based RFQ revision) | Phase 3C does not infer `revision` without RFQ evidence; Phase 4 writes `revision` only; `version` becomes read-only at the Phase 4 write cutoff |
| `SalesQuotation` | `approval_status` (free-form compatibility) | `SalesQuotationApprovalDecision.decision` | Phase 3C preserves it; Phase 4 projection may dual-write temporarily; read-only after all approval readers switch |
| `TransactionOrder` | `status` (`new/approved/processing/completed/cancelled`) | `workflow_status` | Phase 3D leaves old field unchanged; Phase 4 adapter dual-writes only where mapping is exact; old field read-only at direct-order/workflow write cutoff |
| `TransactionOrder` | `quoted_at` (`CharField(80)`) | `source_quotation_sent_at` (`DateTimeField`) | Never overwrite text; backfill only when ISO parsing and source evidence are exact |
| `TransactionOrder` | `completed_at` (`CharField(80)`) | `completed_at_v1` (`DateTimeField`) | Never overwrite text; only unambiguous timezone-aware values may backfill |
| `SalesOpportunity` | `expected_close_date` (`CharField(40)`) | none in MVP core | Deferred; no shadow field in Phase 3 |
| `CrmInteraction` | `occurred_at` (`CharField(40)`) | none in MVP core | Deferred; no shadow field in Phase 3 |
| `CrmTask` | `due_date` (`CharField(40)`) | none in MVP core | Deferred; no shadow field in Phase 3 |
| `SalesFollowUp` | `due_date` (`CharField(40)`) | none in MVP core | Deferred; no shadow field in Phase 3 |

New canonical date fields are never backed by string defaults:
`SalesRfq.quote_due_at` and `required_delivery_date` are `DateField`;
quotation validity uses `DateField`; order `ordered_at` is `DateTimeField` and
`expected_delivery_date` is `DateField`. Additive migrations make canonical
fields nullable first; final V1-required checks are conditional on
`data_contract=MVP_V1`.

## 14. Business number strategy (R2.1 clarification)

R2.1 narrows command idempotency to retry-sensitive commercial operations:
RFQ creation, quotation creation/revision, and accepted-quotation-to-order
conversion. Normal Customer, Part, and Material CRUD relies on unique business
codes and does not require command idempotency. Phase 3B supplies only RFQ
schema support; the future Phase 4 command layer owns replay semantics.

Create `business_core.BusinessNumberSequence` with one locked row per
`(namespace, period)`. Formats are `CUS-{value:04d}`, `PART-{value:04d}`,
`MAT-{value:04d}`, `RFQ-{YYYY}-{value:04d}`, `QT-{YYYY}-{value:04d}` for a
quotation family, and `SO-{YYYY}-{value:04d}`. A quotation display number is
`{quotation_family_number}-R{revision}`. The family number is stored once on
the RFQ when R0 is created. Namespaces/periods are exactly:

| Entity | Namespace | Period |
| --- | --- | --- |
| Customer | `CUS` | `GLOBAL` |
| Part | `PART` | `GLOBAL` |
| Material | `MAT` | `GLOBAL` |
| RFQ | `RFQ` | four-digit UTC creation year |
| Quotation family | `QT` | four-digit UTC creation year |
| Sales Order | `SO` | four-digit UTC creation year |

Allocation is one service transaction: `transaction.atomic()`, acquire or
create the sequence row, lock it with `select_for_update()`, increment
`last_value`, persist it, format the code, then insert the entity. Creation of a
missing sequence row handles a unique race by rolling back to a savepoint and
re-reading it locked. Entity-code `IntegrityError` retries the whole allocation
at most **3 attempts** with bounded application jitter; after that it returns a
conflict and writes no entity. Gaps after rollback/crash are allowed; duplicates
are not.

PostgreSQL row locks are the production concurrency authority. SQLite ignores
or weakens `SELECT ... FOR UPDATE` and may return database-lock errors, so SQLite
tests validate formatting, uniqueness, retry bounds, and idempotency but never
claim concurrency parity. PostgreSQL tests use separate connections/processes,
a barrier, and at least 20 simultaneous allocations per namespace/period.

Quotation revision allocation does not use the sequence table. In one atomic
transaction, lock the RFQ row, query `Max("revision")` for that RFQ, allocate
zero for the first revision or max + 1, and insert under unique `(rfq,
revision)`. Retry `IntegrityError` at most 3 attempts. The family number is
allocated once and reused by all revisions.

Every retry-sensitive commercial command must accept a unique idempotency key.
The future service returns the existing entity for the same key and equivalent
request hash; the same key with a different hash is a conflict. Number
allocation and entity insert commit together. Phase 3B implements RFQ storage
and constraint tests only, not this API/service behavior. Allocator tests cover
formatting, uniqueness, and bounded retry and do not claim complete command
idempotency.

## 15. Money contract

All monetary columns use `DecimalField(max_digits=20, decimal_places=4)`.
Quantities use `DecimalField(max_digits=16, decimal_places=4)`. No float is a
source of truth. Supported currencies are exactly `VND` and `USD`.

| Currency | Settlement quantum | Display scale | Rounding |
| --- | --- | --- | --- |
| `USD` | `Decimal("0.01")` | 2 | `ROUND_HALF_UP` |
| `VND` | `Decimal("1")` | 0 | `ROUND_HALF_UP` |

The backend parses Decimal from strings, rejects non-finite values, calculates
raw `quantity * unit_price`, and quantizes each line subtotal to the currency
quantum. Header subtotal is the sum of already-quantized line subtotals.
Header discount and tax are independently quantized; total is
`quantize(subtotal - discount_amount + tax_amount)`. Stored values retain four
decimal places. Client totals are ignored or rejected on mismatch.

DB checks enforce quantity/unit-price positivity, monetary nonnegativity,
`discount_amount <= subtotal`, and the exact same-row header equation
`total = subtotal - discount_amount + tax_amount`. They do not assert that a
header subtotal equals a sum of child rows. They also do not assert
`line_subtotal = quantity * unit_price`, because currency rounding makes a
portable exact expression unsafe. Services and tests own both cross-row and
rounded-line equations.

Legacy catalog price is float and historic money may have two decimal places.
Mapping converts through `Decimal(str(value))`, quantizes using the declared
currency, and compares with a currency tolerance: USD `0.01`, VND `1`. Missing
currency, non-finite values, negative values, or a delta greater than tolerance
go to the exception report and stop promotion; migrations never auto-correct an
unexplained delta or mark that row `MVP_V1`.

## 16. Field-level target schema

Notation: “V1 required” means the database column remains nullable for historic
rows, while a named conditional check plus service/serializer requires it when
`data_contract=MVP_V1`. `PROTECT` is used for business evidence; `CASCADE` is
limited to owned detail rows. Index entries name single/composite indexes;
constraint entries reference section 17. No existing column is dropped or
renamed in Phase 3.

### 16.1 BusinessCustomer

| Field name | Django field type | DB null | Blank | Default | Choices | Relation/on_delete | Mutable | Index | Constraint | Existing source / backfill | Phase |
| --- | --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| `id` | `BigAutoField(primary_key=True)` | No | No | auto | — | — | No | PK | PK | existing `id`; unchanged | existing |
| `legacy_customer_id` | `IntegerField(null=True, unique=True)` | Yes | Yes | None | — | — | No | unique | existing unique | unchanged | existing |
| `data_contract` | `CharField(max_length=16, db_index=True)` | No | No | `LEGACY` | `LEGACY`, `MVP_V1` | — | No after create | single | `ck_customer_v1_required` | all existing rows `LEGACY`; never auto-promote | 3B |
| `customer_code` | `CharField(max_length=32, null=True)` | Yes; V1 required | Yes during rollout | None | — | — | No after issue | single/unique partial | `uq_customer_code_nonnull`, `ck_customer_v1_required` | only deterministic managed evidence; otherwise null/report | 3B |
| `company_name` | `CharField(max_length=220)` | No | compatibility True; V1 false | `""` existing | — | — | Yes while active | composite status/name | `ck_customer_v1_required` | existing value; blank is exception | existing/3B |
| `contact_name` | `CharField(max_length=160)` | No | No | — | — | — | Yes | — | — | unchanged | existing |
| `email` | `EmailField()` | No | Yes | `""` | — | — | Yes | existing email index | `ck_customer_v1_contact` | normalize/validate existing; ambiguous stays legacy | existing/3B |
| `phone` | `CharField(max_length=80)` | No | Yes | `""` | — | — | Yes | — | `ck_customer_v1_contact` | normalize only if lossless; raw exception otherwise | existing/3B |
| `country` | `CharField(max_length=120)` | No | Yes | `Vietnam` | — | — | Yes | — | — | unchanged | existing |
| `status` | `CharField(max_length=16)` | No | No | `ACTIVE` | `ACTIVE`, `INACTIVE` | — | Yes by archive command | status/name | `ck_customer_v1_status` | exact `active/inactive` uppercased; unknown reported | 3B |
| `notes` | `TextField()` | No | Yes | `""` | — | — | Yes | — | — | unchanged | existing |
| `archived_at` | `DateTimeField(null=True)` | Yes | Yes | None | — | — | Only archive | — | — | no backfill | 3B |
| `created_by` | `ForeignKey(FoundationUser, null=True, related_name="created_business_customers")` | Yes; V1 required | Yes rollout | None | — | `PROTECT` | No | single | `ck_customer_v1_required` | map only stable user evidence | 3B |
| `updated_by` | `ForeignKey(FoundationUser, null=True, related_name="updated_business_customers")` | Yes | Yes | None | — | `PROTECT` | Yes | — | — | no invented actor | 3B |
| `created_at` | `DateTimeField(auto_now_add=True)` | No | No | auto | — | — | No | ordering | — | unchanged | existing |
| `updated_at` | `DateTimeField(auto_now=True)` | No | No | auto | — | — | auto | — | — | unchanged | existing |

### 16.2 BusinessProduct and BusinessMaterial

| Entity.field | Django field type | DB null | Blank | Default | Choices | Relation/on_delete | Mutable | Index | Constraint | Existing source / backfill | Phase |
| --- | --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| `BusinessProduct.id` | `BigAutoField(primary_key=True)` | No | No | auto | — | — | No | PK | PK | unchanged | existing |
| `BusinessProduct.legacy_product_id` | `IntegerField(null=True, unique=True)` | Yes | Yes | None | — | — | No | unique | existing unique | unchanged | existing |
| `BusinessProduct.data_contract` | `CharField(max_length=16, db_index=True)` | No | No | `LEGACY` | `LEGACY`, `MVP_V1` | — | No | single | `ck_part_v1_required` | existing `LEGACY` | 3B |
| `BusinessProduct.part_code` | `CharField(max_length=32, null=True)` | Yes; V1 required | Yes rollout | None | — | — | No after issue | unique partial | `uq_part_code_nonnull`, `ck_part_v1_required` | deterministic code only; else report | 3B |
| `BusinessProduct.revision` | `CharField(max_length=32, null=True)` | Yes; V1 required | Yes rollout | None | — | — | Yes before use | — | `ck_part_v1_required` | no safe source; null/report | 3B |
| `BusinessProduct.unit` | `CharField(max_length=8, null=True)` | Yes; V1 required | Yes rollout | None | `PCS`, `KG`, `M`, `MM` | — | Yes before use | — | `ck_part_v1_unit` | map explicit unit only; no guess | 3B |
| `BusinessProduct.default_material` | `ForeignKey(BusinessMaterial, null=True, related_name="default_parts")` | Yes | Yes | None | — | `PROTECT` | Yes | single | — | explicit mapped material only | 3B |
| `BusinessProduct.tolerance` | `CharField(max_length=120)` | No | Yes | `""` | — | — | Yes | — | — | product spec only if unambiguous | 3B |
| `BusinessProduct.technical_requirements` | `TextField()` | No | Yes | `""` | — | — | Yes | — | — | no automatic merge of arbitrary specs | 3B |
| `BusinessProduct.is_active` | `BooleanField(default=True)` | No | No | True | — | — | Yes by archive | active/code | — | map published/active only when exact | 3B |
| `BusinessProduct.created_by` | `ForeignKey(FoundationUser, null=True, related_name="created_business_products")` | Yes; V1 required | Yes rollout | None | — | `PROTECT` | No | — | `ck_part_v1_required` | stable actor only | 3B |
| `BusinessProduct.updated_by` | `ForeignKey(FoundationUser, null=True, related_name="updated_business_products")` | Yes | Yes | None | — | `PROTECT` | Yes | — | — | no invented actor | 3B |
| `BusinessProduct.archived_at` | `DateTimeField(null=True)` | Yes | Yes | None | — | — | archive only | — | — | none | 3B |
| `BusinessProduct.name` | `CharField(max_length=220)` | No | No | — | — | — | Yes | — | `ck_part_v1_required` | unchanged | existing |
| `BusinessProduct.slug` | `SlugField(max_length=240, unique=True)` | No | No | — | — | — | compatibility mutable | unique | existing unique | unchanged | existing |
| `BusinessProduct.sku` | `CharField(max_length=120)` | No | Yes | `""` | — | — | compatibility mutable | — | — | unchanged; not canonical code | existing |
| `BusinessProduct.price` | `DecimalField(max_digits=12, decimal_places=2)` | No | No | 0 | — | — | compatibility only | — | — | unchanged; not quotation authority | existing |
| `BusinessProduct.status` | `CharField(max_length=30)` | No | No | `draft` | legacy | — | compatibility only | existing | — | retained; canonical activity uses `is_active` | existing |
| `BusinessProduct.category_name` | `CharField(max_length=160)` | No | Yes | `""` | — | — | Yes | — | — | unchanged | existing |
| `BusinessProduct.legacy_category_id` | `IntegerField(null=True)` | Yes | Yes | None | — | — | No | existing | — | unchanged | existing |
| `BusinessProduct.short_description` | `TextField()` | No | Yes | `""` | — | — | Yes | — | — | unchanged | existing |
| `BusinessProduct.description` | `TextField()` | No | Yes | `""` | — | — | Yes | — | — | unchanged | existing |
| `BusinessProduct.main_image` | `TextField()` | No | Yes | `""` | — | — | Yes | — | — | unchanged | existing |
| `BusinessProduct.seo_title` | `CharField(max_length=255)` | No | Yes | `""` | — | — | Yes | — | — | unchanged | existing |
| `BusinessProduct.seo_description` | `TextField()` | No | Yes | `""` | — | — | Yes | — | — | unchanged | existing |
| `BusinessProduct.seo_keywords` | `TextField()` | No | Yes | `""` | — | — | Yes | — | — | unchanged | existing |
| `BusinessProduct.sort_order` | `IntegerField()` | No | No | 0 | — | — | Yes | ordering | — | unchanged | existing |
| `BusinessProduct.published_at` | `CharField(max_length=80)` | No | Yes | `""` | — | — | compatibility | — | — | retained text; no core shadow | existing |
| `BusinessProduct.created_at` | `DateTimeField(auto_now_add=True)` | No | No | auto | — | — | No | — | — | unchanged | existing |
| `BusinessProduct.updated_at` | `DateTimeField(auto_now=True)` | No | No | auto | — | — | auto | — | — | unchanged | existing |
| `BusinessMaterial.id` | `BigAutoField(primary_key=True)` | No | No | auto | — | — | No | PK | PK | new | 3B |
| `BusinessMaterial.data_contract` | `CharField(max_length=16, db_index=True)` | No | No | `MVP_V1` | `LEGACY`, `MVP_V1` | — | No | single | `ck_material_v1_required` | new; imports occur outside migrations | 3B |
| `BusinessMaterial.legacy_material_id` | `IntegerField(null=True, unique=True)` | Yes | Yes | None | — | — | No | unique | `uq_material_legacy_id` | future import evidence only | 3B |
| `BusinessMaterial.material_code` | `CharField(max_length=32)` | No | No | — | — | — | No | unique | `uq_material_code` | allocated by sequence | 3B |
| `BusinessMaterial.name` | `CharField(max_length=160)` | No | No | — | — | — | Yes before use | active/name | `ck_material_v1_required` | explicit input/import | 3B |
| `BusinessMaterial.standard` | `CharField(max_length=120)` | No | Yes | `""` | — | — | Yes before use | — | — | explicit source only | 3B |
| `BusinessMaterial.grade` | `CharField(max_length=120)` | No | Yes | `""` | — | — | Yes before use | — | — | explicit source only | 3B |
| `BusinessMaterial.description` | `TextField()` | No | Yes | `""` | — | — | Yes | — | — | explicit source only | 3B |
| `BusinessMaterial.is_active` | `BooleanField(default=True)` | No | No | True | — | — | archive only | active/name | — | new | 3B |
| `BusinessMaterial.created_by` | `ForeignKey(FoundationUser, related_name="created_business_materials")` | No | No | — | — | `PROTECT` | No | — | `ck_material_v1_required` | creator | 3B |
| `BusinessMaterial.updated_by` | `ForeignKey(FoundationUser, null=True, related_name="updated_business_materials")` | Yes | Yes | None | — | `PROTECT` | Yes | — | — | none initially | 3B |
| `BusinessMaterial.created_at` | `DateTimeField(auto_now_add=True)` | No | No | auto | — | — | No | — | — | new | 3B |
| `BusinessMaterial.updated_at` | `DateTimeField(auto_now=True)` | No | No | auto | — | — | auto | — | — | new | 3B |

### 16.3 BusinessNumberSequence

| Field name | Django field type | DB null | Blank | Default | Choices | Relation/on_delete | Mutable | Index | Constraint | Existing source / backfill | Phase |
| --- | --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| `id` | `BigAutoField(primary_key=True)` | No | No | auto | — | — | No | PK | PK | new | 3B |
| `namespace` | `CharField(max_length=16)` | No | No | — | `CUS`, `PART`, `MAT`, `RFQ`, `QT`, `SO` | — | No | composite | `uq_numseq_namespace_period`, `ck_numseq_namespace` | new | 3B |
| `period` | `CharField(max_length=16)` | No | No | — | `GLOBAL` or `YYYY` | — | No | composite | `uq_numseq_namespace_period`, `ck_numseq_period` | new | 3B |
| `last_value` | `PositiveBigIntegerField()` | No | No | 0 | — | — | lock/increment only | — | `ck_numseq_nonnegative` | initialize zero on first allocation | 3B |
| `created_at` | `DateTimeField(auto_now_add=True)` | No | No | auto | — | — | No | — | — | new | 3B |
| `updated_at` | `DateTimeField(auto_now=True)` | No | No | auto | — | — | auto | — | — | new | 3B |

### 16.4 RFQ entities

| Entity.field | Django field type | DB null | Blank | Default | Choices | Relation/on_delete | Mutable | Index | Constraint | Existing source / backfill | Phase |
| --- | --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| `SalesRfq.id` | `BigAutoField(primary_key=True)` | No | No | auto | — | — | No | PK | PK | new | 3B |
| `SalesRfq.data_contract` | `CharField(max_length=16, db_index=True)` | No | No | `MVP_V1` | contract choices | — | No | single | `ck_rfq_v1_required` | new; future imports explicitly LEGACY | 3B |
| `SalesRfq.legacy_quote_request_id` | `IntegerField(null=True, unique=True)` | Yes | Yes | None | — | — | No | unique | `uq_rfq_legacy_quote_id` | future external import only | 3B |
| `SalesRfq.rfq_number` | `CharField(max_length=32)` | No | No | — | — | — | No | unique | `uq_rfq_number` | sequence | 3B |
| `SalesRfq.quotation_family_number` | `CharField(max_length=24, null=True)` | Yes until first revision | Yes | None | — | — | Set once under RFQ lock | unique partial | `uq_rfq_quote_family_nonnull` | QT sequence when R0 is created | 3B schema; value used 3C |
| `SalesRfq.idempotency_key` | `CharField(max_length=64, null=True, blank=True)` | Yes | Yes | None | — | — | No after create | partial unique | `uq_rfq_idempotency_nonnull`, `ck_rfq_idempotency_pair_v1` | future RFQ command input; null allowed before Phase 4 | 3B |
| `SalesRfq.request_hash` | `CharField(max_length=64, null=True, blank=True)` | Yes | Yes | None | SHA-256 hex contract | — | No after create | — | `ck_rfq_idempotency_pair_v1` | future RFQ command input; null allowed before Phase 4 | 3B |
| `SalesRfq.customer` | `ForeignKey(BusinessCustomer, related_name="rfqs")` | No | No | — | — | `PROTECT` | No after submit | single | `ck_rfq_v1_required` | explicit selection | 3B |
| `SalesRfq.status` | `CharField(max_length=24, db_index=True)` | No | No | `DRAFT` | RFQ lifecycle | — | transition only | status/due | `ck_rfq_status` | new | 3B |
| `SalesRfq.project_name` | `CharField(max_length=220)` | No | Yes | `""` | — | — | Draft/info correction | — | — | explicit source | 3B |
| `SalesRfq.notes` | `TextField()` | No | Yes | `""` | — | — | allowed policy | — | — | explicit source | 3B |
| `SalesRfq.quote_due_at` | `DateField()` | No | No | — | — | — | Draft/info correction | status/due | `ck_rfq_due_order` | explicit source | 3B |
| `SalesRfq.required_delivery_date` | `DateField()` | No | No | — | — | — | Draft/info correction | — | `ck_rfq_due_order` | explicit source | 3B |
| `SalesRfq.assigned_to` | `ForeignKey(FoundationUser, null=True, related_name="assigned_rfqs")` | Yes | Yes | None | — | `SET_NULL` | Yes | single | — | explicit actor ID | 3B |
| `SalesRfq.closure_reason` | `TextField()` | No | Yes | `""` | — | — | close only | — | `ck_rfq_close_reason` | none | 3B |
| `SalesRfq.created_by` | `ForeignKey(FoundationUser, related_name="created_rfqs")` | No | No | — | — | `PROTECT` | No | single | `ck_rfq_v1_required` | creator | 3B |
| `SalesRfq.updated_by` | `ForeignKey(FoundationUser, null=True, related_name="updated_rfqs")` | Yes | Yes | None | — | `PROTECT` | Yes | — | — | none initially | 3B |
| `SalesRfq.created_at` | `DateTimeField(auto_now_add=True)` | No | No | auto | — | — | No | — | — | new | 3B |
| `SalesRfq.updated_at` | `DateTimeField(auto_now=True)` | No | No | auto | — | — | auto | — | — | new | 3B |
| `SalesRfqLine.id` | `BigAutoField(primary_key=True)` | No | No | auto | — | — | No | PK | PK | new | 3B |
| `SalesRfqLine.rfq` | `ForeignKey(SalesRfq, related_name="lines")` | No | No | — | — | `CASCADE` | No | composite | `uq_rfqline_parent_number` | explicit | 3B |
| `SalesRfqLine.line_number` | `PositiveIntegerField()` | No | No | — | — | — | No after submit | composite | `uq_rfqline_parent_number`, `ck_rfqline_number_pos` | allocated within RFQ | 3B |
| `SalesRfqLine.part` | `ForeignKey(BusinessProduct, null=True, related_name="rfq_lines")` | Yes | Yes | None | — | `PROTECT` | Draft/info correction | single | — | explicit mapped part only | 3B |
| `SalesRfqLine.material` | `ForeignKey(BusinessMaterial, null=True, related_name="rfq_lines")` | Yes | Yes | None | — | `PROTECT` | Draft/info correction | single | — | explicit material only | 3B |
| `SalesRfqLine.description` | `TextField()` | No | No | — | — | — | Draft/info correction | — | `ck_rfqline_v1_required` | explicit | 3B |
| `SalesRfqLine.quantity` | `DecimalField(max_digits=16, decimal_places=4)` | No | No | — | — | — | Draft/info correction | — | `ck_rfqline_quantity_pos` | Decimal string only | 3B |
| `SalesRfqLine.unit` | `CharField(max_length=8)` | No | No | `PCS` | controlled units | — | Draft/info correction | — | `ck_rfqline_unit` | explicit/default for new only | 3B |
| `SalesRfqLine.required_delivery_date` | `DateField()` | No | No | — | — | — | Draft/info correction | — | — | explicit | 3B |
| `SalesRfqLine.tolerance` | `CharField(max_length=120)` | No | Yes | `""` | — | — | Draft/info correction | — | — | explicit | 3B |
| `SalesRfqLine.technical_notes` | `TextField()` | No | Yes | `""` | — | — | Draft/info correction | — | — | explicit | 3B |
| `SalesRfqLine.drawing_required` | `BooleanField(default=True)` | No | No | True | — | — | Draft/info correction | — | — | explicit decision | 3B |
| `SalesRfqLine.created_at` | `DateTimeField(auto_now_add=True)` | No | No | auto | — | — | No | — | — | new | 3B |
| `SalesRfqLine.updated_at` | `DateTimeField(auto_now=True)` | No | No | auto | — | — | auto | — | — | new | 3B |
| `SalesRfqDocument.id` | `BigAutoField(primary_key=True)` | No | No | auto | — | — | No | PK | PK | new | 3B |
| `SalesRfqDocument.rfq` | `ForeignKey(SalesRfq, related_name="documents")` | No | No | — | — | `CASCADE` | No | rfq/time | — | explicit | 3B |
| `SalesRfqDocument.rfq_line` | `ForeignKey(SalesRfqLine, null=True, related_name="documents")` | Yes | Yes | None | — | `CASCADE` | No | single | service same-RFQ | explicit | 3B |
| `SalesRfqDocument.document_group_id` | `UUIDField()` | No | No | `uuid.uuid4` | — | — | No | composite | `uq_rfqdoc_group_version` | generated | 3B |
| `SalesRfqDocument.version` | `PositiveIntegerField()` | No | No | 1 | — | — | No | composite | `uq_rfqdoc_group_version`, `ck_rfqdoc_version_pos` | max+1 under group lock | 3B |
| `SalesRfqDocument.original_filename` | `CharField(max_length=255)` | No | No | — | — | — | No | — | `ck_rfqdoc_v1_required` | metadata only | 3B |
| `SalesRfqDocument.storage_key` | `CharField(max_length=512, unique=True)` | No | No | generated | — | — | No | unique | `uq_rfqdoc_storage_key` | generated non-public path | 3B |
| `SalesRfqDocument.mime_type` | `CharField(max_length=120)` | No | No | — | allowlist | — | No | — | `ck_rfqdoc_mime` | inspected content | 3B |
| `SalesRfqDocument.size_bytes` | `PositiveBigIntegerField()` | No | No | — | — | — | No | — | `ck_rfqdoc_size_pos` | measured | 3B |
| `SalesRfqDocument.checksum_sha256` | `CharField(max_length=64, db_index=True)` | No | No | — | hex | — | No | single | `ck_rfqdoc_checksum_len` | computed | 3B |
| `SalesRfqDocument.document_revision` | `CharField(max_length=64)` | No | Yes | `""` | — | — | No | — | — | explicit metadata | 3B |
| `SalesRfqDocument.replaces` | `ForeignKey(self, null=True, related_name="replaced_by")` | Yes | Yes | None | — | `PROTECT` | No | — | service same group | prior version | 3B |
| `SalesRfqDocument.uploaded_by` | `ForeignKey(FoundationUser, related_name="uploaded_rfq_documents")` | No | No | — | — | `PROTECT` | No | — | `ck_rfqdoc_v1_required` | uploader | 3B |
| `SalesRfqDocument.uploaded_at` | `DateTimeField(auto_now_add=True)` | No | No | auto | — | — | No | rfq/time | — | new | 3B |
| `SalesTechnicalReview.id` | `BigAutoField(primary_key=True)` | No | No | auto | — | — | No | PK | PK | new | 3B |
| `SalesTechnicalReview.rfq` | `ForeignKey(SalesRfq, related_name="technical_reviews")` | No | No | — | — | `PROTECT` | No | rfq/time | — | explicit | 3B |
| `SalesTechnicalReview.reviewer` | `ForeignKey(FoundationUser, related_name="technical_reviews")` | No | No | — | — | `PROTECT` | No | single | `ck_techreview_v1_required` | actor | 3B |
| `SalesTechnicalReview.decision` | `CharField(max_length=24)` | No | No | — | `STARTED`, `NEEDS_INFORMATION`, `READY_TO_QUOTE`, `DECLINED` | — | No | — | `ck_techreview_decision` | explicit | 3B |
| `SalesTechnicalReview.reason` | `TextField()` | No | Yes | `""` | — | — | No | — | `ck_techreview_reason` | explicit | 3B |
| `SalesTechnicalReview.notes` | `TextField()` | No | Yes | `""` | — | — | No | — | — | explicit | 3B |
| `SalesTechnicalReview.requested_fields` | `JSONField(default=list)` | No | Yes | list | — | — | No | — | service safe keys | explicit | 3B |
| `SalesTechnicalReview.created_at` | `DateTimeField(auto_now_add=True)` | No | No | auto | — | — | No | rfq/time | — | new | 3B |

### 16.5 Quotation entities

| Entity.field | Django field type | DB null | Blank | Default | Choices | Relation/on_delete | Mutable | Index | Constraint | Existing source / backfill | Phase |
| --- | --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| `SalesQuotation.id` | `BigAutoField(primary_key=True)` | No | No | auto | — | — | No | PK | PK | unchanged | existing |
| `SalesQuotation.data_contract` | `CharField(max_length=16, db_index=True)` | No | No | `LEGACY` | contract choices | — | No | single | V1 checks | existing rows LEGACY | 3C |
| `SalesQuotation.opportunity` | `ForeignKey(SalesOpportunity, null=True, related_name="quotations")` | Yes | Yes | None | — | `SET_NULL` | Draft only | existing relation | — | unchanged/deferred | existing |
| `SalesQuotation.customer` | `ForeignKey(BusinessCustomer, null=True, related_name="sales_quotations")` | Yes | Yes | None | — | `SET_NULL` | compatibility | existing relation | — | unchanged; V1 derives RFQ customer | existing |
| `SalesQuotation.rfq` | `ForeignKey(SalesRfq, null=True, related_name="quotations")` | Yes; V1 required | Yes rollout | None | — | `PROTECT` | No | composite | `uq_quote_rfq_revision`, `ck_quote_v1_required` | only explicit RFQ evidence | 3C |
| `SalesQuotation.quotation_number` | `CharField(max_length=80, unique=True)` | No | No | — | — | — | No | unique | existing `unique`, `ck_quote_v1_required` | preserve existing; V1 family + Rn | existing/3C |
| `SalesQuotation.version` | `PositiveIntegerField()` | No | No | 1 | legacy | — | compatibility until cutoff | — | — | unchanged; no inferred revision | existing |
| `SalesQuotation.revision` | `PositiveIntegerField(null=True)` | Yes; V1 required | Yes rollout | None | zero-based | — | No | composite | `uq_quote_rfq_revision`, `ck_quote_v1_required` | only with explicit RFQ/revision evidence | 3C |
| `SalesQuotation.status` | `CharField(max_length=40)` | No | No | `draft` | legacy statuses | — | compatibility only | existing status index | — | unchanged | existing |
| `SalesQuotation.workflow_status` | `CharField(max_length=24, null=True, db_index=True)` | Yes; V1 required | Yes rollout | None | quotation lifecycle | — | transition only | status/validity | `ck_quote_workflow_status`, `uq_quote_effective_rfq` | no auto-map ambiguous legacy | 3C |
| `SalesQuotation.approval_status` | `CharField(max_length=40)` | No | No | `pending` | legacy/free-form | — | compatibility only | existing index | — | unchanged | existing |
| `SalesQuotation.currency` | `CharField(max_length=3, null=True)` | Yes; V1 required | Yes rollout | None | `VND`, `USD` | — | No after submit | — | `ck_quote_currency` | explicit only | 3C |
| `SalesQuotation.valid_from` | `DateField(null=True)` | Yes; V1 required | Yes rollout | None | — | — | Draft only | validity index | `ck_quote_validity` | parse only exact source evidence | 3C |
| `SalesQuotation.valid_until` | `DateField(null=True)` | Yes; V1 required | Yes rollout | None | — | — | Draft only | validity index | `ck_quote_validity` | parse only exact source evidence | 3C |
| `SalesQuotation.subtotal` | `DecimalField(max_digits=20, decimal_places=4)` | No | No | 0 | — | — | service before submit | — | `ck_quote_money_nonneg`, `ck_quote_total_equation` | widen existing 14,2 without value invention | 3C |
| `SalesQuotation.discount_total` | `DecimalField(max_digits=20, decimal_places=4)` | No | No | 0 | — | — | service before submit | — | `ck_quote_discount_bound`, `ck_quote_total_equation` | widen existing | 3C |
| `SalesQuotation.tax_amount` | `DecimalField(max_digits=20, decimal_places=4)` | No | No | 0 | — | — | service before submit | — | `ck_quote_money_nonneg`, `ck_quote_total_equation` | new zero only for new V1; legacy remains contract LEGACY | 3C |
| `SalesQuotation.total` | `DecimalField(max_digits=20, decimal_places=4)` | No | No | 0 | — | — | calculated only | — | `ck_quote_money_nonneg`, `ck_quote_total_equation` | widen existing; validate, never silently repair | 3C |
| `SalesQuotation.terms` | `TextField()` | No | Yes | `""` | — | — | Draft only | — | — | explicit | 3C |
| `SalesQuotation.customer_snapshot` | `JSONField(default=dict)` | No | Yes rollout | dict | safe schema | — | No after submit | — | `ck_quote_v1_required` service schema | generated from RFQ customer | 3C |
| `SalesQuotation.rfq_snapshot` | `JSONField(default=dict)` | No | Yes rollout | dict | safe schema | — | No after submit | — | `ck_quote_v1_required` service schema | generated from RFQ | 3C |
| `SalesQuotation.sent_at` | `DateTimeField(null=True)` | Yes | Yes | None | — | — | send only | — | service status invariant | no fake backfill | 3C |
| `SalesQuotation.sent_to` | `CharField(max_length=254)` | No | Yes | `""` | — | — | send only | — | service status invariant | explicit evidence | 3C |
| `SalesQuotation.sent_evidence` | `TextField()` | No | Yes | `""` | — | — | send only | — | service status invariant | explicit evidence | 3C |
| `SalesQuotation.idempotency_key` | `CharField(max_length=64, null=True)` | Yes; V1 create required | Yes rollout | None | — | — | No | unique partial | `uq_quote_idempotency_nonnull` | new command input | 3C |
| `SalesQuotation.request_hash` | `CharField(max_length=64)` | No | Yes rollout | `""` | sha256 | — | No | — | service key/hash invariant | new command | 3C |
| `SalesQuotation.created_by` | `ForeignKey(FoundationUser, null=True, related_name="sales_quotations")` | Yes; V1 required | Yes rollout | None | — | `SET_NULL` existing; target `PROTECT` deferred because legacy | No | creator index | `ck_quote_v1_required` | existing stable FK | existing/3C |
| `SalesQuotation.updated_by` | `ForeignKey(FoundationUser, null=True, related_name="updated_sales_quotations")` | Yes | Yes | None | — | `PROTECT` | Yes before submit | — | — | no invented actor | 3C |
| `SalesQuotation.created_at` | `DateTimeField(auto_now_add=True)` | No | No | auto | — | — | No | ordering | — | unchanged | existing |
| `SalesQuotation.updated_at` | `DateTimeField(auto_now=True)` | No | No | auto | — | — | auto | — | — | unchanged | existing |
| `SalesQuotationLine.id` | `BigAutoField(primary_key=True)` | No | No | auto | — | — | No | PK | PK | unchanged | existing |
| `SalesQuotationLine.data_contract` | `CharField(max_length=16, db_index=True)` | No | No | `LEGACY` | contract choices | — | No | single | V1 line checks | all existing lines LEGACY; V1 service sets MVP_V1 | 3C |
| `SalesQuotationLine.quotation` | `ForeignKey(SalesQuotation, related_name="lines")` | No | No | — | — | `CASCADE` | No | composite | `uq_quoteline_parent_number` | unchanged | existing |
| `SalesQuotationLine.line_number` | `PositiveIntegerField(null=True)` | Yes; V1 required | Yes rollout | None | — | — | No after submit | composite | `uq_quoteline_parent_number`, `ck_quoteline_number_pos` | deterministic current id order only after review | 3C |
| `SalesQuotationLine.source_rfq_line` | `ForeignKey(SalesRfqLine, null=True, related_name="quotation_lines")` | Yes; V1 required | Yes rollout | None | — | `PROTECT` | No | single | service same-RFQ | explicit source only | 3C |
| `SalesQuotationLine.product` | `ForeignKey(BusinessProduct, null=True, related_name="sales_quote_lines")` | Yes | Yes | None | — | `SET_NULL` | compatibility | existing relation | — | unchanged | existing |
| `SalesQuotationLine.description` | `TextField()` | No | Yes compatibility; V1 nonblank | `""` | — | — | Draft only | — | `ck_quoteline_v1_required` | existing | existing/3C |
| `SalesQuotationLine.part_code_snapshot` | `CharField(max_length=32)` | No | Yes rollout | `""` | — | — | No after submit | — | `ck_quoteline_v1_required` | source RFQ/part snapshot | 3C |
| `SalesQuotationLine.material_snapshot` | `CharField(max_length=240)` | No | Yes rollout | `""` | — | — | No after submit | — | — | source RFQ line | 3C |
| `SalesQuotationLine.unit` | `CharField(max_length=8)` | No | Yes rollout | `""` | units | — | Draft only | — | `ck_quoteline_unit` | explicit source | 3C |
| `SalesQuotationLine.quantity` | `DecimalField(max_digits=16, decimal_places=4)` | No | No | 1 | — | — | Draft only | — | `ck_quoteline_quantity_pos` | widen existing 12,2 | 3C |
| `SalesQuotationLine.unit_price` | `DecimalField(max_digits=20, decimal_places=4)` | No | No | 0 | — | — | Draft only | — | `ck_quoteline_price_pos` | widen existing; zero blocks V1 | 3C |
| `SalesQuotationLine.discount` | `DecimalField(max_digits=20, decimal_places=4)` | No | No | 0 | — | — | Draft only | — | `ck_quoteline_money_nonneg` | widen existing | 3C |
| `SalesQuotationLine.line_subtotal` | `DecimalField(max_digits=20, decimal_places=4)` | No | No | 0 | — | — | calculated only | — | `ck_quoteline_money_nonneg` | backend quantized | 3C |
| `SalesQuotationLine.line_total` | `DecimalField(max_digits=20, decimal_places=4)` | No | No | 0 | — | — | calculated only | — | `ck_quoteline_money_nonneg` | widen existing; validate | 3C |
| `SalesQuotationLine.created_at` | `DateTimeField(auto_now_add=True, null=True)` | Yes rollout | No | auto | — | — | No | — | V1 required service | existing rows get migration time only if approved; else null | 3C |
| `SalesQuotationApprovalDecision.id` | `BigAutoField(primary_key=True)` | No | No | auto | — | — | No | PK | PK | new | 3C |
| `SalesQuotationApprovalDecision.quotation` | `ForeignKey(SalesQuotation, related_name="approval_decisions")` | No | No | — | — | `PROTECT` | No | named unique | `uq_quote_approval_decision` | no legacy fabrication | 3C |
| `SalesQuotationApprovalDecision.reviewer` | `ForeignKey(FoundationUser, related_name="quotation_approval_decisions")` | No | No | — | — | `PROTECT` | No | single | service maker-checker | actor | 3C |
| `SalesQuotationApprovalDecision.decision` | `CharField(max_length=16)` | No | No | — | `APPROVED`, `REJECTED` | — | No | — | `ck_quoteapproval_decision` | explicit | 3C |
| `SalesQuotationApprovalDecision.reason` | `TextField()` | No | Yes | `""` | — | — | No | — | `ck_quoteapproval_reason` | explicit for rejection | 3C |
| `SalesQuotationApprovalDecision.notes` | `TextField()` | No | Yes | `""` | — | — | No | — | — | explicit | 3C |
| `SalesQuotationApprovalDecision.decided_at` | `DateTimeField()` | No | No | `timezone.now` | — | — | No | — | — | command time | 3C |
| `SalesQuotationCustomerDecision.id` | `BigAutoField(primary_key=True)` | No | No | auto | — | — | No | PK | PK | new | 3C |
| `SalesQuotationCustomerDecision.quotation` | `ForeignKey(SalesQuotation, related_name="customer_decisions")` | No | No | — | — | `PROTECT` | No | named unique | `uq_quote_customer_decision` | no legacy fabrication | 3C |
| `SalesQuotationCustomerDecision.recorded_by` | `ForeignKey(FoundationUser, related_name="recorded_customer_decisions")` | No | No | — | — | `PROTECT` | No | single | — | actor | 3C |
| `SalesQuotationCustomerDecision.decision` | `CharField(max_length=16)` | No | No | — | `ACCEPTED`, `DECLINED` | — | No | — | `ck_quotecustomer_decision` | explicit | 3C |
| `SalesQuotationCustomerDecision.contact_snapshot` | `CharField(max_length=254)` | No | No | — | — | — | No | — | `ck_quotecustomer_required` | evidence | 3C |
| `SalesQuotationCustomerDecision.evidence` | `TextField()` | No | No | — | — | — | No | — | `ck_quotecustomer_required` | evidence | 3C |
| `SalesQuotationCustomerDecision.reason` | `TextField()` | No | Yes | `""` | — | — | No | — | `ck_quotecustomer_reason` | required for decline | 3C |
| `SalesQuotationCustomerDecision.decided_at` | `DateTimeField()` | No | No | `timezone.now` | — | — | No | — | — | customer decision time | 3C |

### 16.6 Order, progress, and audit entities

| Entity.field | Django field type | DB null | Blank | Default | Choices | Relation/on_delete | Mutable | Index | Constraint | Existing source / backfill | Phase |
| --- | --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| `TransactionOrder.id` | `BigAutoField(primary_key=True)` | No | No | auto | — | — | No | PK | PK | unchanged | existing |
| `TransactionOrder.data_contract` | `CharField(max_length=16, db_index=True)` | No | No | `LEGACY` | contract choices | — | No | single | V1 checks | existing LEGACY | 3D |
| `TransactionOrder.legacy_quote_request_id` | `IntegerField(null=True, unique=True)` | Yes | Yes | None | — | — | No | unique | existing unique | unchanged; not quotation evidence | existing |
| `TransactionOrder.order_number` | `CharField(max_length=80, unique=True)` | No | No | — | — | — | No | unique | existing unique, `ck_order_v1_required` | preserve old; V1 uses SO sequence | existing/3D |
| `TransactionOrder.source_quotation` | `ForeignKey(SalesQuotation, null=True, related_name="sales_orders")` | Yes; V1 required | Yes rollout | None | — | `PROTECT` | No | named partial unique | `uq_order_source_quote`, `ck_order_v1_required` | only accepted V1 conversion | 3D |
| `TransactionOrder.source_rfq` | `ForeignKey(SalesRfq, null=True, related_name="sales_orders")` | Yes; V1 required | Yes rollout | None | — | `PROTECT` | No | single | `ck_order_v1_required` | derive source quotation | 3D |
| `TransactionOrder.customer` | `ForeignKey(BusinessCustomer, related_name="orders")` | No | No | — | — | `PROTECT` | No after conversion | existing relation | — | unchanged | existing |
| `TransactionOrder.project_name` | `CharField(max_length=220)` | No | Yes | `""` | — | — | compatibility | — | — | unchanged | existing |
| `TransactionOrder.message` | `TextField()` | No | Yes | `""` | — | — | compatibility | — | — | unchanged | existing |
| `TransactionOrder.status` | `CharField(max_length=40)` | No | No | `new` | legacy | — | compatibility only | existing index | — | unchanged | existing |
| `TransactionOrder.workflow_status` | `CharField(max_length=16, null=True, db_index=True)` | Yes; V1 required | Yes rollout | None | order lifecycle | — | transition only | status/date | `ck_order_workflow_status` | no auto-classification | 3D |
| `TransactionOrder.assigned_to` | `ForeignKey(FoundationUser, null=True, related_name="assigned_orders")` | Yes | Yes | None | — | `SET_NULL` | Yes | existing | — | unchanged | existing |
| `TransactionOrder.internal_note` | `TextField()` | No | Yes | `""` | — | — | controlled notes | — | — | unchanged | existing |
| `TransactionOrder.currency` | `CharField(max_length=3, null=True)` | Yes; V1 required | Yes rollout | None | VND, USD | — | No | — | `ck_order_currency` | source quotation | 3D |
| `TransactionOrder.subtotal` | `DecimalField(max_digits=20, decimal_places=4)` | No | No | 0 | — | — | No | — | `ck_order_money_nonneg`, `ck_order_total_equation` | source quotation snapshot | 3D |
| `TransactionOrder.discount_total` | `DecimalField(max_digits=20, decimal_places=4)` | No | No | 0 | — | — | No | — | `ck_order_discount_bound`, `ck_order_total_equation` | source quotation snapshot | 3D |
| `TransactionOrder.tax_amount` | `DecimalField(max_digits=20, decimal_places=4)` | No | No | 0 | — | — | No | — | `ck_order_money_nonneg`, `ck_order_total_equation` | source quotation snapshot | 3D |
| `TransactionOrder.total_amount` | `DecimalField(max_digits=20, decimal_places=4)` | No | No | 0 | — | — | No | — | `ck_order_money_nonneg`, `ck_order_total_equation` | widen existing; validate only | 3D |
| `TransactionOrder.customer_snapshot` | `JSONField(default=dict)` | No | Yes rollout | dict | safe schema | — | No | — | service required for V1 | conversion snapshot | 3D |
| `TransactionOrder.quotation_snapshot` | `JSONField(default=dict)` | No | Yes rollout | dict | safe schema | — | No | — | service required for V1 | conversion snapshot | 3D |
| `TransactionOrder.ordered_at` | `DateTimeField(null=True)` | Yes; V1 required | Yes rollout | None | — | — | No | status/date | `ck_order_v1_required` | conversion time only | 3D |
| `TransactionOrder.expected_delivery_date` | `DateField(null=True)` | Yes; V1 required | Yes rollout | None | — | — | controlled before work | status/date | service ordered-date comparison | source quotation/RFQ | 3D |
| `TransactionOrder.progress_percent` | `PositiveSmallIntegerField()` | No | No | 0 | 0–100 | — | progress command | — | `ck_order_progress_range` | new V1 only | 3D |
| `TransactionOrder.hold_reason` | `TextField()` | No | Yes | `""` | — | — | hold/resume command | — | `ck_order_hold_reason` | none | 3D |
| `TransactionOrder.cancel_reason` | `TextField()` | No | Yes | `""` | — | — | cancel command | — | `ck_order_cancel_reason` | none | 3D |
| `TransactionOrder.quoted_at` | `CharField(max_length=80)` | No | Yes | `""` | legacy text | — | compatibility only | — | — | unchanged | existing |
| `TransactionOrder.source_quotation_sent_at` | `DateTimeField(null=True)` | Yes | Yes | None | — | — | No | — | — | exact parse/evidence only | 3D |
| `TransactionOrder.completed_at` | `CharField(max_length=80)` | No | Yes | `""` | legacy text | — | compatibility only | — | — | unchanged | existing |
| `TransactionOrder.completed_at_v1` | `DateTimeField(null=True)` | Yes | Yes | None | — | — | completion only | — | service status invariant | exact parse/evidence only | 3D |
| `TransactionOrder.idempotency_key` | `CharField(max_length=64, null=True)` | Yes; V1 required | Yes rollout | None | — | — | No | unique partial | `uq_order_idempotency_nonnull` | conversion command | 3D |
| `TransactionOrder.request_hash` | `CharField(max_length=64)` | No | Yes rollout | `""` | sha256 | — | No | — | service invariant | conversion command | 3D |
| `TransactionOrder.created_by` | `ForeignKey(FoundationUser, null=True, related_name="created_transaction_orders")` | Yes; V1 required | Yes rollout | None | — | `PROTECT` | No | — | `ck_order_v1_required` | conversion actor | 3D |
| `TransactionOrder.updated_by` | `ForeignKey(FoundationUser, null=True, related_name="updated_transaction_orders")` | Yes | Yes | None | — | `PROTECT` | progress only | — | — | no invented actor | 3D |
| `TransactionOrder.created_at` | `DateTimeField(auto_now_add=True)` | No | No | auto | — | — | No | ordering | — | unchanged | existing |
| `TransactionOrder.updated_at` | `DateTimeField(auto_now=True)` | No | No | auto | — | — | auto | — | — | unchanged | existing |
| `TransactionOrderItem.id` | `BigAutoField(primary_key=True)` | No | No | auto | — | — | No | PK | PK | unchanged | existing |
| `TransactionOrderItem.data_contract` | `CharField(max_length=16, db_index=True)` | No | No | `LEGACY` | contract choices | — | No | single | V1 line checks | all existing lines LEGACY; conversion sets MVP_V1 | 3D |
| `TransactionOrderItem.legacy_quote_item_id` | `IntegerField(null=True, unique=True)` | Yes | Yes | None | — | — | No | unique | existing unique | unchanged | existing |
| `TransactionOrderItem.order` | `ForeignKey(TransactionOrder, related_name="items")` | No | No | — | — | `CASCADE` | No | composite | `uq_orderline_parent_number` | unchanged | existing |
| `TransactionOrderItem.line_number` | `PositiveIntegerField(null=True)` | Yes; V1 required | Yes rollout | None | — | — | No | composite | `uq_orderline_parent_number`, `ck_orderline_number_pos` | explicit conversion order | 3D |
| `TransactionOrderItem.source_quotation_line` | `ForeignKey(SalesQuotationLine, null=True, related_name="order_lines")` | Yes; V1 required | Yes rollout | None | — | `PROTECT` | No | named partial unique | `uq_orderline_source_line` | source conversion | 3D |
| `TransactionOrderItem.product` | `ForeignKey(BusinessProduct, null=True, related_name="order_items")` | Yes | Yes | None | — | `PROTECT` | compatibility | existing relation | — | unchanged | existing |
| `TransactionOrderItem.inventory_item` | `ForeignKey(InventoryItem, null=True, related_name="order_items")` | Yes | Yes | None | — | `PROTECT` | deferred | existing relation | — | unchanged; no V1 reservation | existing |
| `TransactionOrderItem.drawing_code` | `CharField(max_length=160)` | No | Yes | `""` | — | — | compatibility | — | — | unchanged/snapshot input | existing |
| `TransactionOrderItem.material_name` | `CharField(max_length=160)` | No | Yes | `""` | — | — | compatibility | — | — | unchanged | existing |
| `TransactionOrderItem.description_snapshot` | `TextField()` | No | Yes rollout | `""` | — | — | No | — | `ck_orderline_v1_required` | quotation line | 3D |
| `TransactionOrderItem.part_code_snapshot` | `CharField(max_length=32)` | No | Yes rollout | `""` | — | — | No | — | `ck_orderline_v1_required` | quotation line | 3D |
| `TransactionOrderItem.material_snapshot` | `CharField(max_length=240)` | No | Yes rollout | `""` | — | — | No | — | — | quotation line | 3D |
| `TransactionOrderItem.quantity` | `DecimalField(max_digits=16, decimal_places=4)` | No | No | 1 | — | — | No | — | `ck_orderline_quantity_pos` | convert current integer exactly | 3D |
| `TransactionOrderItem.unit` | `CharField(max_length=8)` | No | Yes rollout | `""` | units | — | No | — | `ck_orderline_unit` | quotation snapshot | 3D |
| `TransactionOrderItem.tolerance` | `CharField(max_length=120)` | No | Yes | `""` | — | — | No | — | — | unchanged/snapshot | existing |
| `TransactionOrderItem.note` | `TextField()` | No | Yes | `""` | — | — | controlled internal | — | — | unchanged | existing |
| `TransactionOrderItem.unit_price` | `DecimalField(max_digits=20, decimal_places=4)` | No | No | 0 | — | — | No | — | `ck_orderline_money_nonneg` | widen existing | 3D |
| `TransactionOrderItem.line_total` | `DecimalField(max_digits=20, decimal_places=4)` | No | No | 0 | — | — | No | — | `ck_orderline_money_nonneg` | widen existing/validate | 3D |
| `OrderProgressEvent.id` | `BigAutoField(primary_key=True)` | No | No | auto | — | — | No | PK | PK | new | 3D |
| `OrderProgressEvent.order` | `ForeignKey(TransactionOrder, related_name="progress_events")` | No | No | — | — | `PROTECT` | No | order/time | — | explicit | 3D |
| `OrderProgressEvent.from_status` | `CharField(max_length=16)` | No | Yes only initial | `""` | order statuses | — | No | — | `ck_progress_statuses` | current locked state | 3D |
| `OrderProgressEvent.to_status` | `CharField(max_length=16)` | No | No | — | order statuses | — | No | status/time | `ck_progress_statuses` | command target | 3D |
| `OrderProgressEvent.progress_percent` | `PositiveSmallIntegerField()` | No | No | — | 0–100 | — | No | — | `ck_progress_percent_range` | command | 3D |
| `OrderProgressEvent.milestone_note` | `CharField(max_length=240)` | No | Yes | `""` | — | — | No | — | — | command | 3D |
| `OrderProgressEvent.reason` | `TextField()` | No | Yes conditional | `""` | — | — | No | — | `ck_progress_reason` | required hold/cancel | 3D |
| `OrderProgressEvent.actor` | `ForeignKey(FoundationUser, related_name="order_progress_events")` | No | No | — | — | `PROTECT` | No | actor/time | — | command actor | 3D |
| `OrderProgressEvent.created_at` | `DateTimeField(auto_now_add=True)` | No | No | auto | — | — | No | order/time | — | new | 3D |
| `AuditEvent.id` | `BigAutoField(primary_key=True)` | No | No | auto | — | — | No | PK | PK | new | 3D |
| `AuditEvent.actor_ref` | `CharField(max_length=80)` | No | No | — | stable user ID or `system` | — | No | actor/time | `ck_audit_actor_ref` | explicit | 3D |
| `AuditEvent.actor_display` | `CharField(max_length=160)` | No | No | — | — | — | No | — | `ck_audit_actor_ref` | snapshot | 3D |
| `AuditEvent.actor_user` | `ForeignKey(FoundationUser, null=True, related_name="audit_events")` | Yes for system | Yes | None | — | `PROTECT` | No | actor/time | service actor/ref match | stable actor | 3D |
| `AuditEvent.action` | `CharField(max_length=120)` | No | No | — | approved action catalog | — | No | action/time | `ck_audit_required` | command | 3D |
| `AuditEvent.entity_type` | `CharField(max_length=80)` | No | No | — | controlled types | — | No | entity/time | `ck_audit_required` | command | 3D |
| `AuditEvent.entity_id` | `CharField(max_length=80)` | No | No | — | — | — | No | entity/time | `ck_audit_required` | string PK | 3D |
| `AuditEvent.old_status` | `CharField(max_length=24)` | No | Yes | `""` | domain status | — | No | — | — | command | 3D |
| `AuditEvent.new_status` | `CharField(max_length=24)` | No | Yes | `""` | domain status | — | No | — | — | command | 3D |
| `AuditEvent.reason` | `TextField()` | No | Yes conditional | `""` | — | — | No | — | service action requirement | command | 3D |
| `AuditEvent.metadata` | `JSONField(default=dict)` | No | Yes | dict | safe schema | — | No | — | service secret/PII filter | command | 3D |
| `AuditEvent.correlation_id` | `UUIDField(db_index=True)` | No | No | `uuid.uuid4` | — | — | No | single | — | request/job context | 3D |
| `AuditEvent.created_at` | `DateTimeField(auto_now_add=True)` | No | No | auto | — | — | No | entity/action/actor time | — | new | 3D |

### 16.7 Foundation RBAC fields and actions

No RBAC column is added. Existing exact fields remain: Permission `id`,
`code CharField(120, unique)`, `module CharField(80)`, `action CharField(40)`,
`description TextField(blank)`; Role `id`, `name CharField(50, unique)`,
`description`, `created_at`; RolePermission `id`, role/permission CASCADE with
unique `(role, permission)`. Phase 3B defines schema-needed actions; Phase 3D
seeds the complete matrix and assignments remain Owner-reviewed.

| Module | Exact actions added | Phase |
| --- | --- | --- |
| `customer` | `view`, `create`, `change`, `archive` | 3B definitions; 3D grants |
| `part` | `view`, `manage`, `archive` | 3B definitions; 3D grants |
| `material` | `view`, `manage`, `archive` | 3B definitions; 3D grants |
| `rfq` | `view`, `create`, `change`, `archive`, `submit`, `review`, `document_upload`, `document_download` | 3B definitions; 3D grants |
| `quotation` | `view`, `create_revision`, `change`, `submit`, `approve`, `reject`, `send`, `record_customer_decision`, `convert` | 3C definitions; 3D grants |
| `order` | `view`, `progress`, `hold`, `resume`, `complete`, `cancel` | 3D |
| `audit` | `view` | 3D |
| `user` | `view`, `manage` | 3D |

## 17. Constraint catalog

`V1` below means an implication/conditional constraint for
`data_contract=MVP_V1`. PostgreSQL is production authority. SQLite supports many
checks and partial indexes in the tested Django version, but service validation
is retained and concurrency parity is never claimed.

| Constraint name | Table | Type | Expression/fields | Applies to | PostgreSQL | SQLite | Phase |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `uq_numseq_namespace_period` | `business_number_sequences` | Unique | `(namespace, period)` | all | native | native | 3B |
| `ck_numseq_namespace` | same | Check | namespace in allowed set | all | native | native | 3B |
| `ck_numseq_period` | same | Check | GLOBAL or four-digit year consistent with namespace | all | native regex/check | service fallback for regex | 3B |
| `ck_numseq_nonnegative` | same | Check | `last_value >= 0` | all | native | native | 3B |
| `uq_customer_code_nonnull` | `business_customers` | Partial unique | `customer_code`, when non-null | all issued codes | authority | supported; verify | 3B |
| `ck_customer_v1_status` | same | Check | not V1 or status in ACTIVE/INACTIVE | V1 | native | native | 3B |
| `ck_customer_v1_required` | same | Check | not V1 or nonblank code/company and creator non-null | V1 | native | native | 3B |
| `ck_customer_v1_contact` | same | Check | not V1/ACTIVE or nonblank email or phone | active V1 | native | native | 3B |
| `uq_part_code_nonnull` | `business_products` | Partial unique | `part_code`, when non-null | all issued codes | authority | supported; verify | 3B |
| `ck_part_v1_required` | same | Check | not V1 or code/revision/unit/name/creator present | V1 | native | native | 3B |
| `ck_part_v1_unit` | same | Check | not V1 or unit in PCS/KG/M/MM | V1 | native | native | 3B |
| `uq_material_code` | `business_materials` | Unique | `material_code` | all | native | native | 3B |
| `uq_material_legacy_id` | same | Unique | nullable `legacy_material_id` | non-null imported IDs | native | native | 3B |
| `ck_material_v1_required` | same | Check | not V1 or nonblank code/name and creator present | V1 | native | native | 3B |
| `uq_rfq_number` | `sales_rfqs` | Unique | `rfq_number` | all | native | native | 3B |
| `uq_rfq_quote_family_nonnull` | same | Partial unique | `quotation_family_number` when non-null | issued families | authority | supported; verify | 3B/3C |
| `uq_rfq_idempotency_nonnull` | same | Partial unique | `idempotency_key` when non-null | all keyed RFQs | authority | supported; verify | 3B |
| `ck_rfq_idempotency_pair_v1` | same | Check | not V1 or key/hash are both null or both non-null | V1 | native | native | 3B |
| `uq_rfq_legacy_quote_id` | same | Unique | nullable legacy ID | imports | native | native | 3B |
| `ck_rfq_status` | same | Check | status in RFQ lifecycle set | all | native | native | 3B |
| `ck_rfq_v1_required` | same | Check | V1 number/customer/dates/creator present | V1 | native | native | 3B |
| `ck_rfq_due_order` | same | Check | `quote_due_at <= required_delivery_date` | all | native | native | 3B |
| `ck_rfq_close_reason` | same | Check | CLOSED implies nonblank closure reason | all | native | native | 3B |
| `uq_rfqline_parent_number` | `sales_rfq_lines` | Unique | `(rfq_id, line_number)` | all | native | native | 3B |
| `ck_rfqline_number_pos` | same | Check | `line_number > 0` | all | native | native | 3B |
| `ck_rfqline_quantity_pos` | same | Check | `quantity > 0` | all | native | native | 3B |
| `ck_rfqline_unit` | same | Check | unit in controlled set | all | native | native | 3B |
| `ck_rfqline_v1_required` | same | Check | nonblank description and required date | all new rows | native | native | 3B |
| `uq_rfqdoc_group_version` | `sales_rfq_documents` | Unique | `(document_group_id, version)` | all | native | native | 3B |
| `uq_rfqdoc_storage_key` | same | Unique | `storage_key` | all | native | native | 3B |
| `ck_rfqdoc_version_pos` | same | Check | `version > 0` | all | native | native | 3B |
| `ck_rfqdoc_size_pos` | same | Check | `size_bytes > 0` and configured max | all | native | native | 3B |
| `ck_rfqdoc_checksum_len` | same | Check | length checksum = 64 | all | native | length supported | 3B |
| `ck_rfqdoc_mime` | same | Check | MIME in approved allowlist | all | native | native | 3B |
| `ck_rfqdoc_v1_required` | same | Check | filename/storage/checksum/uploader nonblank | all new rows | native | native | 3B |
| `ck_techreview_decision` | `sales_technical_reviews` | Check | decision in exact set | all | native | native | 3B |
| `ck_techreview_reason` | same | Check | NEEDS_INFORMATION/DECLINED implies nonblank reason | all | native | native | 3B |
| `ck_techreview_v1_required` | same | Check | reviewer and RFQ present | all new rows | native | native | 3B |
| `uq_quote_rfq_revision` | `sales_platform_quotations` | Partial unique | `(rfq_id, revision)` when both non-null | sourced revisions | authority | supported; verify | 3C |
| `uq_quote_effective_rfq` | same | Partial unique | `rfq_id` when V1 and workflow in APPROVED/SENT/ACCEPTED | V1 effective | authority | partial index supported; no locking parity | 3C |
| `uq_quote_idempotency_nonnull` | same | Partial unique | `idempotency_key` when non-null | V1 commands | authority | supported | 3C |
| `ck_quote_workflow_status` | same | Check | not V1 or workflow in exact set | V1 | native | native | 3C |
| `ck_quote_v1_required` | same | Check | V1 RFQ/revision/currency/dates/creator/snapshots present | V1 | native where scalar; JSON schema in service | scalar native | 3C |
| `ck_quote_currency` | same | Check | not V1 or currency in VND/USD | V1 | native | native | 3C |
| `ck_quote_validity` | same | Check | not V1 or `valid_until >= valid_from` | V1 | native | native | 3C |
| `ck_quote_money_nonneg` | same | Check | V1 monetary columns >= 0 | V1 | native | native | 3C |
| `ck_quote_discount_bound` | same | Check | not V1 or discount_total <= subtotal | V1 | native | native | 3C |
| `ck_quote_total_equation` | same | Check | not V1 or total = subtotal - discount_total + tax_amount | V1 | native exact Decimal | native exact Decimal | 3C |
| `uq_quoteline_parent_number` | `sales_platform_quotation_lines` | Partial unique | `(quotation_id, line_number)` when line_number non-null | numbered lines | authority | supported | 3C |
| `ck_quoteline_number_pos` | same | Check | null or line_number > 0 | all | native | native | 3C |
| `ck_quoteline_quantity_pos` | same | Check | not V1 or quantity > 0 | V1 | native | native | 3C |
| `ck_quoteline_price_pos` | same | Check | not V1 or unit_price > 0 | V1 | native | native | 3C |
| `ck_quoteline_money_nonneg` | same | Check | not V1 or discount/line_subtotal/line_total >= 0 | V1 | native | native | 3C |
| `ck_quoteline_unit` | same | Check | blank legacy or controlled unit | all | native | native | 3C |
| `ck_quoteline_v1_required` | same | Check + service | V1 line requires source/line/snapshots; service verifies same RFQ | V1 | scalar check; cross-row service | same | 3C |
| `uq_quote_approval_decision` | `sales_quotation_approval_decisions` | Unique | `quotation_id` OneToOne | all | native | native | 3C |
| `ck_quoteapproval_decision` | same | Check | APPROVED/REJECTED | all | native | native | 3C |
| `ck_quoteapproval_reason` | same | Check | REJECTED implies nonblank reason | all | native | native | 3C |
| `uq_quote_customer_decision` | `sales_quotation_customer_decisions` | Unique | `quotation_id` OneToOne | all | native | native | 3C |
| `ck_quotecustomer_decision` | same | Check | ACCEPTED/DECLINED | all | native | native | 3C |
| `ck_quotecustomer_required` | same | Check | nonblank contact/evidence | all | native | native | 3C |
| `ck_quotecustomer_reason` | same | Check | DECLINED implies nonblank reason | all | native | native | 3C |
| `uq_order_source_quote` | `transaction_orders` | Partial unique | `source_quotation_id` when non-null | sourced orders | authority | supported | 3D |
| `uq_order_idempotency_nonnull` | same | Partial unique | `idempotency_key` when non-null | V1 commands | authority | supported | 3D |
| `ck_order_workflow_status` | same | Check | not V1 or workflow in exact set | V1 | native | native | 3D |
| `ck_order_v1_required` | same | Check | V1 source/RFQ/order dates/currency/creator present | V1 | native scalar | native scalar | 3D |
| `ck_order_currency` | same | Check | not V1 or VND/USD | V1 | native | native | 3D |
| `ck_order_money_nonneg` | same | Check | V1 monetary columns >= 0 | V1 | native | native | 3D |
| `ck_order_discount_bound` | same | Check | not V1 or discount <= subtotal | V1 | native | native | 3D |
| `ck_order_total_equation` | same | Check | not V1 or total = subtotal - discount + tax | V1 | native | native | 3D |
| `ck_order_progress_range` | same | Check | progress_percent between 0 and 100 | all | native | native | 3D |
| `ck_order_hold_reason` | same | Check | V1 ON_HOLD implies nonblank hold_reason | V1 | native | native | 3D |
| `ck_order_cancel_reason` | same | Check | V1 CANCELLED implies nonblank cancel_reason | V1 | native | native | 3D |
| `uq_orderline_parent_number` | `transaction_order_items` | Partial unique | `(order_id, line_number)` when non-null | numbered lines | authority | supported | 3D |
| `uq_orderline_source_line` | same | Unique | nullable source quotation line | V1 source line | native | native | 3D |
| `ck_orderline_number_pos` | same | Check | null or line_number > 0 | all | native | native | 3D |
| `ck_orderline_quantity_pos` | same | Check | not V1 or quantity > 0 | V1 | native | native | 3D |
| `ck_orderline_money_nonneg` | same | Check | not V1 or unit_price/line_total >= 0 | V1 | native | native | 3D |
| `ck_orderline_unit` | same | Check | blank legacy or controlled unit | all | native | native | 3D |
| `ck_orderline_v1_required` | same | Check + service | V1 line requires source/snapshots/line; service verifies parent/source | V1 | scalar check; cross-row service | same | 3D |
| `ck_progress_statuses` | `transaction_order_progress_events` | Check | from blank/canonical and to canonical | all | native | native | 3D |
| `ck_progress_percent_range` | same | Check | 0 <= percent <= 100 | all | native | native | 3D |
| `ck_progress_reason` | same | Check | ON_HOLD/CANCELLED implies nonblank reason | all | native | native | 3D |
| `ck_audit_actor_ref` | `transaction_audit_events` | Check | actor_ref/display nonblank | all | native | native | 3D |
| `ck_audit_required` | same | Check | action/entity_type/entity_id nonblank | all | native | native | 3D |

Maker-checker, document-line same-RFQ, parent-contract-dependent line rules,
header-versus-child totals, valid transition edges, expected delivery versus
`ordered_at.date()`, and append-only behavior are service/permission/test
invariants, not falsely represented as portable `CheckConstraint` expressions.

## 18. Data mapping matrix and legacy import separation

| Source model.field | Target model.field | Transform | Deterministic? | Loss/ambiguity risk | Backfill phase | Validation | Failure handling |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| `BusinessCustomer.id` | same | preserve PK | Yes | none | 3B | count/PK checksum | abort |
| `.legacy_customer_id` | same | preserve nullable integer | Yes | duplicate already constrained | 3B | uniqueness | abort |
| `.company_name` | same | trim only after byte-for-byte report | Conditional | blank/whitespace | 3B | nonblank report | keep LEGACY; exception |
| `.contact_name/email/phone/country/notes` | same | preserve; normalize copies only when lossless | Conditional | invalid email/phone | 3B | validators and before/after report | keep raw/LEGACY; exception |
| `.status` | `.status` | exact active→ACTIVE, inactive→INACTIVE | Conditional | unknown values | 3B | distinct-value query | abort status backfill for row; exception |
| `.created_at/.updated_at` | same | preserve | Yes | none | 3B | min/max/count | abort |
| `.legacy_customer_id` | `.customer_code` | no automatic business code | No | provenance is not issued code | none | null allowed for LEGACY | exception; future reviewed allocation |
| any existing row | `.data_contract` | set LEGACY | Yes | none | 3B | all existing LEGACY | abort |
| actor evidence | `.created_by/.updated_by` | map exact stable FoundationUser ID only | Conditional | email/name ambiguity | 3B | one-to-one actor lookup | null + exception; never invent |
| `BusinessProduct.id/legacy_product_id` | same | preserve | Yes | none | 3B | count/unique | abort |
| `.name/slug/sku/content/SEO/sort fields` | same | preserve | Yes | none | 3B | checksums | abort |
| `.price` | same compatibility price | widen Decimal only | Yes | existing precision | 3B | exact Decimal roundtrip | stop on delta |
| `.status` | same compatibility field | preserve | Yes | not activity source | 3B | distinct values | keep unchanged |
| explicit SKU/business evidence | `.part_code` | copy only if validated canonical and unique | Conditional | SKU may not be business code | 3B | collision/format report | null + exception |
| explicit revision/unit evidence | `.revision/.unit` | normalized controlled token | Conditional | often missing | 3B | allowlist | null + exception |
| mapped material evidence | `.default_material` | target managed material FK | Conditional | legacy name collisions | future import | mapping report | leave null |
| legacy `crm.Customer.*` | `BusinessCustomer.*` | no schema-migration mapping | No in migration | duplicate identity | separate import task | fingerprint/collision/evidence | dry-run report; no write |
| legacy `catalog.Product.*` | `BusinessProduct.*` | no schema-migration mapping | No in migration | duplicate/code/float | separate import task | fingerprint/collision/money | dry-run report; no write |
| legacy `catalog.Material.*` | `BusinessMaterial.*` | explicit ID/name/standard mapping | Conditional | duplicate names/grade semantics | separate import task | source checksum and collision report | no write until Owner approval |
| legacy `QuoteRequest.*` | `SalesRfq.*` | explicit import only; never quotation | Conditional | status/date/customer ambiguity | separate import task | customer/line/file evidence | keep external; exception |
| legacy `QuoteRequestItem.*` | `SalesRfqLine.*` | explicit import only | Conditional | unit/date/material missing | separate import task | positive qty and mappings | exception |
| legacy `QuoteFile.*` | `SalesRfqDocument.*` | metadata plus verified file/checksum only | Conditional | missing/unsafe file | separate import task | MIME/content/checksum | reject row |
| `SalesQuotation.id/opportunity/customer/number` | same | preserve | Yes | customer may not equal RFQ | 3C | count/FK/unique | abort |
| `.status` | `.workflow_status` | no automatic map | No | approval/customer evidence absent | none | exception report | null, data_contract LEGACY |
| `.version` | `.revision` | only with explicit RFQ/family evidence and verified base | Conditional | one-based vs zero-based | reviewed future remediation | family collision report | null/exception |
| `.approval_status` | approval decision | never auto-create | No | no reviewer/evidence | none | n/a | retain compatibility only |
| `.subtotal/.discount_total/.total` | widened same fields | Decimal exact widen and equation audit | Conditional | historic calculation differences | 3C | currency-aware delta report | stop constraint, keep LEGACY |
| `SalesQuotationLine.*` | retained/widened fields | preserve description/FKs; widen Decimal | Conditional | zero price, missing unit/snapshot | 3C | quantity/money report | keep LEGACY; exception |
| line order evidence | `.line_number` | stable existing PK order only after Owner-approved rule | Conditional | display order may differ | remediation | uniqueness report | leave null |
| current lines | snapshot/source fields | do not fabricate | No | source RFQ absent | none | n/a | leave blank/null LEGACY |
| `TransactionOrder.id/legacy ID/number/customer/text fields` | same | preserve | Yes | semantic order ambiguity | 3D | count/checksum/FK | abort |
| `.status` | `.workflow_status` | no automatic classification | No | seeded QuoteRequest is not confirmed order | none | exception report | null, LEGACY |
| `.quoted_at` | `.source_quotation_sent_at` | ISO parse only with source quotation evidence | Conditional | timezone/meaning | remediation | parse + source equality | leave null/exception |
| `.completed_at` | `.completed_at_v1` | timezone-aware parse only with terminal evidence | Conditional | timezone/status | remediation | parse/status check | leave null/exception |
| `.total_amount` | widened same field | exact Decimal widen | Conditional | no currency/source | 3D | delta/equation report | keep LEGACY; no repair |
| `TransactionOrderItem.quantity` | widened Decimal quantity | integer to Decimal exact | Yes | none if positive | 3D | roundtrip/positive | exception if invalid |
| order item money/text/FKs | retained/widened and snapshots | preserve current; no snapshot fabrication | Conditional | missing source quote | 3D | FK/money report | keep LEGACY |
| `WorkflowApproval.*` | new approval/audit | no automatic mapping | No | requester=reviewer and wrong domain | none | historic report only | retain old table |
| `OrderStatusHistory.*` | `OrderProgressEvent` | no automatic mapping | No | actor strings/progress absent | none | historic report only | retain old table |
| `TransactionHistory.*` | `AuditEvent` | no automatic mapping | No | optional actor/free payload | none | historic report only | retain old table |
| actor email/name strings | FoundationUser FK | exact unique match only | Conditional | renamed/shared identity | remediation/import | match cardinality = 1 | null/exception; no fake actor |
| legacy float/text money | Decimal target | `Decimal(str(v))`, currency quantize | Conditional | missing currency/delta | import/remediation | tolerance USD .01/VND 1 | stop and report unexplained delta |

Schema migrations are deterministic and **never** inspect environment variables,
network services, or a legacy database. Conditional legacy import from a
schema migration is prohibited.

Any future legacy import is a separately authorized tool, proposed as
`python manage.py import_legacy_reference_data --dry-run`. It requires an
explicit read-only legacy URL, defaults to dry-run, fingerprints the source and
records its checksum, produces collision and evidence reports, is idempotent,
uses atomic batches with an explicit batch size, stores a resumable cursor,
never overwrites an established mapping, and requires separate Owner approval
for `--apply`. R2 and Phase 3B do not build or run this command.

## 19. Phase 3B, 3C, and 3D boundaries

### Phase 3B — Master Data and RFQ

Scope is only BusinessNumberSequence, schema-needed permission definitions,
Customer/Part extensions, Material, RFQ/line/document, TechnicalReview, their
constraints, and tests. It does not alter quotation/order fields or consumers.

- Entry: R2 approved; clean checkpoint; PostgreSQL test database identified;
  preflight of current managed master rows reviewed.
- Expected files: `apps/business_core/models.py`, `apps/sales/models.py`, narrowly
  scoped foundation permission migration, new migrations in those apps, and
  Phase 3B model/migration tests. No API/service/UI files.
- Exit: clean and existing-data migrations pass; constraints in section 17 for
  3B verified on PostgreSQL; SQLite fallback tests pass without concurrency
  claims; full suite has zero failures/errors; no legacy DB access.
- Compatibility: current fields/endpoints remain unchanged; new tables are not
  consumer-visible. Existing records stay `data_contract=LEGACY`.
- Recovery: reverse only on disposable verification DB; deployed additive
  schema remains during app rollback; forward-fix after any V1 write.

### Phase 3C — Quotation

Scope is only `SalesQuotation`, `SalesQuotationLine`, RFQ family/revision,
ApprovalDecision, CustomerDecision, money/currency/validity/snapshots,
constraints, and tests. It does not create/extend orders or switch consumers.

- Entry: Phase 3B exit evidence and RFQ constraints pass; quotation preflight
  reports all legacy statuses, totals, versions, and collisions.
- Expected files: `apps/sales/models.py`, new sales migrations, and Phase 3C
  model/migration/money/concurrency tests. No API/service/UI files.
- Exit: nullable compatibility migration, deterministic validation, then V1
  constraints pass on PostgreSQL; legacy rows remain readable and unpromoted;
  no synthetic approval/customer decision.
- Compatibility: `status`, `version`, and `approval_status` remain writable only
  by pre-existing consumers until Phase 4; canonical fields are not exposed.
- Recovery: constraints can reverse; do not remove canonical columns after V1
  rows exist; use forward-fix.

### Phase 3D — Order, Progress, Audit, and RBAC grants

Scope is only order/item extensions, progress/audit tables, completed RBAC
permission/role seed, constraints, and tests. User-to-role reassignment remains
Owner-reviewed and is not inferred.

- Entry: Phase 3C exit evidence passes; order/history/actor preflight reviewed;
  accepted quotation conversion invariants testable on PostgreSQL.
- Expected files: `apps/transaction_domain/models.py`, foundation and
  transaction-domain migrations, and Phase 3D migration/order/audit/RBAC tests.
  No API/service/UI files.
- Exit: one-order constraint, progress/audit checks, append-only enforcement
  tests, PostgreSQL conversion race tests, role fail-closed tests, and full suite
  pass; old order/history rows remain unchanged and readable.
- Compatibility: direct order/workflow endpoints are not switched in Phase 3D;
  Phase 4 owns dual-write and write cutoff.
- Recovery: application rollback leaves additive schema; reverse only before
  V1 writes on disposable DB; otherwise forward-fix.

## 20. R2 migration sequence

Proposed numeric prefixes are illustrative next positions; implementation must
use actual graph leaves. Every `RunPython` uses historical models, is idempotent,
and accesses only the migration database.

| Order | Phase | App | Proposed migration purpose | Schema operation | Data operation | Preconditions | Verification | Reverse/forward-fix | Risk |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 3B | foundation | define 3B permission rows | none | idempotent permission definitions only; no grants/users | foundation 0006; codes collision-free | exact code set/count | reverse created unreferenced rows; else forward | low |
| 2 | 3B | business_core | number sequence + nullable master extensions + Material | create sequence/material; add nullable customer/part fields/indexes; widen no data columns yet | set existing `data_contract=LEGACY` via field default state | preflight and backup evidence | schema introspection; old row checksums | reverse only empty/new columns on disposable; forward in deployment | low-yellow |
| 3 | 3B | business_core | deterministic master normalization | no schema | exact status case mapping and safe Decimal/no-loss transforms only | exception query reviewed | before/after counts; unmapped report | reversible mapping table; forward-fix | yellow |
| 4 | 3B | business_core | master constraints | add named 3B constraints/indexes | none | validation queries zero for applicable rows | PostgreSQL violation tests | reverse constraints; forward-fix data | yellow |
| 5 | 3B | sales | RFQ schema | create RFQ/line/document/review tables and named constraints | none | business core 3B complete; permission definitions exist | clean migration and invariants | reverse empty tables only; forward after writes | low-yellow |
| 6 | 3B | sales/tests gate | Phase 3B verification boundary | none | none | migrations 1–5 | migration executor clean/existing DB, full tests | stop; no 3C | low |
| 7 | 3C | sales | quotation nullable shadows and decisions | add data_contract/rfq/revision/workflow/date/snapshot/idempotency fields; use RFQ family number; widen Decimal; create decision tables | existing rows explicitly LEGACY | 3B exit; quotation preflight | schema/types and exact old values | reverse before V1; otherwise forward | yellow |
| 8 | 3C | sales | deterministic quotation validation/backfill | no schema | widen values; populate only explicitly evidenced canonical fields | mapping report approved | money delta/status/version exception report | reversible exact mapping; no ambiguous update | yellow |
| 9 | 3C | sales | quotation constraints/indexes | add named 3C constraints and partial uniques | none | all applicable validation queries zero | PostgreSQL SQL/introspection + negative tests | reverse constraints; forward-fix | yellow |
| 10 | 3C | sales/tests gate | Phase 3C verification boundary | none | none | migrations 7–9 | clean/existing migration, money and race tests, full suite | stop; no 3D | low |
| 11 | 3D | transaction_domain | nullable order shadows + progress/audit | add canonical fields/widen Decimal; create event tables | existing orders explicitly LEGACY | 3C exit; order/history preflight | old values/checksums and schema | reverse before V1 only; otherwise forward | yellow |
| 12 | 3D | transaction_domain | deterministic order validation | no schema | exact integer-to-Decimal widening; no status/source/evidence fabrication | mapping report approved | exception report and row counts | reversible exact transform | yellow |
| 13 | 3D | foundation | complete canonical role/permission grants | none | idempotent Admin/Sales/Manager permission links; no inferred user reassignment | exact action catalog approved | matrix query and fail-closed users | reverse only created links; forward-fix | yellow |
| 14 | 3D | transaction_domain | order/event constraints/indexes | add named 3D constraints and partial uniques | none | validation queries zero | PostgreSQL constraint/race/append-only tests | reverse constraints; forward-fix | yellow |
| 15 | 3D | all/tests gate | Phase 3D final verification | none | none | migrations 11–14 | clean/existing/reverse tests, full suite, diff audit | stop release or forward-fix | low |

No step adds a non-null field with a fabricated default to a populated table;
no step drops/renames compatibility fields; no step changes a consumer; no step
reads network, environment-dependent legacy data, or external files.

## 21. R2 test matrix

| Test ID | Phase | Layer | Scenario | Database | Expected result |
| --- | --- | --- | --- | --- | --- |
| `MIG-001` | 3B | migration | clean database through 3B | SQLite + PostgreSQL | graph applies; schema exact |
| `MIG-002` | 3B | migration | current managed-data fixture through 3B | PostgreSQL | PK/rows preserved; existing contract LEGACY |
| `MIG-003` | 3B | migration | legacy alias disabled/empty environment | SQLite + PostgreSQL | identical schema/result; no legacy access |
| `NUM-001` | 3B | model | customer/part/material code uniqueness | both | duplicate rejected |
| `NUM-002` | 3B | service contract | 20 concurrent business allocations | PostgreSQL | unique monotonic values; gaps allowed |
| `NUM-003` | 3B | fallback | sequence formatting/retry/lock error | SQLite | bounded outcome; no concurrency PASS claim |
| `RFQ-001` | 3B | constraint/service | zero/negative RFQ line quantity | both | rejected |
| `RFQ-002` | 3B | constraint/service | quote due after delivery; created-date rule | both | DB/service rejection as assigned |
| `DOC-001` | 3B | constraint | duplicate document group/version | both | rejected |
| `DOC-002` | 3B | service | document line belongs to another RFQ | both | rejected; no stored file metadata |
| `REV-001` | 3B | constraint | technical review missing reason | both | NEEDS_INFORMATION/DECLINED rejected |
| `RFQ-IDEM-001` | 3B | constraint | duplicate non-null RFQ idempotency key | both | duplicate rejected |
| `RFQ-IDEM-002` | 3B | constraint | V1 key without request hash or reverse | both | rejected |
| `RFQ-IDEM-003` | 3B | constraint | both RFQ idempotency fields null before Phase 4 | both | allowed |
| `MIG-101` | 3C | migration | clean and existing quotation data | both | old fields exact; shadows nullable; LEGACY retained |
| `QUO-001` | 3C | concurrency | simultaneous next revision | PostgreSQL | distinct revisions or bounded retry/conflict |
| `QUO-002` | 3C | partial unique | two effective V1 revisions same RFQ | PostgreSQL | second rejected atomically |
| `QUO-003` | 3C | service | creator approves own quotation | both | rejected; no decision/status change |
| `MON-001` | 3C | calculation | USD half-up line/header quantization | both | quantum 0.01 and exact stored 4dp |
| `MON-002` | 3C | calculation | VND half-up line/header quantization | both | quantum 1 and exact stored 4dp |
| `MON-003` | 3C | migration | legacy float/Decimal delta | both | over-tolerance row reported; no repair/promotion |
| `QUO-004` | 3C | service | accept expired quotation | both | rejected; no customer decision/order |
| `MIG-201` | 3D | migration | clean and existing order/history fixture | both | old fields/rows exact; canonical shadows nullable |
| `ORD-001` | 3D | concurrency | simultaneous conversion/idempotency retry | PostgreSQL | exactly one order, same result for same key |
| `ORD-002` | 3D | unique | two orders for one quotation | both | rejected |
| `ORD-003` | 3D | service/constraint | invalid progress/range/transition/reason | both | rejected atomically |
| `AUD-001` | 3D | model/API/admin | update/delete AuditEvent | both | no exposed mutation; manager/query guard rejects |
| `RBAC-001` | 3D | permission | legacy/unassigned user calls V1 action | both | fail closed |
| `MIG-301` | each | migration | forward then safe reverse before V1 writes | both | original schema/data restored in disposable DB |
| `MIG-302` | each | migration | reverse attempted after V1 fixture writes | both | test documents blocked/destructive boundary; forward-fix required |
| `PG-001` | 3C/3D | database | inspect partial unique/check SQL | PostgreSQL | exact named constraints active |
| `SQLITE-001` | all | fallback | constraint subset and service fallback | SQLite | supported checks pass; limitations explicitly asserted |

Only PostgreSQL results may close number allocation, quotation revision, one
effective revision, and conversion race acceptance criteria.

## 22. Risk register, stop conditions, and consistency gate

| Lane | Risk | Probability | Impact | Detection | Prevention | Stop condition | Recovery |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Green | additive empty-table schema | Low | Low | migration SQL/introspection | isolated migrations | unexpected destructive SQL | revert before writes or forward-fix |
| Yellow | nullable additions/widening on populated tables | Medium | Medium | lock timing and checksum tests | separate operations, maintenance plan | table rewrite/lock exceeds approved window | stop deployment; tune forward migration |
| Yellow | deterministic backfill | Medium | High | pre/post counts and exception report | whitelist transforms, historical models | unexplained delta or unknown value | rollback exact batch/forward-fix |
| Yellow | constraint activation | Medium | High | zero-violation preflight | add last, named constraints | any violating applicable row | do not add constraint; remediate separately |
| Yellow | PostgreSQL/SQLite divergence | High | Medium | engine-specific suite | PostgreSQL authority, service fallback | only SQLite evidence available | block concurrency release |
| Yellow | legacy import tool | Medium | High | fingerprint/collision/dry-run report | separate authorization and apply flag | checksum changed, collision, missing evidence | no apply; resume from verified cursor |
| Red | legacy import of ambiguous commercial data | Medium | Critical | exception/evidence review | no inference/promotion | would fabricate RFQ/decision/order | reject import; retain external/LEGACY |
| Red | drop/rename/destructive migration | Low | Critical | SQL plan/diff review | explicitly outside Phase 3 | any drop/rename/truncate | block task; redesign additive |
| Red | production data mutation | Medium | Critical | environment identity and approval gate | separate runbook/approval/backup | production target without explicit approval | stop; restore only via approved runbook |
| Yellow | business-number/revision race | Medium | High | PostgreSQL barrier tests | row locks, unique constraints, 3 retries | duplicate or unbounded retry | rollback transaction; conflict; investigate |
| Yellow | legacy money precision | High | High | currency delta report | Decimal(str), defined tolerance | missing currency/non-finite/over tolerance | keep LEGACY; stop promotion |
| Yellow | role mapping over-grants | Medium | Critical | permission matrix and user report | no inferred assignment | unknown role/user mapping | fail closed; Owner review |
| Yellow | compatibility consumer writes old fields | Medium | High | write telemetry/contract tests | Phase 4 adapter and cutoff | canonical/legacy divergence | rollback command; keep old reader; forward-fix |

Final consistency checks required before Phase 3B approval:

1. Every named constraint field appears in section 16; automated doc lint should
   compare tokens and report no unknown field.
2. Every target mapping field appears in section 16 and every source is present
   in the section 3 inventory/current model definition.
3. Migration review state never appears as a business-status choice.
4. `data_contract` is consistently `LEGACY` or `MVP_V1`; extended-table existing
   rows default/backfill LEGACY, new empty-table entities default MVP_V1, and
   future V1 services set MVP_V1 explicitly.
5. Quotation/order canonical lifecycle is always `workflow_status`; compatibility
   `status` is never described as canonical.
6. No migration reads or conditionally imports a legacy database; import is a
   separately authorized future tool.
7. 3B owns master/RFQ, 3C owns quotation, and 3D owns order/progress/audit/grants;
   their model/migration scopes do not overlap except declared dependencies.
8. All money fields use Decimal(20,4), quantities Decimal(16,4), currency quantum
   and `ROUND_HALF_UP`; child sums remain service-owned.
9. Every migration row in section 20 has verification and recovery guidance.
10. Referenced paths must exist at implementation start:
    `django_backend/apps/foundation/models.py`,
    `django_backend/apps/business_core/models.py`,
    `django_backend/apps/sales/models.py`,
    `django_backend/apps/transaction_domain/models.py`, and their migration/test
    directories.
11. This R2 document is a plan only and makes no schema-implementation claim.
12. Markdown tables must have consistent column counts and Mermaid fences must
    be balanced before handoff.

Resulting implementation gate: after documentation verification and Owner
approval, Phase 3B has no remaining field-name, number, money, constraint,
mapping, import, or phase-boundary decision to invent.
