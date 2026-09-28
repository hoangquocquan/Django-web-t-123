# AWS staging cost guardrails

- Monthly budget and alert destination are mandatory operator inputs; no amount is assumed in code.
- Every resource receives `Project`, `Environment=staging`, `ManagedBy=terraform`, `Repository`, `Owner`, `CostCenter`, and `CandidateSHA` tags where AWS supports them.
- Fargate services default to zero tasks during binding. The gated deployment workflow raises them to one or two only after migration succeeds.
- RDS defaults to single-AZ `db.t4g.small`, 30 GiB gp3 with bounded autoscaling. Redis defaults to one `cache.t4g.micro`; a second node is explicit.
- CloudWatch logs default to 14 days, backups to 7 days, and each ECR repository retains 20 images.
- No NAT Gateway is defined. Private tasks use four interface endpoints (ECR API/DKR, Logs, Secrets Manager) plus a no-hourly-charge S3 gateway endpoint. Interface endpoints have an hourly cost; compare that cost with a NAT Gateway before authorization, but do not weaken private isolation to save money.
- ALB, RDS, Redis, EFS, interface endpoints, backups and Fargate are paid services if applied. This code creates none by itself.
- AI/GPU and unrestricted internet egress remain disabled. Enabling an external provider requires a separate design and cost review.
- Scheduled shutdown may be used for nonessential compute only. Never schedule deletion of databases, media or backups.

No AWS Budget, alert, resource or subscription was created by this remediation.
