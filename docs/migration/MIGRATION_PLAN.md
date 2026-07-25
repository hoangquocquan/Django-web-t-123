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
