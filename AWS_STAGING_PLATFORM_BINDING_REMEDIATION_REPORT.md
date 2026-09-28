# AWS staging platform binding remediation report

## Git state

```text
BRANCH: feat/aws-staging-platform-binding
START_HEAD: ee822d546f5ffbe701d60f0c3b489f21ea1bf058
FINAL_HEAD: SELF (the commit containing this report; use PR #14 head metadata for the immutable SHA)
BASE_MAIN: 31da17011adb22a0dab4857f8249985249af0e51
WORKTREE: C:\Users\hoang\.codex\worktrees\aws-staging-platform-binding\WEB Ô TÔ DJANGO
```

The originally requested checkout `C:\Users\hoang\Documents\Django-web-t-123` was on unrelated branch `codex/demo-database-validation` at `2ebcb30cbe28749c5a610a42e3a4bc899faf7b47` with user application/migration changes. It was fetched read-only and left untouched. Remediation used the existing isolated PR worktree above.

## Blocker remediation matrix

| Blocker | Previous state | New state | Evidence |
|---|---|---|---|
| Public subnets | Missing | Implemented in two AZs; ALB only | `infra/aws/staging/networking.tf` |
| Private app/data tiers | Partial data subnets only | Separate private application/data subnets and route tables | `infra/aws/staging/networking.tf` |
| ALB | Missing | HTTPS listener, HTTP redirect, target groups, routing and health checks | `infra/aws/staging/load-balancer.tf` |
| ECS task definitions | Missing | Digest-pinned backend/frontend plus separate migration task | `infra/aws/staging/ecs.tf` |
| ECS services | Missing | Private Fargate services, no public IP, stability-aware deployment | `infra/aws/staging/ecs.tf` |
| IAM roles | Missing | Scoped execution/task/OIDC/backup roles; unavoidable wildcard Describe/token actions documented | `infra/aws/staging/iam.tf`, `backup-observability.tf` |
| Security groups | Missing | Explicit ALB→ECS→RDS/Redis/EFS and endpoint flows | `infra/aws/staging/security-groups.tf` |
| EFS mount targets | Missing | Two data-subnet targets, encrypted filesystem, access point, TLS/IAM mounts | `infra/aws/staging/data-services.tf`, `ecs.tf` |
| DNS/ACM | Documentation only | Required approved certificate ARN; optional Route 53 alias; external DNS documented | `infra/aws/staging/load-balancer.tf`, `variables.tf` |
| Redis authentication | Missing | Redis 7.1 auth token sourced from operator-managed Secrets Manager ARN | `infra/aws/staging/data-services.tf` |
| RDS TLS enforcement | Missing | PostgreSQL 16 parameter group sets `rds.force_ssl=1`; app requires `sslmode=require` | `infra/aws/staging/data-services.tf`, `ecs.tf` |
| Runtime safety flags | Documentation only | Supported LINE/Ollama/legacy flags explicit; public AI constants remain application-fixed false | `infra/aws/staging/ecs.tf`, architecture document |
| Environment validation | Missing | Root accepts only `environment == "staging"`; provider restricts account ID | `infra/aws/staging/variables.tf`, `versions.tf` |
| tfvars consistency | Inconsistent | All sample keys declared; no orphan keys or secret values | `infra/aws/staging/terraform.tfvars.example` |
| Migration workflow | Documentation only | Executable one-off ECS task; snapshot/migration/service/health gates fail closed | `.github/workflows/aws-staging-deploy.yml` |
| Build workflow | Validation-only | Exact-SHA build/push and immutable digest evidence through OIDC | `.github/workflows/aws-staging-build.yml` |
| Cost controls | High-cost choices unresolved | No NAT; service count starts at zero; small single-AZ defaults; retention bounded | `AWS_STAGING_COST_GUARDRAILS.md` |

## Static security review

- No AWS key, database password, Redis token, LINE token, AI/API secret, Terraform state, real `.tfvars`, or plan file was found in the remediation scope.
- RDS is private and encrypted; TLS is enforced by parameter group.
- Redis is private, authenticated, and encrypted in transit/at rest.
- EFS is encrypted; ECS mounts require TLS and IAM authorization.
- ECS tasks have no public IP. The ALB is the sole public entry point.
- IAM contains no `Action = "*"`. Four `Resource = "*"` cases are limited to APIs that do not support useful resource scoping (`ecr:GetAuthorizationToken`, ECS/RDS Describe) and are documented inline.
- ECR tags are immutable and scan on push.
- Runtime safety flags are explicit. Normal web task commands contain no migration.
- Terraform state and real `terraform.tfvars` patterns are ignored.

## Validation results

```text
TERRAFORM_TOOL_AVAILABLE=YES
TERRAFORM_FMT=PASS
TERRAFORM_INIT_BACKEND_FALSE=PASS
TERRAFORM_VALIDATE=PASS

DJANGO_TESTS=PASS (400 passed, 151 skipped)
DJANGO_CHECK=PASS
DJANGO_MIGRATION_DRIFT=PASS (No changes detected)
FRONTEND_BUILD=PASS
FRONTEND_TYPECHECK=PASS
AWS_LEARNING_LAB=PASS (8 passed; Compose config valid)
RUNTIME_SYNTAX=PASS
SECRET_SCAN=PASS_STATIC; GITLEAKS_LOCAL=NOT_RUN_TOOL_UNAVAILABLE; EXACT_HEAD_CI_REQUIRED
SAST=PASS (Bandit high-severity gate; no issues)
VULNERABILITY_SCAN=PASS_DEPENDENCY_AUDITS; TRIVY_LOCAL=NOT_RUN_TOOL_UNAVAILABLE; EXACT_HEAD_CI_REQUIRED
POSTGRES_MIGRATION_SMOKE=NOT_RUN_LOCAL; EXACT_HEAD_CI_REQUIRED
PHASE_13_2=NOT_RUN_LOCAL; EXACT_HEAD_CI_REQUIRED
```

The first full pytest attempt produced only environment setup errors because a pre-existing global pytest temp directory had inaccessible ownership. Re-running with a fresh task-specific `--basetemp` passed all executed tests; the scratch directory was removed afterward.

## AWS mutation

```text
AWS_PLAN_EXECUTED=NO
AWS_APPLY_EXECUTED=NO
AWS_MUTATION=NO
PAID_RESOURCE_CREATED=NO
PRODUCTION_RESOURCE_CREATED=NO
```

## Application scope

```text
APPLICATION_CODE_CHANGED=NO
BUSINESS_LOGIC_CHANGED=NO
DATABASE_SCHEMA_CHANGED=NO
RAG_CONTRACT_CHANGED=NO
AI_SALES_CONTRACT_CHANGED=NO
LINE_N8N_PRODUCTION_SEND_CHANGED=NO
```

## Remaining operator inputs

No code blocker remains from the prior final review. Provisioning still requires account, region, budget, hostname/DNS, issued ACM certificate, encrypted remote state, approved image digests, Redis auth secret, runtime secret population, GitHub staging environment/OIDC approval and explicit provisioning authorization.

The new exact PR head must receive independent review and all GitHub checks (including Gitleaks, Trivy, Phase 13.2 and PostgreSQL smoke) must pass before any merge decision.

```text
READY_FOR_FINAL_PR_REVIEW=YES
READY_TO_MERGE=NO (independent review and exact-head CI still required)
READY_FOR_AWS_PROVISIONING=NO
```
