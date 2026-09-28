# Staging Terraform root

This root is staging-only. It contains no remote backend configuration and no real operator values.

Permitted local validation:

```text
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
```

Do not run `terraform plan` without approved account/operator context. Never run `terraform apply` as part of repository remediation.

Copy `terraform.tfvars.example` to ignored `terraform.tfvars` only in an authorized operator environment. Replace every placeholder. The Redis authentication token remains in an operator-managed Secrets Manager secret; provide its ARN, not the value. Because the AWS provider must read that secret to configure ElastiCache, use encrypted/versioned remote state before any authorized plan/apply and tightly restrict state access.

Before services can start, populate the four Terraform-created Secrets Manager containers out-of-band:

- `django-secret-key`
- `database-url`
- `redis-url`
- `metrics-token`

The database URL must use PostgreSQL credentials and the Redis URL must use `rediss://` with authentication. Do not output either value.

Private application egress is deliberately limited to VPC endpoints; there is no NAT Gateway. Route 53 record creation is optional. External DNS operators use the `alb_dns_name` output.
