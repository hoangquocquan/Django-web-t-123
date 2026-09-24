# ADR-010 Sales Quotation Strategy

## Context

Legacy sales tables:

- `quote_requests`
- `quote_request_items`
- `quote_files`

Dependencies:

CRM:

- `customers`

Catalog:

- `products`
- `materials`

Phase 6 mapped these tables with unmanaged read-only Django ORM models. Phase 6.1 hardens the architecture before CMS migration and before any future write-enabled quotation work.

## Decision

Use the read-only unmanaged ORM pattern for Sales / Quotation.

Sales models remain:

- `managed = False`
- routed through database alias `legacy`
- protected by `LegacyReadOnlyModel`
- accessed through repository and service boundaries

No Sales API, serializer, CRUD write operation, pricing change or data migration is introduced in Phase 6.1.

## Domain Boundary

CRM responsibility:

- Own customer identity and customer profile data.
- Decide future customer creation/linking rules.
- Provide customer records to quotation flows.

Catalog responsibility:

- Own product and material reference data.
- Provide current product/material metadata.
- Define catalog change lifecycle.

Sales responsibility:

- Own quotation lifecycle.
- Own quote header, quote item and quote file metadata.
- Preserve historical quote state when future snapshot fields are approved.
- Coordinate future write transaction boundaries.

## Consequences

Benefits:

- Keeps cross-module ownership clear.
- Avoids Sales mutating customer, product or material master data.
- Preserves safe legacy read-only behavior.
- Prepares a clean path for future transaction-safe quotation writes.

Risks:

- Current quote item rows reference live product/material records, so historical quote state is not fully protected yet.
- File metadata exists in database, but physical file lifecycle is outside database rollback.
- Status workflow values need normalization before future write APIs.

Future actions:

- Approve snapshot fields before quote write migration.
- Approve transaction boundary before quote creation APIs.
- Approve file lifecycle and cleanup process before upload migration.
- Add status transition policy before workflow automation.

## Status

Accepted
