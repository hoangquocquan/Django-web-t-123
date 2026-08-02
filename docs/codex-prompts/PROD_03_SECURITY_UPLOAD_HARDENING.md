# PROD-03 Security And Upload Hardening

## Objective

Harden Django authentication, authorization, token lifecycle, security headers,
and document upload handling without enabling autonomous or production actions.

## Scope

- Central DRF Bearer authentication and module permission adapter.
- Password policy, login throttling, privacy-preserving login audit, token
  rotation/revocation/cleanup, active-session limit, and 2FA challenge layer.
- Upload size, MIME, magic-byte, extension, archive, malware-contract, private
  download, and transaction-safe cleanup controls.
- URL allowlist and SSRF scheme/private-address validation.
- Browser security headers and production container verification.

## Safety Gates

```json
{
  "human_approval_required": true,
  "auto_merge": false,
  "auto_deploy": false,
  "approval_bypass_detected": false
}
```

## Acceptance Criteria

- Anonymous, unauthorized, brute-force, expired, and revoked access fail closed.
- Forged, oversized, malware-signature, zip-bomb, and traversal uploads fail.
- Private files require permission and partial files are removed after failure.
- Compile, Django, migration, focused, regression, static, dependency, Docker,
  PostgreSQL, Redis, and mandatory Ollama review gates pass.

## Rollback

Revert the dedicated PROD-03 commit and reverse migration `foundation.0006` only
after a human confirms no audit/challenge rows need retention.
