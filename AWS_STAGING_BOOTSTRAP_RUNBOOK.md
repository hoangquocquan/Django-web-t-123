# AWS staging bootstrap runbook

This runbook defines future operator sequencing. It is not plan/apply authorization.

## 1. Collect required inputs

- AWS account ID.
- Region `ap-northeast-1`.
- Globally unique state bucket name.
- State keys for bootstrap and staging; the keys must differ.
- Owner and cost-center tags.
- USD 50 monthly budget alert destination.
- `oidc_provider_mode`: `create` or `existing`.
- Exact existing GitHub OIDC provider ARN when using `existing` mode.
- Redis AUTH token delivered through an approved sensitive input channel.
- Later full-stack hostname, DNS provider/ownership, and ACM certificate ARN.

Never commit the Redis token, AWS credentials, populated backend files, real `.tfvars`, state, or lock objects.

## 2. Validate source without cloud execution

For both `infra/aws/bootstrap` and `infra/aws/staging`, permitted commands are:

```text
terraform fmt -check -recursive
terraform init -backend=false -input=false
terraform validate -no-color
```

Do not run plan or apply under this runbook without a new explicit authorization.

## 3. First state-foundation execution

The first future bootstrap execution must use local state on a controlled encrypted operator device because the S3 bucket does not yet exist. Review a normal complete plan—never a routine `-target` plan—and confirm it contains only the bootstrap resource set.

After an authorized apply creates the bucket:

1. Add an empty S3 backend declaration to the bootstrap root.
2. Use a partial backend file with `encrypt = true` and `use_lockfile = true`.
3. Migrate the local bootstrap state to its dedicated key.
4. Confirm the remote state object, versioning, and lockfile behavior.
5. Securely dispose of the local copy according to policy.

Treat state read access as Redis credential access.

## 4. Bootstrap resources and outputs

After a separately reviewed bootstrap plan/apply, record only non-secret outputs:

- `state_bucket_name`, `state_bucket_region`
- `github_oidc_provider_arn`
- `github_image_build_role_arn`
- backend/frontend ECR repository names, URLs and ARNs
- `redis_auth_secret_arn`

Never record the Redis token or state contents as evidence.

## 5. GitHub administrator binding

Create and protect the `staging` environment outside Terraform. Set:

- `AWS_STAGING_REGION=ap-northeast-1`
- `AWS_STAGING_ROLE_ARN=<github_image_build_role_arn>`
- `AWS_STAGING_BACKEND_ECR_REPOSITORY=<backend_ecr_repository_name>`
- `AWS_STAGING_FRONTEND_ECR_REPOSITORY=<frontend_ecr_repository_name>`

Do not add long-lived AWS keys. Do not set `AWS_STAGING_DEPLOY_ROLE_ARN` until the full staging root has created the distinct deploy role.

## 6. Produce immutable images

Run the manual build workflow for one exact reviewed 40-character commit SHA. Capture both `sha256:<64 lowercase hex>` digests. Do not use `latest`, branch tags, or mutable evidence.

## 7. Prepare the full staging root

Copy the bootstrap repository URLs/ARNs, Redis secret ARN, and OIDC provider ARN into an ignored operator tfvars file. Supply the exact image digests. Initialize the full root against a different S3 state key.

Before requesting full-plan authorization, confirm:

- the bootstrap and staging states have no duplicate physical resources;
- hostname, DNS ownership and regional ACM certificate are approved;
- the Redis secret version exists;
- both image digests resolve in the two bootstrap repositories;
- budget alerts and ownership are approved;
- all static validation and security checks pass.

## 8. Post-full-apply binding

Only after a separately authorized full apply:

- populate Django/database/Redis/metrics runtime secret values securely;
- set `AWS_STAGING_DEPLOY_ROLE_ARN` from `github_staging_deploy_role_arn`;
- set ECS, subnet, security-group, RDS, URL and desired-count GitHub variables;
- bind external DNS when Route 53 is not selected;
- run the gated migration/deployment workflow only after independent review.

## Stop conditions

Stop on missing account, alert destination, hostname/DNS/certificate, ambiguous OIDC ownership, duplicate resource ownership, broadened trust, mutable images, exposed secret/state, unexpected full-platform resources in bootstrap, or any request to plan/apply without separate authorization.
