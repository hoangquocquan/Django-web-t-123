# ADR-009 CRM Migration Strategy

## Context

Legacy CRM tables currently included in the Django migration are:

- `customers`
- `customer_notes`
- `contact_requests`

These tables support customer records, customer care notes and public contact form submissions.

The current `contact_requests` table has no foreign key to `customers`. Because of that, Django must not create a fake relationship between contact requests and customers in Phase 5.1.

## Decision

Use the read-only unmanaged ORM migration pattern for CRM.

CRM models remain:

- `managed = False`
- routed through database alias `legacy`
- protected by `LegacyReadOnlyModel`
- accessed through repository and service boundaries

No CRM API, serializer, CRUD write operation or data migration is introduced in this phase.

## Customer Relationship Strategy

Future customer/contact matching should be staged, not automatic-only.

Recommended matching order:

1. Email matching

   Normalize email by trimming spaces and lowercasing. If one contact email matches exactly one customer email, the system can suggest a link.

2. Phone matching

   Normalize phone by removing spaces, punctuation and country-code formatting differences. Phone matching should be secondary because formatting quality is usually less stable than email.

3. Manual verification

   Admin should confirm suggested links before permanent association. This avoids merging unrelated customers who share a company phone or generic email.

4. Future relationship table

   If CRM needs durable linking without changing `contact_requests`, create a separate table such as `customer_contact_links` in a future write-enabled migration phase.

## Consequences

Benefits:

- Preserves legacy database safety.
- Avoids incorrect customer/contact relationships.
- Creates a repeatable governance pattern before Phase 6.
- Keeps CRM service/repository boundaries clean.

Risks:

- Contact/customer linking remains manual or inferred until a future phase.
- Existing invalid customer email data can reduce matching quality.
- Contact requests currently missing email/phone/company cannot be matched reliably.

Future actions:

- Define matching normalization rules.
- Add duplicate review workflow in CRM UI/API phase.
- Create relationship table only after architecture approval.
- Add rollback plan before any write-enabled CRM migration.

## Status

Accepted
