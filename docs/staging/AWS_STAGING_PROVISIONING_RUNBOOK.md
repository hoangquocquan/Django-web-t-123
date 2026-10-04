# AWS staging provisioning runbook

This is an operator procedure, not provisioning authorization. Never run `terraform apply` without explicit approval, an approved budget, and a reviewed plan.

## Preflight

1. Confirm the AWS account, region, budget, hostname, DNS ownership, ACM certificate and two availability zones.
2. Complete the independent `infra/aws/bootstrap` procedure in `AWS_STAGING_BOOTSTRAP_RUNBOOK.md`. It owns the versioned/SSE-S3 state bucket, optional OIDC provider, image-build role, ECR repositories, and Redis AUTH secret/version.
3. Treat bootstrap state access as credential access because Terraform manages the Redis secret value. Record the secret ARN, never the value.
4. If GitHub deployment is approved, enable the full-root deployment role using the bootstrap-selected OIDC provider ARN. It remains separate from the bootstrap image-build role.
5. Copy `terraform.tfvars.example` to ignored `terraform.tfvars`, replace every placeholder, and use exact reviewed image digests.

## Validation and plan

From `infra/aws/staging` run:

```text
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
```

Only after operator context exists, use a saved, reviewed plan. This repository task does not authorize plan or apply.

## Provisioning order for an authorized future session

1. After the separately authorized bootstrap apply and GitHub environment binding, use the manual build workflow for the exact reviewed SHA.
2. Bind the resulting backend/frontend digests in Terraform and review the full plan.
3. Provision the VPC, public ALB subnets, private application/data subnets, VPC endpoints and least-privilege security groups.
4. Provision private RDS (`rds.force_ssl=1`), authenticated TLS Redis, encrypted EFS/mount targets, logs and backups. ECR remains bootstrap-owned.
5. Keep ECS service desired counts at zero during initial binding. Populate `/django-web-t-123/staging/django-secret-key`, `database-url`, `redis-url`, and `metrics-token` directly in Secrets Manager. The Redis URL must use `rediss://` and the same approved token used by ElastiCache. Never print values in CI.
6. Confirm the ACM certificate is issued in the ALB region. If `route53_zone_id` is null, create the external DNS record pointing the approved hostname to the ALB DNS name.
7. Configure the GitHub `staging` environment protections and non-secret variables listed in `AWS_STAGING_OPERATOR_INPUTS.md`.
8. Confirm ECS task definitions use the reviewed digests. The gated deployment workflow raises desired counts only after the migration task succeeds.

## Deployment flow

Dispatch `AWS Staging Deploy (manual, gated)` only after independent review of the new PR head:

```text
exact SHA/digest verification
  -> RDS snapshot and wait
  -> one-off Fargate migration task
  -> require migration exit code 0
  -> backend deployment and stability wait
  -> frontend deployment and stability wait
  -> readiness and read-only health smoke
```

Migration failure prevents service update. A snapshot, service stability, or health failure fails the workflow. The workflow does not perform destructive DB actions or Terraform operations. Web task startup never runs migrations.

## PostgreSQL TLS verification after authorized provisioning

1. Confirm the attached parameter group reports `rds.force_ssl=1` and is in sync after any required reboot.
2. From an approved private diagnostic task, confirm a normal SSL connection succeeds with `sslmode=require`.
3. Attempt a non-SSL connection with `sslmode=disable`; it must be rejected.
4. Preserve sanitized evidence without connection strings or credentials.

Stop on any failed preflight, snapshot, migration, service stability, health, or secret check. Do not enable LINE send or anonymous/public AI.
