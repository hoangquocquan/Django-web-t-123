# API Migration Plan

## 1. Purpose

This document plans how the current legacy API will be migrated gradually to Django REST Framework.

The goal is not to rewrite everything immediately. The goal is to create Django APIs in parallel, compare them with the existing legacy APIs, and switch traffic only when each module is safe.

This file is documentation only.

No Django models are created in this phase.
No database migration is performed in this phase.
No application code is changed in this phase.

## 2. Migration Principles

- Keep the legacy API running during migration.
- Build Django API endpoints in a separate namespace first.
- Start with read-only endpoints before write endpoints.
- Keep response data compatible with the current frontend.
- Compare legacy output and Django output before switching.
- Migrate one module at a time.
- Roll back by routing traffic back to the legacy API.

## 3. Existing API Groups

The current backend is a custom Python HTTP server. It serves both website pages and API-like routes.

Based on the technical audit, the API surface can be grouped as follows.

| Group | Purpose | Risk |
| --- | --- | --- |
| Health and developer APIs | Check server status, version, docs, developer tools | Low |
| Public website APIs | Home, products, categories, news, contact, quote request | Medium |
| CMS admin APIs/pages | Admin management screens and save actions | High |
| Authentication APIs/pages | Login, logout, reset password, sessions, account security | High |
| Media upload APIs | Upload, preview, rename, delete files | High |
| AI APIs | Chatbot, translation, content generation, analysis tools | Medium |
| External integration APIs | AWS demo, external API examples | Medium |

## 4. Proposed Django API Namespace

At the beginning, Django should not replace the old `/api/...` routes directly.

Use a versioned namespace:

```text
/api/v1/
```

Recommended examples:

```text
GET  /api/v1/health/
GET  /api/v1/home/
GET  /api/v1/catalog/products/
GET  /api/v1/catalog/products/{id}/
GET  /api/v1/catalog/categories/
GET  /api/v1/content/news/
POST /api/v1/crm/contacts/
POST /api/v1/sales/quote-requests/
POST /api/v1/ai/chat/
```

This allows:

- Legacy frontend to keep using old routes.
- New frontend or test tools to call Django routes.
- Route-by-route cutover later.

## 5. Existing API To Django Endpoint Map

| Current Legacy Endpoint | Method | New Django Endpoint | Migration Phase | Compatibility Note |
| --- | --- | --- | --- | --- |
| `/api/health` | GET | `/api/v1/health/` | Phase 2 | Safe first endpoint |
| `/api/version` | GET | `/api/v1/version/` | Phase 2 | Must include app version and environment |
| `/api/home` | GET | `/api/v1/home/` | Phase 3 | Must keep homepage JSON shape stable |
| `/api/products` | GET | `/api/v1/catalog/products/` | Phase 3 | Needs search, category, status, sort, pagination |
| `/api/products/{id}` | GET | `/api/v1/catalog/products/{id}/` | Phase 3 | Must preserve product detail fields |
| `/api/product-categories` | GET | `/api/v1/catalog/categories/` | Phase 3 | Must match category names and slugs |
| `/api/capabilities` | GET | `/api/v1/catalog/capabilities/` | Phase 3 | Read-only first |
| `/api/news` | GET | `/api/v1/content/news/` | Phase 4 | Needs category, tag, featured, publish status |
| `/api/contact` | POST | `/api/v1/crm/contacts/` | Phase 5 | Requires validation and anti-spam strategy |
| `/api/quote-request` | POST | `/api/v1/sales/quote-requests/` | Phase 5 | High business value, must test carefully |
| `/api/ai/chat` | POST | `/api/v1/ai/chat/` | Phase 6 | Should preserve Ollama fallback behavior |
| `/api/ai/content-seo` | POST | `/api/v1/ai/content-seo/` | Phase 6 | Admin-facing, requires auth later |
| `/api/ai/translate` | POST | `/api/v1/ai/translate/` | Phase 6 | Can be separated from static translations |
| `/api/openapi.json` | GET | `/api/v1/schema/` | Phase 7 | Django should generate OpenAPI automatically |
| `/api/docs` | GET | `/api/v1/docs/` | Phase 7 | Swagger or Redoc can be added later |
| `/api/aws-demo` | GET | `/api/v1/integrations/aws-demo/` | Phase 8 | Keep as demo integration only |

## 6. Admin Route Migration Map

The current admin system includes many server-rendered pages. These should not be replaced first.

| Legacy Admin Area | Current Route Example | Django Future Endpoint | Priority |
| --- | --- | --- | --- |
| Dashboard | `/admin` | `/api/v1/admin/dashboard/` | Medium |
| Products | `/admin/products` | `/api/v1/admin/products/` | High |
| Categories | `/admin/categories` | `/api/v1/admin/categories/` | High |
| News | `/admin/news` | `/api/v1/admin/news/` | Medium |
| Media | `/admin/media` | `/api/v1/admin/media/` | High |
| Pages | `/admin/pages` | `/api/v1/admin/pages/` | Medium |
| Menu | `/admin/menus` | `/api/v1/admin/menus/` | Medium |
| Banner | `/admin/banners` | `/api/v1/admin/banners/` | Low |
| Contacts | `/admin/contacts` | `/api/v1/admin/contacts/` | High |
| Quote Requests | `/admin/quotes` | `/api/v1/admin/quote-requests/` | High |
| Customers | `/admin/customers` | `/api/v1/admin/customers/` | Medium |
| Newsletter | `/admin/newsletter` | `/api/v1/admin/newsletter/` | Low |
| Users | `/admin/users` | `/api/v1/admin/users/` | High |
| Settings | `/admin/settings` | `/api/v1/admin/settings/` | Medium |
| Developer | `/admin/developer` | `/api/v1/admin/developer/` | Low |

Admin APIs should be migrated only after:

- Authentication strategy is reviewed.
- Permission rules are documented.
- CSRF and session behavior are planned.
- File upload behavior is tested.

## 7. API Migration Phases

### Phase 1: Planning

Current phase.

Deliverables:

- Migration plan.
- Module dependency graph.
- Database migration strategy.
- API migration plan.

No code should be changed in this phase.

### Phase 2: Django Health And Core API

Add only safe endpoints:

- Health check.
- Version check.
- Environment check.

Purpose:

- Confirm Django can run beside legacy.
- Confirm URL routing works.
- Confirm deployment can check Django health.

### Phase 3: Read-Only Public APIs

Migrate read-only APIs first:

- Home.
- Products list.
- Product detail.
- Product categories.
- Capabilities.

Purpose:

- Low business risk.
- Easy to compare with old output.
- No database write risk.

### Phase 4: Content APIs

Migrate:

- News list.
- News detail.
- Pages.
- Menus.
- Banners.

Purpose:

- These APIs affect public content but do not usually contain sensitive business transactions.

### Phase 5: Business Write APIs

Migrate:

- Contact requests.
- Quote requests.
- Newsletter subscription.

Purpose:

- These create important business records.
- Must include validation, transactions, spam protection, and logging.

### Phase 6: AI APIs

Migrate:

- AI chatbot.
- AI contact summary.
- AI quote analysis.
- AI content and SEO generation.
- AI translation.
- AI developer assistant.

Purpose:

- Keep AI service logic separate from controllers.
- Keep Ollama fallback behavior stable.
- Avoid blocking core website APIs if AI is slow.

### Phase 7: OpenAPI Documentation

Add Django-generated API documentation:

- OpenAPI schema.
- Swagger UI.
- API examples.

Purpose:

- Make frontend and external integration easier.
- Reduce confusion when both legacy and Django APIs exist.

### Phase 8: Admin CMS APIs

Migrate admin APIs after public APIs are stable.

Start with:

1. Admin products read.
2. Admin categories read.
3. Admin users read.
4. Admin contacts read.
5. Admin quotes read.

Then migrate write operations:

1. Create.
2. Update.
3. Delete.
4. Upload.

### Phase 9: Authentication And Permissions

Migrate:

- Login.
- Logout.
- Password reset.
- Change password.
- Change email.
- Lock and unlock user.
- Session management.
- Role and permission checks.

This phase is high risk and should happen after API and database behavior is well understood.

### Phase 10: Cutover

Switch selected traffic from legacy routes to Django routes.

Cutover should be route-by-route, not all at once.

## 8. Backward Compatibility Strategy

### Keep Old Routes Active

Legacy routes should continue working during migration.

Example:

```text
Old frontend -> /api/products -> legacy backend
New tests    -> /api/v1/catalog/products/ -> Django backend
```

### Preserve Response Shape

If the frontend expects:

```json
{
  "success": true,
  "data": []
}
```

Django should return the same structure unless the frontend is intentionally updated.

### Preserve Field Names

Avoid changing field names during migration.

Example:

```text
Keep: image
Do not suddenly rename to: thumbnail_url
```

Field renames should be a later frontend/API versioning decision.

### Preserve Status Meaning

If legacy uses product statuses:

```text
draft
published
archived
```

Django should use the same values at first.

### Add API Versioning

The first Django API version should be:

```text
/api/v1/
```

Later breaking changes can become:

```text
/api/v2/
```

## 9. Request And Response Compatibility Rules

Every migrated endpoint should be checked for:

- HTTP method.
- URL pattern.
- Query parameters.
- Request body fields.
- Required fields.
- Optional fields.
- Response field names.
- Response nesting.
- Empty result behavior.
- Error response behavior.
- Pagination behavior.
- Sorting behavior.
- Filtering behavior.
- File upload behavior.

## 10. Error Format Strategy

The legacy backend already has centralized error handling.

Django should eventually use a custom DRF exception handler so all API errors return a consistent format.

Recommended format:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": {}
  }
}
```

Important:

- Do not expose raw stack traces in production.
- Keep Vietnamese user-facing messages where needed.
- Keep machine-readable error codes for frontend logic.

## 11. Authentication Strategy

Authentication should not be migrated too early.

Recommended order:

1. Keep legacy admin session system active.
2. Build Django public read APIs without admin authentication.
3. Build Django admin read APIs behind a temporary controlled access layer.
4. Map legacy users and roles to Django-compatible permission design.
5. Add CSRF protection for admin write APIs.
6. Migrate login and session management after parity testing.

High-risk areas:

- Password hashing compatibility.
- Session expiration.
- Multiple device sessions.
- Account lock and unlock.
- Role and permission mapping.
- Password reset tokens.

## 12. File Upload API Strategy

Media and product image uploads are high risk because they touch both database and filesystem.

Migration should check:

- Upload directory.
- Public URL format.
- File size limit.
- Allowed extensions.
- Duplicate file names.
- Image preview URL.
- Delete behavior.
- Rename behavior.
- Security scanning strategy.

Recommended approach:

1. Keep legacy upload active first.
2. Add Django read-only media listing.
3. Add Django upload to a separate test folder.
4. Validate URLs and thumbnails.
5. Switch admin upload route only after testing.

## 13. AI API Strategy

AI endpoints should be migrated as service-backed APIs, not embedded directly in views.

Recommended future service groups:

- Chat service.
- Translation service.
- Content and SEO generation service.
- Contact summary service.
- Quote analysis service.
- PDF/catalogue reading service.
- Developer assistant service.

Compatibility requirements:

- If Ollama is unavailable, return a controlled fallback message.
- AI timeout should not freeze the whole website.
- Admin-only AI features must require authentication.
- AI prompts should not expose secrets or internal system data.

## 14. Testing Strategy

### Contract Tests

For each migrated endpoint:

1. Call legacy endpoint.
2. Call Django endpoint.
3. Compare response fields.
4. Compare important business values.

### Snapshot Tests

Use fixed sample data to compare stable JSON output.

### Integration Tests

Test important flows:

- Product list filtering.
- Product detail.
- Contact submit.
- Quote request submit.
- Admin user list.
- Media upload.
- Login and logout when auth migration begins.

### Error Tests

Test:

- Missing required fields.
- Invalid email.
- Invalid product ID.
- Unauthorized admin access.
- File too large.
- Unsupported file type.

## 15. API Risk Analysis

| Risk | Impact | Probability | Mitigation |
| --- | --- | --- | --- |
| Response format mismatch | Frontend breaks | High | Contract tests before cutover |
| Authentication mismatch | Admin access issues | High | Migrate auth late |
| Write endpoint data loss | Lost contacts or quotes | Medium | Backup and transaction checks |
| Upload path mismatch | Broken images | Medium | Separate media migration plan |
| Pagination mismatch | Admin tables confusing | Medium | Standardize query parameters |
| Validation mismatch | Forms fail unexpectedly | Medium | Match legacy required fields first |
| AI timeout | Slow admin tools | Medium | Add timeout and fallback response |
| OpenAPI drift | Bad integration docs | Low | Generate docs from Django routes |

## 16. Rollback Strategy

Rollback must be possible at endpoint level.

### Before Cutover

No rollback is needed because legacy still serves production traffic.

### During Cutover

If a Django endpoint fails:

1. Route traffic back to legacy endpoint.
2. Disable the Django route from proxy or frontend config.
3. Check error logs.
4. Compare request payload with legacy behavior.
5. Fix Django implementation later.

### For Write APIs

Before enabling Django write APIs:

- Backup database.
- Log request payload.
- Log created record ID.
- Use transactions.
- Validate record exists after write.

If write API causes issues:

- Stop Django write route.
- Return traffic to legacy route.
- Restore affected records from backup if needed.

## 17. Cutover Checklist

Before switching one API route to Django:

- Legacy endpoint behavior is documented.
- Django endpoint returns same required fields.
- Pagination behavior is tested.
- Filtering behavior is tested.
- Error behavior is tested.
- Permissions are tested.
- Logs are enabled.
- Rollback route is ready.
- Database backup exists for write endpoints.

## 18. OpenAPI And Swagger Plan

Django REST Framework should eventually expose API documentation.

Recommended endpoints:

```text
GET /api/v1/schema/
GET /api/v1/docs/
```

The documentation should include:

- Endpoint path.
- HTTP method.
- Request body.
- Query parameters.
- Response examples.
- Error examples.
- Authentication requirement.

Legacy documentation can remain available until migration is complete.

## 19. API Migration Exit Criteria

Phase 1 API planning is complete when:

- Existing API groups are listed.
- New Django endpoint namespace is proposed.
- Backward compatibility strategy is documented.
- Risk and rollback strategy are documented.
- No code has been changed.

Future API implementation should not start until these reports are reviewed.

## 20. Recommended Next Step

Step 2: Analyze existing database schema and convert legacy models to Django ORM models.

## 21. Phase 1 Review Update - API Version Strategy

Recommended Django API namespace:

```text
/api/v1/
```

Example migration:

```text
Legacy:
GET /api/products

New:
GET /api/v1/products
```

Important decision:

- `/api/v1/` should be the stable Django API contract.
- The old `/api/...` routes should remain available during migration.
- Breaking changes should not be introduced into `/api/v1/` after frontend integration starts.
- Future breaking changes should use `/api/v2/`.

Preferred public API naming:

| Area | Recommended Endpoint Pattern |
|---|---|
| Health | `/api/v1/health/` |
| Products | `/api/v1/products/` |
| Categories | `/api/v1/product-categories/` |
| Capabilities | `/api/v1/capabilities/` |
| News | `/api/v1/news/` |
| Contact | `/api/v1/contacts/` |
| Quote requests | `/api/v1/quote-requests/` |
| AI | `/api/v1/ai/...` |

More nested variants such as `/api/v1/catalog/products/` can still be used internally or later, but `/api/v1/products/` is easier for compatibility with the current frontend mental model.

## 22. Phase 1 Review Update - Compatibility Strategy

Compatibility rules:

- Keep old API working.
- Add Django API beside legacy API.
- Do not remove old routes until route parity is proven.
- Use an adapter layer if Django internal serializers differ from legacy response shape.
- Preserve response field names that the frontend already uses.
- Preserve HTTP status behavior where possible.
- Preserve pagination/search/filter query parameters where possible.
- Preserve Vietnamese user-facing messages where the current UI expects them.

Adapter layer purpose:

```text
Django ORM/service output
  -> Compatibility adapter
  -> Legacy-shaped JSON response
  -> Existing frontend can still read it
```

The adapter layer prevents internal Django model naming from leaking into the public API too early.

Example:

```text
Internal Django field: thumbnail_url
Legacy/frontend field: image
Adapter returns: image
```

## 23. Phase 1 Review Update - API Migration Method

Each endpoint should move through these steps:

1. Document old endpoint behavior.
2. Create Django endpoint under `/api/v1/`.
3. Keep old endpoint active.
4. Compare old response and new response.
5. Add contract tests.
6. Switch frontend or proxy only after validation.
7. Keep rollback route to legacy.

For write APIs:

1. Backup database first.
2. Validate request fields.
3. Use transaction.
4. Match legacy side effects.
5. Test rollback on failure.

## 24. Phase 1 Review Update - Endpoint Migration Matrix

| Old Endpoint | New Endpoint | Method | Affected Module | Breaking Change Risk | Notes |
|---|---|---|---|---|---|
| `/api/health` | `/api/v1/health/` | GET | Foundation/Core | Low | First safe Django endpoint |
| `/api/version` | `/api/v1/version/` | GET | Foundation/Core | Low | Include app/env/version information |
| `/api/home` | `/api/v1/home/` | GET | Public/Home | Medium | Aggregates product/news/settings/banner data |
| `/api/products` | `/api/v1/products/` | GET | Catalog | High | Must preserve search/category/status/sort/pagination behavior |
| `/api/products` | `/api/v1/products/` | POST | Catalog/Admin | High | Write migration later; requires auth/permission/validation |
| `/api/products/{id}` | `/api/v1/products/{id}/` | GET | Catalog | High | Must preserve detail, specs, gallery, related products |
| `/api/products/{id}` | `/api/v1/products/{id}/` | PUT | Catalog/Admin | High | Write migration later |
| `/api/products/{id}` | `/api/v1/products/{id}/` | DELETE | Catalog/Admin | High | Requires delete confirmation/audit/rollback strategy |
| `/api/product-categories` | `/api/v1/product-categories/` | GET | Catalog | Medium | Category names/slugs must match |
| `/api/capabilities` | `/api/v1/capabilities/` | GET | Catalog/Manufacturing | Medium | Depends on machines/processes relationship |
| `/api/news` | `/api/v1/news/` | GET | Content | Medium | Must preserve category/tag/publish status |
| `/api/contact` | `/api/v1/contacts/` | POST | CRM | High | Business lead write; requires validation and spam/security review |
| `/api/quote-request` | `/api/v1/quote-requests/` | POST | Sales | High | Multi-table write with quote items/files |
| `/api/ai/chat` | `/api/v1/ai/chat/` | POST | AI | Medium | Preserve Ollama fallback and timeout behavior |
| `/api/ai/content-seo` | `/api/v1/ai/content-seo/` | POST | AI/Admin | Medium/High | Admin-only, should suggest not auto-publish |
| `/api/ai/translate` | `/api/v1/ai/translate/` | POST | AI/Localization | Medium | Needs cache and fallback behavior |
| `/api/openapi.json` | `/api/v1/schema/` | GET | Developer/API Docs | Low | Django-generated schema later |
| `/api/docs` | `/api/v1/docs/` | GET | Developer/API Docs | Low | Swagger/Redoc |
| `/api/aws-demo` | `/api/v1/integrations/aws-demo/` | GET | Integration Demo | Low/Medium | Demo only; do not block core migration |

## 25. Phase 1 Review Update - Admin API Compatibility

Admin migration should not start by replacing HTML pages directly.

Recommended method:

1. Keep legacy admin pages active.
2. Add Django JSON APIs for read-only admin data.
3. Connect admin UI to Django only after permissions are ready.
4. Move write APIs after CSRF, permissions, validation, file upload, and audit logs are validated.

High-risk admin API areas:

- users
- roles/permissions
- product save/delete
- media upload/delete
- quote status updates
- settings save
- developer tools

## 26. Phase 1 Review Update - API Compatibility Layer Dependency

The API compatibility layer depends on:

- `core` for common response/error format.
- database mapping for field names and status values.
- module services for business behavior.
- serializers/adapters for legacy response shape.
- tests for legacy-vs-Django parity.

No module should expose a new Django response shape to the existing frontend until compatibility is reviewed.
