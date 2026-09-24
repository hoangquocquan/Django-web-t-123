# Migration Phase Versioning Rules

## Major Phase

Format:

```text
Phase X
```

Used for:

- new module migration
- architecture milestone
- new business capability migration
- major technical boundary

Example:

```text
Phase 5
CRM Migration
```

## Minor Phase

Format:

```text
Phase X.Y
```

Used for:

- fixing architecture issues
- solving migration blockers
- additional preparation
- correcting mapping assumptions
- hardening review feedback

Example:

```text
Phase 5.1
CRM Data Mapping Correction
```

## Rules

- Never rewrite completed phases.
- Always create a new minor phase for corrections.
- Preserve migration history.
- Every phase must have its own branch.
- Every phase must have a checkpoint commit.
- Every phase must have a review package.
- Every phase must stop for review before the next phase starts.

## Examples

Completed:

```text
Phase 3
Database Mapping
```

Issue discovered:

```text
Phase 3.1
Database Mapping Hardening
```

Additional blocker discovered:

```text
Phase 3.2
ORM Readiness
```
