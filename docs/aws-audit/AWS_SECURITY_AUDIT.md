# AWS Security Audit

## Current Status

No IAM inventory, security group export, AWS Secrets Manager configuration, or AWS account policy evidence was found.

## Repository Security Evidence

Positive controls:

- `.env` is ignored.
- `.env.example` avoids real production secrets.
- Django production settings enable secure cookie and HTTPS controls.
- Dockerfile runs as non-root user.
- CI exists for automated checks.

Observed gaps:

- No AWS IAM role design.
- No security group rules.
- No Secrets Manager or SSM Parameter Store integration.
- No WAF configuration.
- No production audit logging evidence.

## Exposed Credentials Check

No AWS access key pattern was identified in the inspected AWS-related evidence.

Known local-only placeholders:

- Docker Compose local Postgres password.
- Docker local secret key.
- `.env.example` demo values.

## Recommendation

Before production:

- Use IAM roles for tasks/instances.
- Store secrets in AWS Secrets Manager or SSM Parameter Store.
- Restrict RDS to private subnets.
- Restrict ALB ingress to `443`.
- Add AWS WAF if public traffic grows.
- Enable CloudTrail and GuardDuty.
