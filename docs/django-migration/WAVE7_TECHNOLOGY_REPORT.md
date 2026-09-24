# Wave 7 Technology Report

## Route

`GET /technology`

## Implemented Content

- Technology introduction.
- Drawing review step.
- Machining plan step.
- Quality control step.
- Capability cards.

## Data Source

The page reads capability content through `CatalogService`.

If legacy read-only capability data is not available, the page uses static Django fallback content.

## Result

Django now renders the public technology page.
