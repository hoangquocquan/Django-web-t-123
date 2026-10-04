# Production readiness remediation report

## Scope

- Base SHA: `cde61c8738182e531a5d04fc6a18f5a0c241a410`
- Branch: `feat/production-readiness-remediation`
- Production deployment performed: **NO**
- Production data or credentials used: **NO**
- LINE/n8n sending enabled: **NO**

## P1 remediation matrix

| P1 | Can fix in repo | Needs infrastructure | Needs human | Planned/resulting action | Classification |
|---|---:|---:|---:|---|---|
| Deployment/promotion | Yes | Yes | Yes | Controlled immutable-artifact deployment and rollback runbooks | MANUAL_EXECUTION_REQUIRED |
| Secret manager/validation | Partial | Yes | Yes | Secret-safe preflight plus full-history CI scan; external manager remains operator-owned | MANUAL_EXECUTION_REQUIRED |
| Backup/restore rehearsal | Procedure | Yes | Yes | Executable runbook and rehearsal checklist | MANUAL_EXECUTION_REQUIRED |
| Monitoring/alerts/logs | Procedure | Yes | Yes | Minimum signals, routing and alert-test checklist | MANUAL_EXECUTION_REQUIRED |
| Durable media | Contract | Yes | Yes | Fail-fast attestations and storage requirements | MANUAL_EXECUTION_REQUIRED |
| AI health disclosure | Yes | No | No | Anonymous response minimized; details protected by operations token | REMEDIATED_IN_REPO |
| Redis/Ollama/provider drill | Procedure/config | Yes | Yes | Explicit flags and controlled staging drill | MANUAL_EXECUTION_REQUIRED |
| Capacity/migration locks | Procedure | Yes | Yes | Scenarios and unapproved target placeholders | MANUAL_EXECUTION_REQUIRED |
| CI security gates | Yes | No | No | Gitleaks, pip-audit, pnpm audit, Bandit, Trivy and SBOM | REMEDIATED_IN_REPO |
| Database TLS | Yes | CA provisioning | Yes | Only `require`/`verify-full`; explicit CA guidance | REMEDIATED_IN_REPO |

## Repository changes

Production settings now reject plaintext-capable PostgreSQL modes, non-TLS Redis, enabled LINE/legacy switches, missing AI flags and unacknowledged durable media. A secret-safe validator reports names and sanitized reasons only. The AI health endpoint preserves public status while preventing anonymous provider/model/error disclosure. A read-only smoke tool contains only liveness/readiness GETs. Runtime dependency patches resolve the audited Django and DRF advisories.

Operational documentation covers deployment, immutable promotion, backup/restore, migration rehearsal, media, observability, dependency drills, capacity, admin, edge security, rollback, LINE/n8n boundary and full-history secret scanning.

## Validation evidence

- Focused remediation/security tests: **23 PASS**
- Django system check: **PASS**
- `makemigrations --check --dry-run`: **PASS**
- Synthetic production preflight: **PASS**, values not emitted
- Django `check --deploy`: **PASS with expected synthetic-key strength warning**
- Python production dependency audit after patch upgrades: **0 known vulnerabilities**
- Frontend production dependency audit: **0 known vulnerabilities**
- Bandit high-severity gate: **PASS**
- Frontend tests: **174 PASS**; typecheck/build: **PASS**
- Feature Python compile and `git diff --check`: **PASS**
- Full local backend suite: 648 PASS, with one pre-existing business UI access-fixture failure and three Windows Unicode-path n8n resolver failures; none intersect this remediation. Exact-head GitHub CI remains authoritative before merge.
- Migrations changed: **NO**

## Manual evidence still required

External secret-manager injection, production-like restore, alert delivery, durable storage provisioning, Redis/AI/provider failure drill, capacity/load test, PostgreSQL migration lock rehearsal, edge controls and actual artifact promotion remain unperformed. Their runbooks do not constitute completion.

AI HEALTH DISCLOSURE: FIXED

DATABASE TLS POLICY: PASS

PRODUCTION CONFIG VALIDATION: PASS

DEPLOYMENT RUNBOOK: READY

SECRET SCANNING CI: PASS

DEPENDENCY SECURITY CI: PASS

SAST: PASS

BACKUP/RESTORE PROCEDURE: DOCUMENTED

BACKUP/RESTORE REHEARSAL: MANUAL_EXECUTION_REQUIRED

OBSERVABILITY REQUIREMENTS: DOCUMENTED

OBSERVABILITY PLATFORM: MANUAL_EXECUTION_REQUIRED

DURABLE MEDIA CONTRACT: DOCUMENTED

DURABLE MEDIA PROVISIONING: MANUAL_EXECUTION_REQUIRED

PROVIDER/REDIS DRILL: MANUAL_EXECUTION_REQUIRED

CAPACITY TEST: MANUAL_EXECUTION_REQUIRED

MIGRATION REHEARSAL: MANUAL_EXECUTION_REQUIRED

LINE/N8N PRODUCTION SEND: NOT_ENABLED

SCOPE CLEAN: YES

READY TO COMMIT: YES
