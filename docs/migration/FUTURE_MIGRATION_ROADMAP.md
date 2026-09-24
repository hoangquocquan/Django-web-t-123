# Future Migration Roadmap

## Current

Phase 9.3 Migration Readiness Validation is completed.

The project is conditionally ready for Phase 10 planning. It is not approved for
live database ownership migration until schema, backup, restore, validation,
rollback and security gates are reviewed.

## Future

### Phase 10 - Database Ownership

Move Django from read-only legacy database consumer to database owner. This
phase family covers PostgreSQL schema design, dry-run migration, reconciliation
and production database cutover.

### Phase 11 - Legacy Shutdown

Remove dependency on the legacy Python backend only after Django owns the
application behavior and database safely.

### Phase 12 - Production Hardening

Prepare enterprise operations with performance tuning, security hardening,
monitoring, alerts, backup verification and disaster recovery.

### Phase 13 - Django Modernization

Remove migration compromises and optimize the application as a native Django
system after legacy constraints are gone.

## Prompt Library

Future execution prompts live in:

```text
docs/codex-prompts/
```

Each future phase prompt is self-contained and can be provided to Codex
independently when the architecture reviewer approves that phase.
