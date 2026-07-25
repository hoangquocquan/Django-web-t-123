# Git Workflow

## Branch

### main

Production stable.

Only stable, reviewed, production-ready code should be merged into this branch.

### develop

Integration branch.

Migration work should be integrated and tested here before it is considered stable.

### migration/*

Migration work branches.

Each migration branch should focus on one phase or one module. Do not mix unrelated changes.

Examples:

```text
migration/phase-0-audit
migration/phase-1-planning
migration/phase-2-django-foundation
migration/product-module
migration/customer-module
migration/quotation-module
```

## Commit Convention

Use short, clear commit prefixes.

### docs

Documentation changes.

Example:

```text
docs: add migration audit report
```

### feat

New feature.

Example:

```text
feat: create django product model
```

### fix

Bug fix.

Example:

```text
fix: handle empty product category
```

### refactor

Code restructuring without changing behavior.

Example:

```text
refactor: split product repository query builder
```

### test

Tests.

Example:

```text
test: add product repository unit tests
```

### chore

Project setup, tooling, or maintenance.

Example:

```text
chore: initialize migration git workflow
```

## Migration Rules

- Do not migrate multiple business modules in one branch.
- Do not merge migration branches automatically.
- Do not push to remote until the local migration step is reviewed.
- Keep legacy code unchanged unless the phase explicitly allows changes.
- Create a rollback note before changing database write behavior.
- Keep migration reports inside `docs/migration/`.
- Keep review reports inside `docs/reviews/`.

## Recommended Flow

1. Start from `develop`.
2. Create a focused migration branch.
3. Make changes for only one phase or one module.
4. Run checks and tests.
5. Write a review note in `docs/reviews/`.
6. Review manually.
7. Merge only after approval.
