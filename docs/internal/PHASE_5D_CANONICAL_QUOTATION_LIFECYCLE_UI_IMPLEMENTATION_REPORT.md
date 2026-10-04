# Phase 5D — Canonical Quotation Lifecycle UI Implementation Report

## Verdict

`READY_FOR_PHASE_5D_REVIEW`

## Repository baseline and safety

- Repository root: `C:\Users\hoang\Documents\ChatGPT\WEB Ô TÔ DJANGO`
- Repository: `Django-web-t-123`
- Branch: `codex/demo-database-validation`
- Starting and current HEAD: `7de1a79a3b61f3350cda4fdbee5b9b5e865e3b47`
- Baseline subject: `phase5c: add RFQ draft line and submission UI`
- The repository was clean before Phase 5D implementation began.
- The two pre-existing report-only paths were verified, moved with literal paths to `C:\Users\hoang\Documents\ChatGPT\DJANGO_PROJECT_REPORTS`, and re-hashed successfully before implementation.
- No file was staged or committed. No branch switch, push, merge, rebase, deployment, Docker, or PostgreSQL command was performed.

## Read-only contract discovery

The implementation was based on a fresh inspection of the Phase 4A, 4C, 5A, 5B, and 5C reports plus the current canonical URL, serializer, view, permission, read-service, command-service, and quotation-domain code. No contract was inferred from the previously blocked Phase 5D run.

The authoritative lifecycle discovered and implemented is:

`READY_TO_QUOTE RFQ -> DRAFT R0 -> PENDING_APPROVAL -> APPROVED or REJECTED -> SENT -> ACCEPTED or DECLINED`

A latest `REJECTED` quotation can create a new `DRAFT` revision while superseding the rejected revision. A `DRAFT` can also be archived to `SUPERSEDED`.

## Canonical endpoint and permission matrix

All read collections are bounded and use canonical `/api/v1/` paths through the existing canonical client.

| Capability | Canonical endpoint | UI permission/lifecycle rule |
| --- | --- | --- |
| List families | `GET quotation-families/?limit=20&ordering=quotation_family_number` | Admin, Sales, Manager with `quotation:view` |
| Family detail | `GET quotation-families/{id}/` | Admin, Sales, Manager with `quotation:view` |
| Family revisions | `GET quotation-families/{id}/revisions/?limit=100&ordering=revision` | Admin, Sales, Manager with `quotation:view` |
| List quotations | `GET quotations/?data_contract=MVP_V1&limit=20&ordering=-created_at` | Admin, Sales, Manager with `quotation:view` |
| Quotation detail | `GET quotations/{id}/` | Admin, Sales, Manager with `quotation:view` |
| Lines | `GET quotations/{id}/lines/?limit=100&ordering=line_number` | Admin, Sales, Manager with `quotation:view` |
| Approval decisions | `GET quotations/{id}/approval-decisions/?limit=100&ordering=decided_at` | Admin, Sales, Manager with `quotation:view` |
| Customer decisions | `GET quotations/{id}/customer-decisions/?limit=100&ordering=decided_at` | Admin, Sales, Manager with `quotation:view` |
| Create R0 | `POST rfqs/{rfq_id}/quotations/commands/create/` | Admin or Sales owner/assignee; RFQ `READY_TO_QUOTE`; idempotency key required |
| Create revision | `POST quotations/{id}/commands/create-revision/` | Admin or Sales owner; latest quotation `REJECTED`; idempotency key required |
| Update commercial draft | `POST quotations/{id}/commands/update/` | Admin or Sales owner; `DRAFT` |
| Archive draft | `POST quotations/{id}/commands/archive/` | Admin or Sales owner; `DRAFT` |
| Submit | `POST quotations/{id}/commands/submit/` | Admin or Sales owner; `DRAFT` |
| Approve | `POST quotations/{id}/commands/approve/` | Manager only; maker-checker enforced; `PENDING_APPROVAL` |
| Reject | `POST quotations/{id}/commands/reject/` | Manager only; maker-checker enforced; `PENDING_APPROVAL`; reason required |
| Send | `POST quotations/{id}/commands/send/` | Admin or Sales owner; `APPROVED`; recipient and evidence required |
| Accept | `POST quotations/{id}/commands/accept/` | Admin or Sales owner; `SENT`; contact snapshot and evidence required |
| Decline | `POST quotations/{id}/commands/decline/` | Admin or Sales owner; `SENT`; contact snapshot, evidence, and reason required |

Quotation-to-order conversion remains explicitly excluded.

## Implemented UI and command behavior

- Added a quotation lifecycle workspace under the existing `sales-quotes` route while keeping both RFQ and quotation workspaces mounted so tab switching preserves state.
- Added canonical family and quotation indexes, family revision history, detail, line, approval-decision, and customer-decision views.
- Added eligible `READY_TO_QUOTE` RFQ selection and R0 commercial quotation creation from authoritative RFQ lines.
- Added DRAFT commercial editing, archiving, and submission.
- Added rejected-revision creation, Manager approve/reject actions, approved quotation sending, and sent quotation accept/decline actions.
- Displays backend-authoritative totals, commercial line data, approval history, and sanitized customer evidence.
- Reconciles successful commands with authoritative backend reads rather than treating the command response as final UI state.
- Uses independent bounded request cancellation and generation guards for quotation index, workspace, and RFQ-line reads to prevent stale writes; tab deactivation also settles a pending presentation state so an invalidated callback cannot leave the UI permanently locked.
- Maps authentication, permission, ownership, maker-checker, lifecycle, validation, conflict, timeout, network, malformed-protocol, and server outcomes to deterministic sanitized UI states.

## Idempotency and ambiguous outcomes

- Initial R0 creation and rejected-revision creation use opaque idempotency keys.
- A logical create attempt retains a defensive copy of its original target, payload, idempotency key, and any created quotation identity.
- Ambiguous transport, timeout, cancellation, protocol, or server outcomes preserve the attempt for safe retry/reconciliation.
- Once a created quotation identity is known, retry performs authoritative reconciliation and does not issue a duplicate POST.
- Every input belonging to the retained logical payload is locked while an active create attempt exists, preventing UI/payload divergence.
- Definitive completion clears the retained attempt so a later logical create receives a new key.

## Regression coverage added

`figma_make_frontend/src/api/phase5d.test.ts` adds 22 focused tests covering:

- bounded canonical read paths and exact command endpoints;
- exact payload allowlists, string decimals including the backend `max_digits=20` and `decimal_places=4` bounds, reasons, and evidence requirements;
- distinct strict approve and reject serializer boundaries before transport;
- retained idempotency key, target, payload, and created identity;
- ambiguity-safe retry and reconciliation without duplicate POST;
- active-attempt locking for every retained-payload field;
- Sales/Admin versus Manager lifecycle boundaries;
- ownership and maker-checker error handling;
- stale-response and cancellation guards;
- release of pending UI state when tab deactivation aborts and invalidates obsolete callbacks;
- authoritative post-command reconciliation;
- absence of legacy endpoints, conversion, persistence, key rendering, logging, and mock quotation data;
- integration with the existing Phase 5A, 5B, and 5C suites.

## Exact changed paths and SHA256

| Path | SHA256 |
| --- | --- |
| `figma_make_frontend/package.json` | `4B008C83641BAE1D7C0D58F30B304B3CEFCEEE06CF20BC8AAC3CC934C652DAF7` |
| `figma_make_frontend/src/App.tsx` | `295018F11BFB31FBE3FA2BC9BB14C7C0BF543B34F91374BB6E93416C85F171BD` |
| `figma_make_frontend/src/api/phase5d.test.ts` | `4EF4A89EB9CE86F796B5E951E5521E099BBFEFAE66F838A5B2BA535F4F0CF0D8` |
| `figma_make_frontend/src/api/quotationCommands.ts` | `D7977A470A7F7F13AB897D996FB1B36D6EF003A4CD36C962DC8DD7371A0303DC` |
| `figma_make_frontend/src/components/QuotationWorkspace.tsx` | `85652DE27F37582E024A95D663E3B9BA6089F6FD1836F743135CBB313B9B5744` |
| `PHASE_5D_CANONICAL_QUOTATION_LIFECYCLE_UI_IMPLEMENTATION_REPORT.md` | Compute after final report creation; reported in the terminal response. |

No backend, migration, API-contract, dependency, lockfile, Docker, PostgreSQL, AI FACTORY, n8n, Zalo, 9Router, Codex Bridge, or other screen file was changed.

## Validation results

| Command | Result |
| --- | --- |
| `pnpm --dir figma_make_frontend run typecheck` | PASS |
| `pnpm --dir figma_make_frontend run typecheck:phase5a` | PASS |
| `pnpm --dir figma_make_frontend run test:phase5a` | PASS — 12/12 |
| `pnpm --dir figma_make_frontend run test:phase5b` | PASS — 18/18 |
| `pnpm --dir figma_make_frontend run test:phase5c` | PASS — 30/30 |
| `pnpm --dir figma_make_frontend run test:phase5d` | PASS — 22/22 |
| `pnpm --dir figma_make_frontend run test` | PASS — 82/82 |
| `pnpm --dir figma_make_frontend run build` | PASS |
| `git diff --check` | PASS |
| `oxfmt --check` on every changed frontend/config file | PASS |

## Final Git state

- HEAD remains `7de1a79a3b61f3350cda4fdbee5b9b5e865e3b47`.
- No paths are staged.
- The only working-tree paths are the five intended Phase 5D frontend/config/test files and this intentional implementation report.
- No blockers or Owner decisions remain.
