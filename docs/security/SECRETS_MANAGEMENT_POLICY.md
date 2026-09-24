# Secrets Management Policy

## Secret Locations

| Location | Status | Rule |
| --- | --- | --- |
| `.env` | Ignored | May contain local secrets; never commit |
| `.env.*` | Ignored | May contain environment secrets; never commit |
| `.env.example` | Committed | Must contain placeholders only |
| `django_backend/.env.example` | Committed | Must contain placeholders only |
| GitHub Actions secrets | Future | Store CI/deployment secrets outside repo |
| Production secret manager | Future | Required before public production |

## Sensitive Values

Treat these as secrets:

- Django `SECRET_KEY`
- database URLs with passwords
- Redis URLs with passwords
- admin tokens
- session IDs
- CSRF tokens
- password reset tokens
- 2FA challenge codes
- SMTP passwords
- AI/API provider keys

## Risk

Current risk is medium:

- `.gitignore` protects `.env` files
- example files exist
- local demo defaults exist for learning
- no automated secret scanner is currently configured

## Rotation Strategy

1. Rotate all demo/local secrets before production.
2. Rotate admin/API tokens whenever exposed in logs, screenshots or support
   tickets.
3. Rotate database credentials after migration/cutover drills.
4. Rotate SMTP/API provider keys on a fixed schedule.
5. Keep rotation evidence in the security review package.

## Storage Recommendation

Development:

- local `.env`
- never commit real secrets

CI/CD:

- GitHub Actions secrets
- masked logs

Production:

- cloud secret manager or vault
- least-privilege service accounts
- audited access

## Logging Policy

Do not log:

- passwords
- password hashes
- tokens
- session IDs
- raw authorization headers
- full database URLs with passwords

## Implementation Status

| Control | Status |
| --- | --- |
| `.env` ignored | Implemented |
| `.env.example` placeholder files | Implemented |
| Secret scanner | Pending |
| Secret manager | Pending |
| Rotation procedure | Documented in this phase |
