# AWS staging bootstrap Terraform root

This independent root owns only the state foundation, GitHub image-build identity, two staging ECR repositories, and Redis AUTH secret prerequisite. It must use a state separate from `../staging`.

Permitted repository validation:

```text
terraform fmt -check -recursive
terraform init -backend=false -input=false
terraform validate -no-color
```

Do not run plan or apply without separate authorization.

## First state-foundation bootstrap

The state bucket cannot contain the state that creates it. The first authorized execution therefore uses local state on a controlled encrypted operator device. After the S3 bucket exists:

1. Add an empty `backend "s3" {}` block to the `terraform` block.
2. Prepare a non-secret partial backend file with the bucket, an operator-approved bootstrap state key, `ap-northeast-1`, `encrypt = true`, and `use_lockfile = true`.
3. Run an explicitly reviewed state migration.
4. Verify remote state, bucket versioning, and lockfile behavior before securely disposing of the local copy under organizational policy.

Credentials never belong in backend configuration. The full staging root uses a distinct state key.

## Sensitive state warning

`redis_auth_token` is written through `aws_secretsmanager_secret_version` and is therefore present in bootstrap Terraform state even though the variable is marked sensitive and no output exposes it. Access to bootstrap state is credential access. Restrict S3 state and lock objects to the minimum operator/automation principals, preserve version history securely, and never publish state as CI evidence.
