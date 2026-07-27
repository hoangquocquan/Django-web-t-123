# Authorization Model

## Roles

| Role | Meaning |
| --- | --- |
| `admin` | Full CMS/system access |
| `editor` | Content and business operation management |
| `viewer` | Read-only access |

## Permissions

Current compatibility matrix:

| Role | Permission boundary |
| --- | --- |
| `admin` | Read/write on all modules |
| `editor` | Read/write on CMS/business modules, not system settings |
| `viewer` | Read-only on all modules |
| unknown role | No access |

## Access Rules

| Surface | Current rule |
| --- | --- |
| Legacy Admin CMS | Uses legacy session and role checks |
| Django `/api/v1/auth/*` | Read-only compatibility |
| Django business list/detail APIs | Read-only migration/API readiness |
| Django write-intent replacements | Validation-gated and migration-safe |
| Production shutdown tools | Blocked unless evidence and approvals pass |

## API Endpoint Protection

Known controls:

- `ReadOnlyApiPermission` blocks unsafe methods on protected business APIs.
- Sensitive auth fields are excluded from auth profile responses.
- Migration tools use explicit safety gates and reports.

Open controls:

- final API authentication for public production
- final per-role endpoint permission map
- per-user audit trail on Django write APIs

## Admin Permissions

Admin permissions currently map to the legacy admin/editor/viewer roles. The
final Django admin/CMS cutover should preserve role behavior and add explicit
tests for every module/action pair.

## Security Boundaries

| Boundary | Rule |
| --- | --- |
| Public website | Public content only |
| Internal CMS | Requires authenticated admin session |
| Internal APIs | Require approved auth policy before public exposure |
| Migration scripts | Local/operator execution only |
| Production shutdown | Requires real evidence and signed approvals |

## Recommendation

Keep `/api/v1/*` business APIs internal until production authentication,
authorization, throttling and monitoring are approved.
