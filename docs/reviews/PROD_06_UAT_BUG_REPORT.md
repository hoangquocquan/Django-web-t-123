# PROD-06 UAT Bug Report

## Corrected

`GET /api/v1/crm/customers/` returned HTTP 500 in the production container
because an unauthenticated compatibility branch attempted to read the retired
legacy SQLite database, which is intentionally absent from the production image.

The production/staging boundary now fails closed with HTTP 403 before querying
legacy storage. Development/test compatibility remains unchanged. Focused tests,
container rebuild, runtime probe and the 140-request load smoke all passed after
the correction.

## Open Bugs

None found by the executed PROD-06 UAT suite.
