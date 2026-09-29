# AWS staging operator inputs

Names, ARNs and decisions only. Never enter secret values in this document, Git, chat, workflow inputs or logs.

## Bootstrap Terraform inputs

- `aws_account_id`
- `aws_region` (`ap-northeast-1` selected)
- `owner`
- `cost_center`
- `state_bucket_name`
- `oidc_provider_mode` (`create` or `existing`)
- `existing_github_oidc_provider_arn` only in `existing` mode
- `redis_auth_token` through an approved sensitive channel only; it is stored in bootstrap state and never output

## Full staging Terraform inputs

- `aws_account_id`
- `aws_region`
- `candidate_sha`
- `owner`
- `cost_center`
- `staging_hostname`
- `certificate_arn` (issued ACM certificate in the selected region)
- `route53_zone_id` or `null` for external DNS
- `backend_image_digest`
- `frontend_image_digest`
- backend/frontend ECR repository URLs and ARNs from bootstrap outputs
- `redis_auth_secret_arn` from the bootstrap output
- optional approved AZs and staging sizes/retention values
- `enable_github_deploy_role`
- `github_oidc_provider_arn` from bootstrap when deployment-role creation is enabled

## GitHub staging environment variables

- `AWS_STAGING_REGION`
- `AWS_STAGING_ROLE_ARN` (bootstrap image-build role only)
- `AWS_STAGING_DEPLOY_ROLE_ARN` (full-root deployment role only)
- `AWS_STAGING_BACKEND_ECR_REPOSITORY`
- `AWS_STAGING_FRONTEND_ECR_REPOSITORY`
- `AWS_STAGING_ECS_CLUSTER`
- `AWS_STAGING_BACKEND_SERVICE`
- `AWS_STAGING_FRONTEND_SERVICE`
- `AWS_STAGING_MIGRATION_TASK_DEFINITION`
- `AWS_STAGING_APPLICATION_SUBNETS` (comma-separated subnet IDs)
- `AWS_STAGING_BACKEND_SECURITY_GROUP`
- `AWS_STAGING_RDS_IDENTIFIER`
- `AWS_STAGING_URL`
- `AWS_STAGING_SERVICE_DESIRED_COUNT` (`1` or `2`)

These are identifiers, not credentials. GitHub authenticates through OIDC; do not add long-lived AWS keys.

## Required approvals

- AWS account and region
- DNS/ACM ownership
- monthly budget and alert destination
- RDS/Redis/EFS sizes and retention
- interface endpoint recurring cost
- GitHub OIDC/environment protection
- encrypted remote Terraform state
- secret population procedure
- explicit provisioning authorization

AI remains initially disabled. LINE production send remains disabled. This staging binding does not authorize production deployment.
