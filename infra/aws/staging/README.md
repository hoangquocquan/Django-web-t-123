# Staging Terraform root

This root is staging-only. It contains an empty S3 backend declaration and no populated backend configuration or real operator values. Supply an operator-reviewed partial configuration with a state key distinct from the bootstrap root.

Permitted local validation:

```text
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
```

Do not run `terraform plan` without approved account/operator context. Never run `terraform apply` as part of repository remediation.

Copy `terraform.tfvars.example` to ignored `terraform.tfvars` only in an authorized operator environment. Replace every placeholder. Supply ECR URLs/ARNs, the Redis secret ARN, and the OIDC provider ARN from bootstrap outputs; this root must not import or own those bootstrap resources. The AWS provider reads the Redis secret to configure ElastiCache, so use encrypted/versioned remote state before any authorized plan/apply and tightly restrict state access.

Before services can start, populate the four Terraform-created Secrets Manager containers out-of-band:

- `django-secret-key`
- `database-url`
- `redis-url`
- `metrics-token`

The database URL must use PostgreSQL credentials and the Redis URL must use `rediss://` with authentication. Do not output either value.

Private application egress is deliberately limited to VPC endpoints; there is no NAT Gateway. Route 53 record creation is optional. External DNS operators use the `alb_dns_name` output.
