# Phase 4C — Quotation and Order Conversion Command API Report

## Final verdict

`READY_FOR_PHASE_4D`

The authenticated canonical quotation lifecycle and accepted-quotation order
conversion commands are implemented and validated on SQLite and PostgreSQL 16.
No frontend, progress-command, worker, webhook, AI, deployment, or legacy API
work was included.

## Project isolation and baseline

- Working directory: `C:\Users\hoang\Documents\ChatGPT\WEB Ô TÔ DJANGO`
- Git root: `C:/Users/hoang/Documents/ChatGPT/WEB Ô TÔ DJANGO`
- Repository: `Django-web-t-123`
- Branch: `codex/demo-database-validation`
- Baseline HEAD: `b6a97637b298759eb4a3c74938d00ed278047370`
- Baseline subject: `phase4b: add master data and RFQ command APIs`
- Remote: `https://github.com/hoangquocquan/Django-web-t-123.git`
- Initial worktree: clean.
- Required backend/frontend directories and Phase 4A/4B reports existed.

AI FACTORY, n8n, Zalo, 9Router, Codex Bridge, their runtime files, and their
reserved ports were not read, inspected, started, stopped, or modified. No Git
commit, push, merge, rebase, branch change, deployment, reset, stash, or amend
was performed.

## Architecture and implementation

The existing canonical response envelope, bearer authentication, exact
permission boundary, serializers, views, URL namespace, Phase 3C quotation
domain, and Phase 3D conversion operation are reused.

- Strict serializers reject unknown/protected fields and JSON floating-point
  money inputs.
- Views contain only request validation, service dispatch, and canonical
  serialization.
- `QuotationCommandService` owns authorization, ownership, idempotency,
  transaction, and audit orchestration.
- Phase 3C domain functions remain authoritative for revision allocation,
  totals, submission, approval, send, and customer decisions.
- Phase 3D `convert_accepted_quotation` remains the only order creation path.
- PostgreSQL quotation locks use `FOR UPDATE OF` on the quotation row while the
  RFQ family row is locked separately; this avoids locking the nullable side of
  an outer join and preserves family-level serialization.

## Endpoint inventory

All routes are under `/api/v1/canonical/` and accept authenticated `POST` only.

| Route | Command |
| --- | --- |
| `rfqs/{rfq_id}/quotations/commands/create/` | Create initial revision |
| `quotations/{id}/commands/create-revision/` | Create revision after rejection |
| `quotations/{id}/commands/update/` | Recalculate editable draft |
| `quotations/{id}/commands/archive/` | Retire eligible draft |
| `quotations/{id}/commands/submit/` | Submit for approval |
| `quotations/{id}/commands/approve/` | Manager approval |
| `quotations/{id}/commands/reject/` | Manager rejection with reason |
| `quotations/{id}/commands/send/` | Record customer send evidence |
| `quotations/{id}/commands/accept/` | Record customer acceptance |
| `quotations/{id}/commands/decline/` | Record customer decline with reason |
| `quotations/{id}/commands/convert-to-order/` | Convert accepted quote once |

No arbitrary Sales Order creation endpoint was added.

## Permission and ownership matrix

Every command requires an active user, active role, exact command permission,
and exact `quotation:view`; conversion also requires exact `order:view`.
Wildcard grants never satisfy an exact check.

| Capability | Admin | Sales | Manager |
| --- | --- | --- | --- |
| Create/revise/change/submit/send/customer decision/convert | Domain-eligible | Owned or assigned only | Denied |
| Archive eligible draft | Allowed | Owned or assigned only | Denied |
| Approve/reject | Denied | Denied | Allowed, maker-checker enforced |

Sales ownership accepts quotation creator, RFQ creator, or RFQ assignee.
Unassigned, inactive, wildcard-only, missing-permission, and unrelated roles
fail closed. Admin cannot substitute for Manager approval/rejection. A Manager
cannot decide a quotation they created.

## State, revision, money, idempotency, and audit

| Command | Required state | Result |
| --- | --- | --- |
| Create | RFQ `READY_TO_QUOTE`, no revision | `DRAFT` R0 |
| Revise | Latest revision `REJECTED` | prior `SUPERSEDED`, new `DRAFT` Rn+1 |
| Update | `DRAFT` | backend-recalculated `DRAFT` |
| Archive | `DRAFT` | `SUPERSEDED` terminal history row |
| Submit | `DRAFT` | `PENDING_APPROVAL` |
| Approve/reject | `PENDING_APPROVAL` | `APPROVED` / `REJECTED` |
| Send | `APPROVED` and currently valid | `SENT` |
| Accept/decline | `SENT` | `ACCEPTED` / `DECLINED` |
| Convert | valid `ACCEPTED` with evidence | one `CONFIRMED` Sales Order |

Archive maps an eligible draft to the existing terminal `SUPERSEDED` state so
history is preserved without inventing a competing workflow state. The model
transition map now permits only `DRAFT -> SUPERSEDED` for this operation.

Revision family numbering, revision allocation, effective-revision uniqueness,
and conversion uniqueness use the existing database constraints and locks.
Submitted commercial fields and lines remain immutable.

All money uses `Decimal` and `ROUND_HALF_UP`. Settlement quantum is `1` for VND
and `0.01` for USD, with four-decimal storage. Backend calculations remain
authoritative; subtotal, total, revision, creator, state, timestamps, audit, and
order linkage cannot be mass assigned.

Quotation creation/revision and order conversion require `Idempotency-Key`.
Request hashes are scoped to actor, command, target, and normalized payload.
Same key/payload replays the original object; changed payload conflicts; failed
transactions persist neither success state nor an idempotency record. Raw keys
and internal hashes are not serialized.

Business transitions and append-only audit events share one outer database
transaction. Implemented actions are `quotation.created`,
`quotation.revision_created`, `quotation.superseded`, `quotation.submitted`,
`quotation.approved`, `quotation.rejected`, `quotation.sent`,
`quotation.customer_accepted`, `quotation.customer_declined`, and the existing
`order.converted`. Audit metadata contains only bounded IDs, numbers, counts,
booleans, or status evidence; contact details, credentials, tokens, raw evidence,
and idempotency hashes are excluded.

## Migration and compatibility fixture correction

Migration `foundation.0010_phase4c_role_activity_and_quotation_archive` is
necessary because the baseline schema had no role activity flag and no exact
`quotation:archive` permission. It adds indexed `FoundationRole.is_active` with
a compatibility-safe default of `True`, defines the permission with collision
checking, and grants it only to existing Admin and Sales roles. Its reverse
operation removes only the marked Phase 4C grants/permission before removing
the new field. No sales/order schema or legacy unmanaged table changed.

The full-suite failure initially reproduced a pre-existing test-isolation gap:
Phase 3B/3C/3D migration-boundary tests left the shared test database at a
historical migration leaf. The autouse fixture added to `django_backend/conftest.py`
restores current leaf migrations only after those three migration modules. It
does not alter application code, seed data, RBAC assertions, or production
runtime. The migration-boundary group passed independently (`25 passed, 3
skipped`) and the subsequent full SQLite suite passed, proving order independence.

## Validation results

Static/framework validation:

| Command | Result |
| --- | --- |
| `python manage.py check` | Passed; 0 issues |
| `python manage.py makemigrations --check --dry-run` | Passed; no changes |
| `python -m compileall -q ...` | Passed |
| `git diff --check` | Passed; only line-ending notices |

SQLite suites:

| Suite | Passed | Failed | Errors | Skipped |
| --- | ---: | ---: | ---: | ---: |
| Phase 4C focused | 15 | 0 | 0 | 3 |
| Phase 4B preservation | 17 | 0 | 0 | 1 |
| Phase 4A preservation | 16 | 0 | 0 | 0 |
| Phase 3C preservation | 14 | 0 | 0 | 1 |
| Phase 3D preservation | 11 | 0 | 0 | 1 |
| Phase 3 migration boundaries + Phase 4C | 25 | 0 | 0 | 3 |
| Full backend | 204 | 0 | 0 | 147 |

PostgreSQL commands used `--ds=config.settings.development` and a redacted
task-local `DATABASE_URL` targeting `127.0.0.1:55438`. Each pytest invocation
created and destroyed its own isolated test database.

| Suite | Passed | Failed | Errors | Skipped |
| --- | ---: | ---: | ---: | ---: |
| Phase 4C focused, including three concurrency tests | 18 | 0 | 0 | 0 |
| Phase 4B preservation | 18 | 0 | 0 | 0 |
| Phase 4A preservation | 16 | 0 | 0 | 0 |
| Phase 3B models + RFQ + migration boundary | 26 | 0 | 0 | 1 |
| Phase 3C domain + migration boundary | 18 | 0 | 0 | 0 |
| Phase 3D domain + migration boundary | 15 | 0 | 0 | 0 |
| Full backend | 210 | 0 | 0 | 141 |

PostgreSQL concurrency results:

- Two identical quotation-creation contenders returned one authoritative row,
  one replay, and one `quotation.created` audit event.
- Two new-revision contenders produced exactly revisions R0/R1, one active R1,
  one superseded R0, and one revision-created audit event.
- Two accepted-quotation conversion contenders returned one Sales Order, one
  replay, and one `order.converted` audit event.
- Forced audit failures rolled back state, business-number allocation, audit,
  and idempotency; retry then succeeded without partial rows.
- Duplicate conversion, wrong state, missing key, changed idempotent payload,
  invalid totals, and illegal transitions were rejected.

## Docker and PostgreSQL isolation

- Docker Client/Server: `29.4.3` / `29.4.3`.
- PostgreSQL: `16.14 (Debian 16.14-1.pgdg13+1)`.
- Port `55438` was free before creation and after cleanup.
- Container: `django-phase4c-postgres16-20260913-b6a97637`.
- Full container ID:
  `9a054b7719e9429d9e0c73fb1d8d24c557b141bc5509d58082db71d2088ede96`.
- Image: `postgres:16`; created `2026-09-13T04:27:45.522181433Z`.
- Mapping: `127.0.0.1:55438 -> 5432/tcp`.
- Network: `django-phase4c-net-20260913-b6a97637`, ID
  `83625bd9f5d4bed0309a6655c13f5d9ac5acfb63e237b14e7742276a68b822ae`.
- Volume: `django-phase4c-pg16-data-20260913-b6a97637`, mounted only at
  `/var/lib/postgresql/data`.
- Labels: task `phase4c-quotation-order-validation`, owner
  `Django-web-t-123`, baseline full SHA above.
- Task-local database credentials were not stored in source or this report.

Cleanup removed only the exact task-owned container, network, and volume.
Exact-name inspections returned not found, the Phase 4C label query returned no
containers, and port `55438` was free. There were 14 unrelated container IDs
before and 14 after. External container ID churn occurred during validation;
no command in this task targeted, inspected internally, or mutated those
resources, and the protected services were not investigated further.

## Changed files and SHA-256

| Path | SHA-256 |
| --- | --- |
| `django_backend/apps/api/canonical_permissions.py` | `5a5a7e8b4676f392ecd6b226667bfc733abead47d3570baa406a16027772b01a` |
| `django_backend/apps/api/canonical_urls.py` | `61086c3847991f02605ac002a481837ad9ed8b49a2fafde70db4231f5a7980eb` |
| `django_backend/apps/api/serializers/canonical_commands.py` | `b5bae17e47d55e65930ce6128fe66a55406086b5d6193acda7ad04a59562d175` |
| `django_backend/apps/api/services/canonical_command_service.py` | `9f74fc611da3f60620fc26b779d981b5d8d16dc51feec280e00f714bd6f8c3d9` |
| `django_backend/apps/api/views/canonical_commands.py` | `cd542b2b352d7d37330d1a077788628d998147b01ce4eba8434e6dcdf0617cbe` |
| `django_backend/apps/api/tests/test_phase4c_quotation_order_commands.py` | `0cb97c1f196f8c32e47b1de08cd15708e8a291537e81adb3edc71f88ff7d2730` |
| `django_backend/apps/foundation/models.py` | `f29d3d9ef97924be86ee621d98e00839e2e818216fb73f28df36622c00ee8a4e` |
| `django_backend/apps/foundation/migrations/0010_phase4c_role_activity_and_quotation_archive.py` | `dc56d3a48f83ee6dde5a69450f042d8024e9517888693ecdad7da347327b369b` |
| `django_backend/apps/sales/models.py` | `fa1c0e6ae0eaae4fd15ead67fea281e392ff856d41f89f1a9ad8b0ac0f6d4c1b` |
| `django_backend/apps/sales/quotation_domain.py` | `9ad2aa33abe6e11c8e7a384de9542b7ef7f8f6f1e654851532601921062c1e5c` |
| `django_backend/conftest.py` | `43cec3510fb1f9d102cba41f19e8e91a72c94988153351aeca8e6d922700a1c0` |

The report is the twelfth changed path. Its final digest is reported in the
terminal handoff rather than embedded in itself, because a file cannot contain
its own stable SHA-256.

Tracked `git diff --stat` before this report was added:

```text
 django_backend/apps/api/canonical_permissions.py   |  15 +-
 django_backend/apps/api/canonical_urls.py          |  66 ++++
 .../apps/api/serializers/canonical_commands.py     | 107 ++++++
 .../apps/api/services/canonical_command_service.py | 379 ++++++++++++++++++++–
 .../apps/api/views/canonical_commands.py           | 184 ++++++++++
 django_backend/apps/foundation/models.py           |   1 +
 django_backend/apps/sales/models.py                |   2 +-
 django_backend/apps/sales/quotation_domain.py      | 119 +++++++
 django_backend/conftest.py                         |  18 +
 9 files changed, 885 insertions(+), 6 deletions(-)
```

Complete Phase 4C worktree paths are the eleven manifest paths above plus
`PHASE_4C_QUOTATION_ORDER_CONVERSION_COMMAND_API_IMPLEMENTATION_REPORT.md`.
There are no unrelated worktree paths.

Final `git status --short`:

```text
 M django_backend/apps/api/canonical_permissions.py
 M django_backend/apps/api/canonical_urls.py
 M django_backend/apps/api/serializers/canonical_commands.py
 M django_backend/apps/api/services/canonical_command_service.py
 M django_backend/apps/api/views/canonical_commands.py
 M django_backend/apps/foundation/models.py
 M django_backend/apps/sales/models.py
 M django_backend/apps/sales/quotation_domain.py
 M django_backend/conftest.py
?? PHASE_4C_QUOTATION_ORDER_CONVERSION_COMMAND_API_IMPLEMENTATION_REPORT.md
?? django_backend/apps/api/tests/test_phase4c_quotation_order_commands.py
?? django_backend/apps/foundation/migrations/0010_phase4c_role_activity_and_quotation_archive.py
```

## Remaining blockers

None. Phase 4C changes remain uncommitted in the worktree for Owner review and
separate checkpoint creation.
