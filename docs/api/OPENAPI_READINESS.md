# OpenAPI Readiness

## Goal

Prepare the API layer for future Swagger/OpenAPI documentation without adding
new packages in Phase 9.2.

## Serializer Coverage

Current serializer helper coverage:

- Catalog products, images, categories, materials
- CRM customers, notes, contact requests
- Sales quote headers, items, files
- CMS pages and nested menu items
- Auth preparation profile

## Schema Requirements

Future OpenAPI integration should describe:

- common success envelope
- common error envelope
- pagination schema
- endpoint parameters such as `limit`, `offset`, `location`, `role`, `admin_id`
- 403 read-only enforcement
- 404 not found response
- 400 invalid pagination response

## Documentation Gaps

- No generated schema yet.
- Serializer helpers are not DRF `Serializer` classes yet.
- No examples exported to machine-readable YAML/JSON yet.
- Real auth requirement is documented but not enforced as a production gate.

## Future Swagger Integration Plan

1. Select approved package, such as `drf-spectacular`, in a future phase.
2. Convert serializer helpers or wrap them with explicit DRF serializers.
3. Add schema views under an internal route.
4. Protect Swagger UI behind admin/auth boundary.
5. Add schema generation test in CI.

No package installation is performed in Phase 9.2.
