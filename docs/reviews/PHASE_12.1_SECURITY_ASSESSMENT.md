# Phase 12.1 Security Assessment

## Current Security Status

The system has meaningful security foundations, but it is not ready for broad
public production exposure.

| Area | Current status | Risk |
| --- | --- | --- |
| Authentication | Legacy admin auth exists; Django auth cutover is read-only/preparatory | High |
| Authorization | Role matrix exists; public/internal API boundaries need final policy | High |
| Secrets | `.env` ignored and examples exist; demo defaults remain for local use | Medium |
| Dependencies | Requirements exist but production lock/CVE scan is not complete | Medium |
| API security | Read-only permission and sensitive-field tests exist | Medium |
| Production shutdown | Still `BLOCKED_SAFELY` | Controlled |

## Authentication Review

Legacy backend supports login, password reset, sessions, CSRF helpers and
account status workflows. Django currently exposes compatibility/read surfaces
and should not be treated as final production login.

Risks:

- production auth cutover incomplete
- demo compatibility tokens must not be used publicly
- reset/session/token fields require strict non-exposure controls

## Authorization Review

Current role model:

- `admin`
- `editor`
- `viewer`

The role matrix exists in Django compatibility services. The public exposure
boundary still needs a final product decision before business APIs are opened
to real users or partners.

## Secret Review

Current protections:

- `.env` and `.env.*` ignored
- `.env.example` files allowed
- Django production settings default to secure cookie/HSTS flags

Open issues:

- local demo defaults exist
- no automated secret scanner is configured yet
- production secrets should move to a proper secret manager

## Dependency Review

Phase 12.1 adds an offline dependency audit. It checks requirement files,
installed versions and pinning status. It does not replace CVE scanning.

## Risk Ranking

| Rank | Risk | Severity | Recommendation |
| --- | --- | --- | --- |
| 1 | Production auth/authorization incomplete | High | Complete auth cutover design before public API exposure |
| 2 | Demo token/default secret usage | High | Replace with secret-manager backed values |
| 3 | Business read APIs exposed without final auth | High | Keep internal until policy is approved |
| 4 | Dependencies not locked/CVE scanned | Medium | Add pip-audit/Dependabot/lockfile |
| 5 | CORS/CSRF policy not production-reviewed for write APIs | Medium | Finalize before write cutover |

## Assessment Result

`SECURITY_HARDENING_COMPLETE_WITH_REMAINING_RISKS`
