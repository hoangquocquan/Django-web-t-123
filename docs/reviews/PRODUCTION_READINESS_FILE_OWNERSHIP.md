# Production Readiness File Ownership

| Phase | Primary ownership |
| --- | --- |
| PROD-00 | Production readiness specifications, baseline evidence and reviews |
| PROD-01 | `apps/business_ui`, Sales/CRM UI tests and UAT fixtures |
| PROD-02 | Production settings, Docker/runtime configuration and infrastructure tests |
| PROD-03 | Authentication, DRF policy, upload validation and security tests |
| PROD-04 | Ollama, Redis, n8n and AI runtime configuration/tests |
| PROD-05 | Monitoring, backup/restore scripts and runbooks |
| PROD-06 | Staging/UAT harness, load/security validation and reports |
| PROD-07 | Release manifest, deployment/rollback checklists and final handover |

Shared settings, URLs, models, migrations, and fixtures are edited serially.
