# Migration Plan - mecprecision-vietnam

Phase: 1 - Migration Planning  
Based on: `TECHNICAL_AUDIT_REPORT.md`  
Rule: Planning only. No code, no Django models, no database migration.

## 1. Migration Goals

The goal is to migrate the current custom Python backend to Django 5.x + Django REST Framework safely.

Primary objectives:

1. Keep the legacy backend running unchanged.
2. Run Django in parallel until parity is proven.
3. Move one module at a time.
4. Start with read-only behavior.
5. Preserve existing API behavior and database data.
6. Use rollback-friendly steps.
7. Use Django built-in features where appropriate, especially auth, sessions, CSRF, permissions, testing, and middleware.

Non-goals for early phases:

- No big rewrite.
- No production database migration.
- No legacy code deletion.
- No business logic change without review.
- No direct switch of admin login until auth compatibility is designed.

## 2. Migration Phases

### Phase 0 - Technical Audit

Status: completed.

Output:

- `TECHNICAL_AUDIT_REPORT.md`

Purpose:

- Understand existing structure, database, API, auth, infrastructure, test coverage, and risk.

### Phase 1 - Migration Planning

Status: current phase.

Outputs:

- `MIGRATION_PLAN.md`
- `MODULE_DEPENDENCY_GRAPH.md`
- `DATABASE_MIGRATION_STRATEGY.md`
- `API_MIGRATION_PLAN.md`

Purpose:

- Define safe module order.
- Define dependency graph.
- Define database migration approach.
- Define API backward compatibility strategy.

No code is written in this phase.

### Phase 2 - Django Foundation

Purpose:

- Create or verify the parallel Django project foundation.
- Configure environment, settings, logging, testing, DRF, CORS, health checks.

Allowed:

- Django project skeleton.
- Django apps skeleton.
- `.env.example`.
- `pytest.ini`.
- README/setup docs.
- health check endpoint.

Not allowed:

- Business logic.
- Django ORM models for legacy tables.
- Database migration.
- Legacy route changes.

Exit criteria:

- `python manage.py check` passes.
- `pytest` passes.
- Django runs separately from legacy backend.

### Phase 3 - Database Analysis

Purpose:

- Create formal table-to-model mapping before writing any Django model.

Output:

- `DATABASE_MAPPING.md`

Required contents:

- Legacy table.
- Proposed Django model.
- Field mapping.
- Relationship mapping.
- Index mapping.
- Risk per table.
- Whether model should be unmanaged at first.

Exit criteria:

- Stakeholder reviews and approves model mapping.
- No database migration has been run.

### Phase 4 - Read-Only ORM Models

Purpose:

- Add unmanaged Django ORM models mapped to existing SQLite tables.

Strategy:

- `managed = False` for all legacy tables.
- No migrations touching legacy tables.
- Add read-only service/API tests comparing Django output with legacy API output.

Exit criteria:

- Django can read critical legacy tables.
- Output parity checks pass for products, categories, customers, contacts, quotes, news.
- Legacy backend still passes existing tests.

### Phase 5 - Public Read API Migration

Purpose:

- Add Django/DRF read endpoints for existing public APIs.

First candidates:

1. `/api/home`
2. `/api/products`
3. `/api/products/{id}`
4. `/api/product-categories`
5. `/api/capabilities`
6. `/api/news`

Strategy:

- Initially expose under a versioned or parallel namespace, for example `/django/api/...` or separate host/port.
- Compare response shape with legacy APIs.

Exit criteria:

- Contract tests prove Django read APIs match legacy response behavior.
- Frontend can be pointed to Django read APIs in local/staging without regression.

### Phase 6 - Public Write API Migration

Purpose:

- Migrate lower-risk public write endpoints after read parity is proven.

Candidates:

1. `/api/contact`
2. `/api/quote-request`
3. Public AI chat if non-mutating.

Required safeguards:

- Transaction handling.
- Validation parity.
- Error response parity.
- Event/job behavior parity.
- Audit and logging.

Exit criteria:

- Legacy and Django write behaviors match in integration tests.
- Rollback path is tested.

### Phase 7 - CMS Read Migration

Purpose:

- Move admin CMS read pages/APIs into Django module by module.

Order:

1. Dashboard read.
2. Products read.
3. Categories read.
4. News read.
5. Contacts read/export.
6. Quotes read.
7. Customers read.
8. Media read.
9. Pages/menus/banners read.
10. Users/settings/developer read.

Exit criteria:

- Admin can inspect data in Django without changing production data.

### Phase 8 - CMS Write Migration

Purpose:

- Move admin write workflows into Django after read views are stable.

Order:

1. Categories.
2. Products.
3. News.
4. Contacts.
5. Customers and notes.
6. Quotes.
7. Newsletter.
8. Pages/menus/banners.
9. Media.
10. Users/settings.

Required safeguards:

- Django forms/serializers.
- CSRF.
- Permission checks.
- Transactions.
- File upload validation.
- Audit log.

Exit criteria:

- Each module has module report, tests, rollback plan.

### Phase 9 - Authentication Migration

Purpose:

- Move from custom auth/session to Django Auth carefully.

Why late:

- Auth impacts every admin module.
- Session/password compatibility risk is high.

Required strategy:

- Preserve legacy users.
- Support legacy password hash verification during transition.
- Map roles to Django groups/permissions.
- Decide whether sessions must be shared or separated.

Exit criteria:

- Login/logout/reset/change password/session revocation/role permissions are covered by tests.
- Admin module permission matrix passes.

### Phase 10 - Infrastructure Cutover

Purpose:

- Switch traffic gradually from legacy to Django.

Strategy:

- Start with separate port/service.
- Add reverse proxy route rules.
- Route low-risk APIs first.
- Keep legacy fallback route.
- Monitor logs, errors, latency.

Exit criteria:

- Full parity.
- Rollback tested.
- Backups verified.

### Phase 11 - Legacy Retirement

Purpose:

- Remove legacy only after Django has full validated parity.

Allowed only when:

- All modules migrated.
- Tests pass.
- Data migration is validated.
- Production cutover is stable.
- Stakeholder approves removal.

## 3. Module Migration Order

Recommended order:

| Order | Module | Reason |
|---:|---|---|
| 1 | Core | Health, settings, logging, DRF base, no business dependency. |
| 2 | Catalog: Categories | Product depends on categories. Small surface. |
| 3 | Catalog: Products | Central public module, many downstream dependencies. |
| 4 | Manufacturing/Capabilities | Public content depends on machines/processes/materials. |
| 5 | CRM: Customers | Quotes and notes depend on customers. |
| 6 | CRM: Contacts | Public form and admin contact workflow. |
| 7 | Sales: Quotation | Depends on customers, products, materials, files. |
| 8 | Content: News | Mostly independent; supports public content and AI search. |
| 9 | CMS Common: Pages/Menus/Banners | Admin content but lower business risk. |
| 10 | Media | Cross-cutting upload dependency; requires security review. |
| 11 | Newsletter | Simple marketing workflow. |
| 12 | AI | Depends on product/news/contact/quote data for context. |
| 13 | Dashboard | Depends on counts from many modules. |
| 14 | Events/Queue/Notifications | Cross-cutting side effects; migrate after core data modules. |
| 15 | Developer/System Tools | Sensitive operations: backup, migrations, logs. |
| 16 | Accounts/Auth | High-risk, affects all admin modules; migrate late. |
| 17 | Admin CMS Write Workflows | After auth/permissions and module services are stable. |

## 4. Dependencies

High-level dependency flow:

```text
Core
  -> Database mapping
  -> Catalog/CMS/CRM/Sales/Content modules
  -> AI and Dashboard
  -> Admin CMS workflows
  -> Auth cutover
  -> Infrastructure cutover
```

Critical module dependencies:

- Products depend on categories.
- Product detail depends on product images/specs/materials/processes.
- Quote requests depend on customers.
- Quote items depend on quote requests, products, materials.
- News depends on news categories and tags.
- Dashboard depends on products, news, customers, contacts, quotes, sessions, visits.
- AI depends on products, news, contacts, quotes, AI history/cache.
- Admin CMS depends on auth, permissions, CSRF, file upload, audit.
- Media is cross-cutting for products/news/banners/users.

Detailed dependency graph is maintained in:

- `MODULE_DEPENDENCY_GRAPH.md`

## 5. Risk Analysis

### 5.1 Highest Risks

| Risk | Severity | Mitigation |
|---|---:|---|
| Incorrect database model mapping | High | Create `DATABASE_MAPPING.md`, use unmanaged models first, compare output with legacy SQL. |
| Auth/session incompatibility | High | Migrate auth late, implement compatibility strategy, test every auth flow. |
| Breaking admin CMS workflows | High | Migrate read-only first, then write workflows one module at a time. |
| Large `backend/app.py` route behavior mismatch | High | Preserve legacy routes, add Django routes in parallel, use contract tests. |
| File upload/storage mismatch | Medium/High | Audit uploads before media migration, keep existing path format initially. |
| SQLite concurrency limitations | Medium | Do not change DB engine early; later evaluate PostgreSQL after ORM parity. |
| AI prompt or fallback behavior mismatch | Medium | Keep AI non-mutating and preserve fallback behavior. |
| Partial OpenAPI docs | Medium | Build DRF schemas gradually and compare with legacy OpenAPI. |

### 5.2 Module-Specific Risks

| Module | Risk | Mitigation |
|---|---|---|
| Products | Many related tables and SEO/media fields. | Start read-only, add relationship tests. |
| Quotes | Multi-step transaction and customer/item/file creation. | Preserve transaction boundaries, test rollback. |
| Auth | Custom PBKDF2 and legacy SHA hash. | Custom Django hasher or migration command. |
| Media | File paths and folder operations. | Keep storage local and compatible first. |
| Dashboard | Aggregates across many tables. | Migrate after source modules. |
| AI | External Ollama may be offline. | Keep fallback response and history logging. |
| Developer | Can run migrations/backups/workers. | Restrict permissions and add audit logs. |

## 6. Rollback Strategy

### 6.1 General Rollback Rules

For every phase:

1. Legacy backend remains unchanged.
2. Django runs in parallel.
3. No legacy route is removed.
4. No legacy database table is modified without backup and approval.
5. Each module has feature flag or route separation.
6. If Django behavior fails, route traffic back to legacy.
7. Keep all legacy tests passing.

### 6.2 Database Rollback

Before any schema-affecting work:

1. Copy `backend/database/mecprecision.sqlite`.
2. Save backup under `backups/` with timestamp.
3. Verify backup can be opened.
4. Run validation queries before and after migration.
5. Do not run Django migrations against legacy tables until explicitly approved.

Initial ORM migration rollback:

- If unmanaged model mapping fails, remove/disable Django route only.
- No data rollback required because no schema/data is changed.

### 6.3 API Rollback

API migration should use one of these safe patterns:

Option A: Parallel namespace

```text
Legacy: /api/products
Django: /django/api/products
```

Rollback:

- Stop using `/django/api/...`.

Option B: Reverse proxy route switch

```text
/api/products -> legacy or Django by proxy config
```

Rollback:

- Revert proxy rule to legacy.

Option C: Header-based shadow mode

```text
Normal request -> legacy response
Shadow request -> Django comparison/log only
```

Rollback:

- Disable shadow comparison.

### 6.4 Auth Rollback

Auth migration must have a separate rollback:

- Keep legacy login available until Django auth is proven.
- Do not overwrite password hashes in bulk.
- If using custom Django password hasher, keep legacy hasher enabled until all users migrate.
- If Django session fails, restore legacy `mecprecision_session` route handling.

### 6.5 Deployment Rollback

During cutover:

- Keep old Docker `web` service.
- Add Django as a separate service.
- Proxy only selected routes.
- Keep health checks for both.
- Revert Nginx route mapping if error rate increases.

## 7. Testing Strategy

Minimum tests for each migrated module:

- Unit tests for service logic.
- Repository/ORM query tests.
- API integration tests.
- Legacy-vs-Django contract tests.
- Permission tests for admin routes.
- Rollback smoke test where relevant.

Required commands during migration:

```powershell
python -m unittest discover -s backend\tests -p "test_*.py"
python manage.py check
pytest
```

For each module, create a module report:

```text
MODULE_REPORT.md
```

The report must include:

- Old structure.
- New structure.
- Files created.
- Files changed.
- Database changes.
- API changes.
- Security review.
- Performance review.
- Test coverage.
- Rollback plan.

## 8. Decision Points Requiring Review

These decisions should not be made silently:

1. Whether to keep SQLite or migrate to PostgreSQL.
2. Whether Django and legacy must share admin sessions.
3. Whether existing admin URLs should remain exactly the same.
4. Whether to migrate public pages to Django templates or keep frontend static.
5. Whether AI can write data or only suggest content.
6. Whether to replace SQLite queue with Celery/RQ/Huey.
7. When to retire `backend/app.py`.

## 9. Phase 1 Conclusion

The recommended migration is incremental:

1. Finish Django foundation.
2. Produce formal database mapping.
3. Add unmanaged read-only models.
4. Add read-only APIs.
5. Add contract tests.
6. Move writes only after read parity.
7. Move authentication late.
8. Cut over route by route.

Next recommended phase:

```text
PHASE 2 - DJANGO FOUNDATION
```

Stop here and wait for review.

## 10. Phase 1 Review Update - Migration Philosophy

The migration philosophy is:

1. Incremental migration.
2. Backward compatibility first.
3. Rollback before cutover.
4. Legacy system remains operational until Django parity is proven.

This means Django should be introduced as a parallel system, not as a replacement on day one.

The legacy Python backend remains the source of truth during early phases. Django can read, compare, and later write only after validation.

Key rules:

- Do not remove legacy routes during migration.
- Do not move all modules at once.
- Do not change database schema before model mapping is reviewed.
- Do not switch authentication early.
- Do not migrate write workflows before read parity exists.
- Every migrated module must have a rollback path.

## 11. Phase 1 Review Update - Phase A To H Migration Plan

The migration plan is organized into business-safe phases. Each phase includes dependencies, risk, rollback approach, and validation method.

### Phase A - Foundation

Scope:

- config
- core
- common utilities
- logging
- error handling

Dependencies:

- No business module dependency.
- Environment configuration must be reviewed first.

Risk:

- Low business risk.
- Medium architecture risk if `core` becomes too large.

Rollback approach:

- Disable Django foundation service.
- Keep legacy backend as active runtime.
- No database rollback required.

Validation method:

- Django health check works.
- Django settings load from environment.
- Logging and error response format are consistent.
- `core` contains only health, middleware, exceptions, logging, and constants.

### Phase B - Catalog

Scope:

- categories
- materials
- machines
- processes
- products

Dependencies:

- Phase A foundation.
- Database mapping for catalog tables.
- API compatibility layer for public product endpoints.
- Media read-only strategy for existing image/file paths.

Risk:

- Medium/high because products connect to categories, specs, images, materials, processes, SEO, and public pages.

Rollback approach:

- Keep legacy `/api/products` and product admin routes active.
- Use Django read-only endpoints first.
- Revert route/proxy/frontend config to legacy if mismatch appears.

Validation method:

- Compare product count between legacy SQL and Django ORM.
- Compare product list response fields.
- Compare product detail response fields.
- Validate category, material, machine, and process relationships.
- Validate image/file paths remain usable.

### Phase C - CRM

Scope:

- customers
- contacts

Dependencies:

- Phase A foundation.
- Database mapping for customer/contact tables.
- Event/notification behavior documented before write migration.

Risk:

- Medium because contact requests are business leads.
- Customer data may be referenced by quotation.

Rollback approach:

- Start with read-only CRM views.
- Keep legacy contact submit route active until Django write behavior is tested.
- Restore from backup if a write migration creates incorrect records.

Validation method:

- Compare customer/contact counts.
- Validate contact status values.
- Validate contact detail fields.
- Test contact form validation in staging before cutover.

### Phase D - Sales

Scope:

- quotation
- quote items
- quote files

Dependencies:

- Phase A foundation.
- Phase B catalog.
- Phase C CRM.
- Media read-only support for quote files.
- Transaction strategy approved.

Risk:

- High because quotation creates multi-table business records and may trigger events/jobs/notifications.

Rollback approach:

- Keep legacy quote request write route active.
- Add Django quotation as read-only first.
- Before write cutover, backup database and test transaction rollback.
- If Django quote write fails, route back to legacy and restore affected rows if necessary.

Validation method:

- Compare quote request counts.
- Validate quote request -> quote items relationship.
- Validate quote files path behavior.
- Validate transaction rollback on partial failure.
- Validate status workflow: pending, processing, quoted, completed.

### Phase E - Content

Scope:

- news
- CMS pages
- menus
- banners

Dependencies:

- Phase A foundation.
- Content table mapping.
- Media read-only support for thumbnails and banners.
- API compatibility layer for news/public content endpoints.

Risk:

- Medium because content affects public pages, SEO, and navigation.

Rollback approach:

- Keep existing public HTML/page rendering active.
- Expose Django content APIs in parallel.
- Revert menu/page/banner data source to legacy if output differs.

Validation method:

- Compare news/category/tag counts.
- Validate page slug behavior.
- Validate menu nested structure.
- Validate banner status/date visibility.
- Validate SEO metadata fields.

### Phase F - Security

Scope:

- accounts
- permissions
- admin

Dependencies:

- Phase A foundation.
- Admin user/session/password table mapping.
- Permission matrix review.
- CSRF/session/password reset strategy.

Risk:

- Very high because security affects all admin access.

Rollback approach:

- Keep legacy login/logout/session routes active.
- Do not overwrite existing password hashes in bulk.
- Keep legacy session cookie behavior available during transition.
- If Django auth fails, route all admin traffic back to legacy.

Validation method:

- Validate login/logout.
- Validate password reset.
- Validate account lock/unlock.
- Validate role/permission access.
- Validate CSRF for admin writes.
- Validate session expiration and multi-device sessions.

### Phase G - AI

Scope:

- chatbot
- translation
- content/SEO generation
- contact summary
- quote analysis
- PDF/catalogue reading
- developer assistant

Dependencies:

- Phase A foundation.
- Catalog/content/CRM/sales read APIs.
- Ollama availability/fallback strategy.
- Admin permission strategy for admin-only AI features.

Risk:

- Medium because AI can be slow, unavailable, or produce inaccurate output.
- High if AI is allowed to write data directly.

Rollback approach:

- Keep AI advisory/non-mutating at first.
- If Ollama is unavailable, return controlled fallback text.
- Disable AI endpoints without affecting core website operation.

Validation method:

- Test Ollama online and offline behavior.
- Validate timeout behavior.
- Validate prompt does not expose secrets.
- Validate AI output is marked as suggestion unless approved by admin.

### Phase H - Dashboard

Scope:

- dashboard counts
- charts
- online users
- visits
- contacts
- quote summaries
- AI operational insights

Dependencies:

- Phase B catalog.
- Phase C CRM.
- Phase D sales.
- Phase E content.
- Phase F security for admin-only dashboard.

Risk:

- Medium because dashboard aggregates many modules and can show wrong numbers if dependencies are incomplete.

Rollback approach:

- Keep legacy dashboard active.
- Add Django dashboard read-only first.
- Revert admin dashboard route to legacy if counts differ.

Validation method:

- Compare product count.
- Compare news count.
- Compare contact count.
- Compare quote count.
- Compare 7-day, 30-day, and 12-month chart values.

## 12. Phase 1 Review Update - Planning Consistency Notes

The Phase A-H plan is consistent with the original detailed Phase 0-11 migration plan:

- Phase A maps to Django foundation and core setup.
- Phase B maps to catalog/category/product migration.
- Phase C maps to customer/contact migration.
- Phase D maps to quotation migration.
- Phase E maps to content/CMS migration.
- Phase F maps to auth/admin/security migration.
- Phase G maps to AI migration.
- Phase H maps to dashboard migration.

The important correction is that authentication remains late even though some user tables can be mapped earlier as read-only data.
