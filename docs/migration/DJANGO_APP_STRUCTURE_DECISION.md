# Django App Structure Decision

Phase: 3.2 - ORM Implementation Readiness & Legacy Database Integration Design  
Rule: Documentation only. No app restructuring or model files are created in this phase.

## 1. Decision Question

How should catalog ORM models be organized in Django?

## 2. Option A - Single Catalog App

Structure:

```text
apps/
  catalog/
    models.py
    repositories/
    services/
    tests/
```

Advantages:

- Simple to start.
- Easy imports.
- Good fit for current Phase 4A size.
- Fewer Django app registration concerns.
- Keeps catalog concepts together.

Disadvantages:

- `models.py` can grow large.
- Future split may be needed if catalog becomes very complex.

## 3. Option B - Nested Catalog Modules

Structure:

```text
apps/
  catalog/
    products/
    categories/
    materials/
    machines/
    processes/
```

Advantages:

- Strong separation.
- Scales better for very large domains.
- Smaller files per concept.

Disadvantages:

- More boilerplate.
- More app/import complexity.
- More decisions before first ORM validation.
- Risk of over-engineering before model parity is proven.

## 4. Recommendation

Recommended for Phase 4:

```text
Option A - Single catalog app, with internal modules when needed.
```

Suggested future-friendly structure:

```text
apps/catalog/
  __init__.py
  apps.py
  models.py
  repositories/
  services/
  tests/
```

If `models.py` becomes too large later, it can be split into a models package:

```text
apps/catalog/models/
  __init__.py
  products.py
  reference.py
  relationships.py
```

## 5. Reasoning

Current size:

- Catalog has around 11 tables in Phase 4A.
- Most are tightly related.
- The first goal is read parity, not perfect domain decomposition.

Future growth:

- Products, materials, machines, processes, and capabilities may grow.
- Internal repositories/services can split behavior without creating many Django apps.

Maintainability:

- One app is easier to register and test for Phase 4.
- Internal folder organization can still keep code readable.

## 6. Boundary Rules

The catalog app should not contain:

- CRM/customer models,
- quote/sales models,
- CMS/news models,
- media storage migration logic,
- authentication/session logic,
- AI service logic.

## 7. Decision

Final Phase 3.2 recommendation:

```text
Use a single `apps.catalog` Django app for Phase 4A.
Keep code internally organized with repositories/services/tests.
Do not create nested Django apps until complexity proves it is needed.
```
