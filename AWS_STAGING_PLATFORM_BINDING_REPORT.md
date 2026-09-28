# AWS staging platform binding report

## Scope

- Branch: `feat/aws-staging-platform-binding`
- Base main: `31da17011adb22a0dab4857f8249985249af0e51`
- Remediation start: `ee822d546f5ffbe701d60f0c3b489f21ea1bf058`
- Application code change required: **NO**
- No business logic, model, serializer, business migration, CRM/RFQ contract, Knowledge/RAG contract, AI Sales contract or LINE/n8n send path changed.

## Implemented binding

The staging Terraform root now implements the documented public ALB/private ECS/private data topology rather than describing it only in prose. It includes:

- two public ALB subnets, two private application subnets, and two private data subnets;
- HTTPS ALB with ACM, HTTP redirect, target groups, routing and health checks;
- private backend/frontend Fargate services, CloudWatch logs and Service Connect;
- least-privilege security groups and task/execution roles;
- private encrypted RDS PostgreSQL with `rds.force_ssl=1`;
- private encrypted Redis 7.1 with authentication sourced from an operator-managed Secrets Manager secret;
- encrypted EFS, mount targets, access point, TLS/IAM mounts and read-only frontend media access;
- immutable/scanned ECR repositories, bounded lifecycle, AWS Backup and basic alarms;
- optional Route 53 alias and optional repository/environment-scoped GitHub OIDC role;
- digest-pinned backend/frontend task definitions and a separate one-off migration task;
- manual build/deploy workflows that verify exact SHA/digests and fail closed when operator binding is absent.

There is no NAT Gateway. Private tasks use ECR, CloudWatch Logs and Secrets Manager interface endpoints plus an S3 gateway endpoint. This prevents unrestricted internet egress and avoids NAT's fixed recurring cost; interface endpoints remain paid resources if later provisioned.

## Runtime safety

Backend ECS explicitly configures:

- `LINE_SEND_ENABLED=false`
- `LEGACY_DATABASE_ENABLED=false`
- `AI_SALES_OLLAMA_ENABLED=false`
- `AI_AGENT_OLLAMA_PLANNER_ENABLED=false`
- `AI_OLLAMA_CAPACITY_ENABLED=false`

`PUBLIC_AI_ENABLED` and `PUBLIC_SYNTHETIC_RAG_DEMO_ENABLED` are application constants fixed to `False`, not supported environment variables. No fictional env names were added.

Web startup remains Gunicorn only. Services default to desired count zero during initial binding. The gated deployment flow creates and waits for an RDS snapshot, runs the dedicated migration task, requires exit code zero, raises service desired counts, waits for stability, and performs readiness/read-only health checks.

## Validation

Terraform CLI was found and actually executed from `infra/aws/staging`:

- `terraform fmt -check -recursive`: PASS after `terraform fmt -recursive`
- `terraform init -backend=false -input=false`: PASS
- `terraform validate`: PASS (`Success! The configuration is valid.`)

No Terraform plan or apply was run. No AWS API was called.

Local application checks:

- Django system check: PASS
- migration drift check: PASS (`No changes detected`)
- full Django pytest: PASS (`400 passed, 151 skipped`)
- frontend typecheck/build: PASS
- AWS learning lab: PASS (`8 passed`) and Compose definition valid
- Phase 6 PowerShell/Compose syntax: PASS
- Bandit high-severity gate: PASS
- Python and frontend production dependency audits: PASS, no known vulnerabilities

Gitleaks and Trivy CLIs were unavailable locally. Their exact-head GitHub checks must pass before any merge decision.

## Operator boundary

Terraform remains unapplied. Required operator inputs include approved AWS account/region, budget, DNS/hostname, issued ACM certificate, encrypted remote state, image digests, Redis auth secret ARN, runtime secret values, GitHub staging environment protection and explicit provisioning authorization.

TERRAFORM VALIDATION: PASS

AWS PLAN EXECUTED: NO

AWS APPLY EXECUTED: NO

AWS MUTATION PERFORMED: NO

PAID RESOURCE CREATED: NO

PRODUCTION RESOURCE CREATED: NO

LINE/N8N PRODUCTION SEND: NOT_ENABLED

READY TO TERRAFORM APPLY: NO

READY FOR AWS OPERATOR PLAN: YES, AFTER INDEPENDENT PR REVIEW AND OPERATOR INPUT

READY FOR FINAL PR REVIEW: YES
