# AWS staging binding

This is a reviewable, staging-only Terraform definition for the candidate SHA. It is intentionally not a production stack and does not create resources by itself.

Architecture: Route 53/external DNS → ACM → ALB → ECS Fargate; private RDS PostgreSQL, ElastiCache Redis/Valkey, EFS media, ECR artifacts, Secrets Manager, CloudWatch and AWS Backup.

Safety:

- Run only `terraform fmt`, `terraform init -backend=false`, `terraform validate`, and review-only `terraform plan` after operator context exists.
- Never run `terraform apply`/`destroy` in this feature.
- Do not commit state, credentials, secret values, plan output or real account/domain values.
- `environment` is validated as `staging`; `LINE_SEND_ENABLED` and anonymous AI flags remain false in the eventual ECS task definition.
- Remote state is designed as an operator-owned encrypted/versioned S3 backend with the locking mechanism supported by the chosen Terraform workflow; no state resources are created here.

The root configuration is deliberately readable. Security groups, ECS task definitions, ALB listeners/target groups, IAM roles, OIDC and detailed observability alarms remain platform-binding follow-up work before any plan can be meaningful; see the handoff/report for the explicit gap list.
