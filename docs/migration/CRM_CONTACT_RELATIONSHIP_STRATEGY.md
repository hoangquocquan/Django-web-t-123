# CRM Contact Relationship Strategy

## Current State

`contact_requests` is an independent legacy table.

It does not have:

- `customer_id`
- foreign key to `customers`
- many-to-many link table

Therefore Phase 5.1 keeps `ContactRequest` independent in Django ORM.

## Option A: Email Matching

Description:

Match `contact_requests.email` to `customers.email` after trimming spaces and lowercasing.

Benefits:

- Usually the most reliable customer identifier.
- Easy to explain to admin users.
- Easy to test.

Risks:

- Current contact demo rows have missing email.
- Customer table currently contains one invalid email value.
- Generic company emails can belong to multiple people.

## Option B: Phone Matching

Description:

Match `contact_requests.phone` to `customers.phone` after normalizing spaces, punctuation and country code formats.

Benefits:

- Useful when email is missing.
- Good for sales follow-up workflows.

Risks:

- Phone format can vary heavily.
- Company hotline numbers can map to many contacts.
- Requires a normalization policy.

## Option C: Manual Customer Linking

Description:

Admin reviews a contact request and manually links it to an existing customer or creates a new customer in a future write-enabled phase.

Benefits:

- Safest for business data.
- Avoids accidental customer merge/link mistakes.
- Works even when email/phone is incomplete.

Risks:

- Requires admin effort.
- Needs UI/API in a later phase.

## Option D: New Relationship Table

Description:

Create a future Django-owned table such as `customer_contact_links`.

Possible fields:

- `id`
- `customer_id`
- `contact_request_id`
- `match_method`
- `confidence_score`
- `verified_by`
- `verified_at`

Benefits:

- Does not require changing legacy `contact_requests`.
- Preserves audit history.
- Allows suggested and verified links.

Risks:

- Requires schema migration in a future approved phase.
- Needs rollback strategy and data validation.

## Recommended Approach

Use a staged strategy:

1. Keep Phase 5.1 read-only with no direct relation.
2. In a future CRM API/UI phase, show suggested matches by email first, then phone.
3. Require manual verification before saving a permanent link.
4. Store approved links in a new Django-owned relationship table, not by mutating legacy contact rows.

## Decision

Do not create database changes in Phase 5.1.

Document the strategy and keep ORM mapping faithful to current legacy schema.
