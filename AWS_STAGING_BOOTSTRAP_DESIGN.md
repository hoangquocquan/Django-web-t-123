# AWS staging bootstrap implementation design

## Decision

The circular image/platform dependency is resolved with **Option A: an independent Terraform bootstrap root with independent state**.

- `infra/aws/bootstrap` owns the small prerequisite layer.
- `infra/aws/staging` owns the full application platform.
- External/operator systems own GitHub environment protection, ACM issuance, and external DNS where Route 53 is not selected.
- Routine `terraform apply -target` is not part of the bootstrap procedure.

No physical resource may be managed by both Terraform states.

## Bootstrap root

The bootstrap root owns:

- an operator-named S3 state bucket with versioning, Block Public Access, bucket-owner-enforced ownership, SSE-S3, HTTPS-only policy, and support for native S3 lockfiles through later backend configuration;
- the account-level GitHub OIDC provider when `oidc_provider_mode = "create"`, or an exact existing provider ARN when the mode is `existing`;
- a dedicated image-build role trusted only for audience `sts.amazonaws.com` and subject `repo:hoangquocquan/Django-web-t-123:environment:staging`;
- immutable, scan-on-push, AES256-encrypted backend/frontend ECR repositories with retention limited to the newest 20 images;
- the Redis AUTH secret container and version.

The image-build role permits only `ecr:GetAuthorizationToken` plus the push/layer/image operations required for those two repository ARNs. It has no ECS, Secrets Manager, IAM mutation, RDS, or account-administration permissions.

`redis_auth_token` is sensitive and is never output, but the value is stored in Terraform state because Terraform manages the secret version. Bootstrap state access must therefore be treated as credential access.

## Full staging root

The full root consumes these bootstrap outputs:

- backend/frontend ECR repository URLs and ARNs;
- Redis AUTH secret ARN;
- GitHub OIDC provider ARN when creation of the distinct deployment role is enabled.

It composes task images as:

```text
<bootstrap ECR repository URL>@<sha256:64-lowercase-hex>
```

It does not create or import bootstrap-owned ECR repositories, lifecycle policies, image-build role, OIDC provider, or Redis AUTH secret. It continues to own VPC/networking, ALB, ECS, RDS, Redis cluster, EFS, CloudWatch, Backup, runtime secret containers, and the optional deployment role.

The deployment role is deliberately separate from the image-build role. It can verify image digests and perform the existing migration/snapshot/ECS deployment flow, but it cannot push images.

## Remote state and first migration

The full staging root contains an empty `backend "s3" {}` declaration. Operators supply non-secret partial backend settings, including:

```hcl
bucket       = "<OPERATOR_STATE_BUCKET>"
key          = "<DISTINCT_STATE_KEY>"
region       = "ap-northeast-1"
encrypt      = true
use_lockfile = true
```

Backend credentials are supplied through the normal AWS credential chain, never committed configuration.

The bootstrap root initially needs controlled local state because its first execution creates the state bucket. After that separately authorized execution, the operator adds the empty S3 backend declaration, migrates local state to a dedicated bootstrap key, verifies versioning and native lockfiles, and securely disposes of the local copy under policy. The staging key must be different.

HashiCorp recommends bucket versioning and documents `use_lockfile = true` for native S3 locking; DynamoDB locking is deprecated: [Terraform S3 backend](https://developer.hashicorp.com/terraform/language/backend/s3).

## Ownership inventory

`Yes` means the named owner manages the resource. Conditional rows identify the exclusive choice.

| Resource | Bootstrap state | Full staging state | External/manual |
|---|---:|---:|---:|
| State S3 bucket and its controls | Yes | No | No |
| Native S3 lockfile objects | Yes, as backend state operations | No | No |
| GitHub OIDC provider (`create` mode) | Yes | No | No |
| GitHub OIDC provider (`existing` mode) | No | No | Yes |
| GitHub image-build role | Yes | No | No |
| Backend/frontend ECR repositories and lifecycle | Yes | No | No |
| Redis AUTH secret container and version | Yes | No | No |
| GitHub deployment role | No | Yes | No |
| VPC, subnets, routes, endpoints, security groups | No | Yes | No |
| ALB, listeners, target groups | No | Yes | No |
| ECS cluster, task definitions and services | No | Yes | No |
| RDS instance and parameter/subnet groups | No | Yes | No |
| Redis replication group and subnet group | No | Yes | No |
| EFS filesystem, access point and mount targets | No | Yes | No |
| CloudWatch logs, alarms and dashboard | No | Yes | No |
| AWS Backup resources | No | Yes | No |
| Runtime secret containers | No | Yes | No |
| Runtime secret values | No | No | Yes, secure post-apply population |
| ACM certificate issuance/validation | No | No | Yes |
| Route 53 alias when `route53_zone_id` is set | No | Yes | No |
| External DNS binding when Route 53 is not selected | No | No | Yes |
| GitHub `staging` environment and variables | No | No | Yes |

## GitHub contract

The manual build workflow keeps the pre-bootstrap contract:

- `AWS_STAGING_REGION`
- `AWS_STAGING_ROLE_ARN` — bootstrap image-build role ARN
- `AWS_STAGING_BACKEND_ECR_REPOSITORY`
- `AWS_STAGING_FRONTEND_ECR_REPOSITORY`

The deploy workflow now uses `AWS_STAGING_DEPLOY_ROLE_ARN`, produced by the full staging root. No workflow accepts static AWS keys; both use `id-token: write` and short-lived OIDC credentials.

GitHub environment creation/protection is outside this implementation and remains a required administrator action.

## Cost boundary

Bootstrap contains only S3 state, IAM/OIDC, two ECR repositories, and one Secrets Manager secret. It does not contain a NAT Gateway, ALB, ECS service, RDS instance, Redis cluster, or EFS filesystem. The approved monthly budget remains USD 50, but the alert destination and AWS account are still missing operator inputs.

## Current execution boundary

This implementation authorizes source changes and static validation only. It does not authorize Terraform plan/apply, AWS mutation, GitHub environment mutation, image publication, or paid-resource creation.
