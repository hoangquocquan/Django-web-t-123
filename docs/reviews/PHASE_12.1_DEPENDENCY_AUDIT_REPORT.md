# Phase 12.1 Dependency Audit Report

## Scope

Offline dependency audit for Python requirement files. This report does not use
internet access and therefore does not replace a real CVE scan.

## Summary

| Item | Value |
| --- | --- |
| Status | `DEPENDENCY_AUDIT_COMPLETE_WITH_WARNINGS` |
| Scanner mode | `OFFLINE_STATIC_REQUIREMENTS_AUDIT` |
| CVE scan status | `NOT_RUN_NETWORK_DISABLED` |
| Dependency count | `9` |
| Unpinned dependency count | `9` |
| Missing installed count | `0` |

## Dependencies

| Package | Requirement | Installed | Strictly pinned | Known vulnerability status | Warnings |
| --- | --- | --- | --- | --- | --- |
| `pypdf` | `pypdf>=4.3.1` | `6.14.2` | `False` | `NOT_CHECKED_OFFLINE` | Dependency is not strictly pinned with ==.<br>Treat uploaded PDFs as untrusted input and scan/limit file size before processing. |
| `django` | `Django>=5.0,<6.0` | `5.2.16` | `False` | `NOT_CHECKED_OFFLINE` | Dependency is not strictly pinned with ==.<br>Keep on an actively supported Django release and apply security updates quickly. |
| `django` | `django` | `5.2.16` | `False` | `NOT_CHECKED_OFFLINE` | Dependency is not strictly pinned with ==.<br>Keep on an actively supported Django release and apply security updates quickly. |
| `djangorestframework` | `djangorestframework` | `3.17.1` | `False` | `NOT_CHECKED_OFFLINE` | Dependency is not strictly pinned with ==.<br>Review API authentication, throttling and permission settings before public exposure. |
| `django-cors-headers` | `django-cors-headers` | `4.9.0` | `False` | `NOT_CHECKED_OFFLINE` | Dependency is not strictly pinned with ==.<br>Keep CORS_ALLOWED_ORIGINS explicit; do not use wildcard origins in production. |
| `python-dotenv` | `python-dotenv` | `1.2.2` | `False` | `NOT_CHECKED_OFFLINE` | Dependency is not strictly pinned with ==.<br>Do not commit real .env files; load production secrets from a secret manager. |
| `pytest` | `pytest` | `9.1.1` | `False` | `NOT_CHECKED_OFFLINE` | Dependency is not strictly pinned with ==.<br>Test-only dependency; do not install in minimal production image unless needed. |
| `pytest-django` | `pytest-django` | `4.12.0` | `False` | `NOT_CHECKED_OFFLINE` | Dependency is not strictly pinned with ==.<br>Test-only dependency; do not install in minimal production image unless needed. |
| `psycopg` | `psycopg[binary]` | `3.3.4` | `False` | `NOT_CHECKED_OFFLINE` | Dependency is not strictly pinned with ==.<br>Use TLS and credential rotation for PostgreSQL production connections. |

## Recommendations

- Pin production dependencies with exact versions or a locked requirements file.
- Run pip-audit, Safety, Dependabot or GitHub Advanced Security in CI before production.
- Separate production dependencies from test/development dependencies.
- Review CORS, authentication and throttling before public API exposure.

## Final Result

`DEPENDENCY_AUDIT_COMPLETE_WITH_WARNINGS`
