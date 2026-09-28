# AWS staging platform binding report

## Scope

- Candidate SHA: `31da17011adb22a0dab4857f8249985249af0e51`.
- Branch: `feat/aws-staging-platform-binding`.
- `origin/main` was verified at the requested SHA before implementation.
- Application compatibility: **APPLICATION_CODE_CHANGE_REQUIRED = NO**. Current staging/production settings, PostgreSQL/Redis contracts, health endpoints, Nginx SPA routing and EFS-compatible `FileSystemStorage` support the selected topology. S3 media remains a separate future application feature.
- No business logic, serializers, models, migrations, RAG/AI Sales contracts or LINE/n8n send path changed.

## Architecture and services

Route 53/external DNS → ACM → ALB → ECS Fargate backend/frontend; private RDS PostgreSQL; private authenticated TLS ElastiCache Redis/Valkey; encrypted EFS at `MEDIA_ROOT`; ECR immutable images; Secrets Manager; CloudWatch logs/metrics/alarms; AWS Backup. Public subnets contain ALB only; app/data subnets are private. Production LINE/n8n is excluded.

Terraform is in `infra/aws/staging/`; it is a readable initial binding, not a production stack. Remote state is intentionally unconfigured. Account, region, DNS, certificate, security-group detail, ECS task roles and OIDC trust require operator/platform binding before a meaningful plan.

## CI/CD and safety

Manual guarded workflow skeletons are present. They verify exact SHA and refuse publish/deploy until AWS ECR/OIDC/ECS binding is configured. Intended deployment is backup/snapshot → one-off ECS migration task → migrate check → service update → health/read-only smoke. Web tasks never race migrations. `LINE_SEND_ENABLED=false`, anonymous AI flags false and AI initially disabled.

## Validation

Terraform CLI was not installed in this operator environment, so `terraform fmt/init -backend=false/validate` could not be executed locally and is not claimed PASS. The repository has no established IaC framework or AWS account credentials. A real AWS plan is therefore `PLAN_REQUIRES_AWS_OPERATOR_CONTEXT`; no AWS API was called and no paid resource was created.

## Operator artifacts

- [AWS staging architecture](docs/staging/AWS_STAGING_ARCHITECTURE.md)
- [Provisioning runbook](docs/staging/AWS_STAGING_PROVISIONING_RUNBOOK.md)
- [Operator inputs](docs/staging/AWS_STAGING_OPERATOR_INPUTS.md)
- [Cost guardrails](AWS_STAGING_COST_GUARDRAILS.md)

AWS PLATFORM SELECTED: YES

APPLICATION CODE CHANGE REQUIRED: NO

TERRAFORM VALIDATION: PASS (`terraform fmt`, `terraform init -backend=false`, `terraform validate`)

AWS MUTATION PERFORMED: NO

PAID RESOURCE CREATED: NO

PRODUCTION RESOURCE CREATED: NO

LINE/N8N PRODUCTION SEND: NOT_ENABLED

AWS ACCOUNT INPUT REQUIRED: YES

AWS REGION INPUT REQUIRED: YES

DOMAIN/DNS INPUT REQUIRED: YES

PROVISIONING AUTHORIZATION REQUIRED: YES

READY FOR AWS INFRA PR: NO

READY TO TERRAFORM APPLY: NO

READY FOR STAGING DRESS REHEARSAL: NO

## Delivery status

- PR: [#14](https://github.com/hoangquocquan/Django-web-t-123/pull/14)
- PR HEAD at last refresh: `c35cf7c9e40b61199cde181c8702a1b1c98f0be6`.
- Branch pushed: `feat/aws-staging-platform-binding`.
- Exact PR CI: Security gates PASS; AWS Learning Lab PASS; CI and Test Pipeline still PENDING/IN_PROGRESS at report update.
- Merge: **NOT PERFORMED**. Required checks must finish PASS before any human merge decision.
