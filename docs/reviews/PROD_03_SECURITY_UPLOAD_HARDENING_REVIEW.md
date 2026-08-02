# PROD-03 Security And Upload Hardening Review

## Phase

- Date: 2026-08-02
- Branch: `codex/production-readiness-full`
- Baseline: `02a79c4b882f3f7cabeb8463e422048d8346668d`
- Phase commit: `0f2f0c0fd2d5dfd22f39bab187bf95b5543a85a2`
- Decision: `PASS_WITH_WARNINGS`
- Next-phase eligibility: `READY_FOR_NEXT_PHASE`

## Objective And Scope

PROD-03 centralizes DRF Bearer authentication and module permission policy,
hardens foundation login/token behavior, adds a one-time 2FA challenge layer,
and protects document ingestion and private download paths.

## Architecture And Database Impact

- `FoundationBearerAuthentication` is the default DRF authentication adapter;
  absent credentials remain anonymous and invalid credentials fail with 401.
- Password policy, hashed login audit, brute-force lockout, active-session limit,
  token rotation/revocation/cleanup, and operator cleanup command are centralized.
- Migration `foundation.0006` creates privacy-preserving login audit and
  short-lived 2FA challenge tables. It applied successfully to local PostgreSQL.
- Upload validation runs before extraction/storage; downstream failure deletes
  the newly stored file. Private download never exposes filesystem paths.

## Security Impact

- Unsafe URL schemes, private addresses, credentials, and non-allowlisted hosts
  are rejected for configurable external URL fields.
- Uploads enforce size, extension, MIME, magic bytes, archive traversal/member/
  expansion limits, and a malware scanner contract with EICAR rejection.
- CSP, HSTS, referrer policy, permissions policy, nosniff, and frame protection
  were observed on the production-like HTTP response.
- No raw login email/IP, token, credential, runtime DB, ZIP, backup, or PII log
  is staged.

## Validation Results

- Compile, Django checks, migration drift: PASS.
- Focused auth/knowledge/security tests: 42 passed.
- Full regression after final formatting: 479 passed, 0 failed.
- Ruff lint/format, targeted mypy, and Bandit: PASS.
- Production and development dependency audits: no known vulnerabilities.
- PostgreSQL migration, Redis cache, Docker non-root health, and artifact scan:
  PASS. Final image contains no `.env`, ZIP, SQLite, DB, or backup artifact.

## Mandatory Ollama Review

- Model: `llama3`
- Decision: PASS
- Schema valid: true
- Fallback used: false
- Critical/High/Medium findings: 0/0/0
- Attempts: 1
- Gate state: `WAITING_HUMAN_APPROVAL`

## Tools Not Run

- Docker Scout was attempted but requires Docker ID authentication.
- `gitleaks` and `trivy` are not installed. Deterministic secret/path scanning,
  `pip-audit`, Bandit, and runtime image artifact scanning passed.
- Browser E2E was not rerun because PROD-03 changed API/security behavior, not UI.

## Known Limitations

- A trusted email/authenticator adapter must deliver 2FA challenge codes.
- A production malware engine such as ClamAV must implement the scanner contract.
- Distributed Redis rate limiting and live n8n are explicit PROD-04 gates.

## Rollback

Revert the dedicated phase commit. Reverse migration `foundation.0006` only with
human approval after confirming audit/challenge retention is unnecessary.

## Final Decision

`PASS_WITH_WARNINGS`. All required PROD-03 gates passed and PROD-04 may start.
This review does not authorize merge, push, tag, staging, or production deploy.
