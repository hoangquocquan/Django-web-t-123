# AWS Current Architecture

## Current Architecture Summary

The project is AWS-ready at planning and local simulation level, but no real AWS infrastructure is currently represented in the repository.

## Current Flow

```mermaid
flowchart TD
    USER["Local browser"] --> DJANGO["Django local server / Docker web"]
    USER --> LEGACY["Legacy Python HTTP server"]
    DJANGO --> SQLITE["Local SQLite fallback"]
    DJANGO --> PGLOCAL["Local Postgres simulation"]
    DJANGO --> REDISLOCAL["Local Redis simulation"]
    DJANGO --> MEDIA["Local media folder / Docker volume"]
```

## Intended AWS Flow

```mermaid
flowchart TD
    USER["User"] --> ROUTE53["Route53 DNS"]
    ROUTE53 --> CLOUDFRONT["CloudFront CDN"]
    CLOUDFRONT --> ALB["ALB with ACM HTTPS"]
    ALB --> ECS["ECS Fargate Django containers"]
    ECS --> RDS["RDS PostgreSQL"]
    ECS --> REDIS["ElastiCache Redis"]
    ECS --> S3["S3 media/static"]
    ECS --> CW["CloudWatch Logs/Metrics"]
```

## AWS Components

| Component | Current status |
| --- | --- |
| Compute | Not provisioned |
| Database | Local only; RDS not provisioned |
| Storage | Local media/static; S3 not provisioned |
| Networking | Nginx sample only; Route53/ALB/CloudFront not provisioned |
| Security | App-level controls exist; AWS IAM/security groups not documented |
| CI/CD | Test/build pipeline exists; AWS deploy pipeline missing |
| Monitoring | Local docs/checks exist; CloudWatch not provisioned |

## Main Risks

- No production AWS inventory.
- No RDS backup evidence.
- No AWS secret management.
- No CDN/static/media strategy implemented.
- No deployment role/pipeline to AWS.

## Improvement Recommendations

1. Choose ECS Fargate or Elastic Beanstalk target.
2. Create Terraform or CloudFormation baseline.
3. Add RDS PostgreSQL in private subnets.
4. Add S3/CloudFront for static/media.
5. Add GitHub Actions OIDC to AWS.
6. Add CloudWatch logs, metrics, alarms.
