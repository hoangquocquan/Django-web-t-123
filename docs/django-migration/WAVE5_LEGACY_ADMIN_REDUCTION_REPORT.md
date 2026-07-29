# Wave 5 Legacy Admin Reduction Report

## Purpose

This report classifies which legacy admin areas can be reduced later and which must remain for compatibility.

## Can Remove Later

These areas now have Django-owned API replacements for migrated domains, but should only be removed after frontend cutover and traffic evidence:

- Product admin read/create/update flows.
- Customer admin read/create/update flows.
- Inventory warehouse/item/adjustment flows.
- Order admin read/create/update flows.
- Workflow transition flows.
- Transaction history listing.
- Admin dashboard counters for migrated domains.
- Admin permission listing for Django foundation roles.

## Keep For Compatibility

These areas remain active because the current browser-facing admin UI still depends on legacy rendering or because a later migration wave must handle them:

- `/admin` HTML shell and sidebar rendering.
- Legacy cookie session behavior.
- Legacy upload/media handling.
- Legacy redirects and form post behavior.
- Existing `/admin/login`, `/admin/logout`, and account pages.

## Needs Future Migration

The following admin modules were not fully transferred in Wave 5:

- Categories.
- News.
- Media manager.
- Dynamic pages.
- Menu builder.
- Banners.
- Contacts and quote assignment UI.
- Newsletter UI.
- CMS settings.
- AI admin tools.
- Developer tools.
- Audit log viewer.

## Rollback Strategy

No rollback is required for legacy admin availability because no legacy route was deleted or disabled.

If Django admin APIs fail, operators can continue using existing legacy `/admin` pages while fixes are applied.

## Decision

Wave 5 reduces future legacy dependency by adding Django admin APIs, but it intentionally keeps legacy admin UI alive until a later cutover phase.
