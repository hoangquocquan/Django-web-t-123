# AWS Security Simulation

## IAM Concept

IAM controls who or what can access AWS resources.

Local equivalent:

- container environment variables
- Docker network isolation
- service-specific credentials

## Environment Secrets

The lab uses local-only demo credentials such as:

```text
minio-local-password
mecprecision-local-password
aws-lab-local-secret-only
```

These are not production secrets.

## Container Security

Existing Dockerfile runs the Django application as a non-root user.

## Network Isolation

The lab uses a private Docker bridge network:

```text
aws-lab
```

Only selected ports are exposed:

- `8088` for Nginx
- `9000` for MinIO API
- `9001` for MinIO console

## AWS Production Equivalent

- IAM roles for ECS tasks.
- Security groups for ALB, ECS, RDS, and Redis.
- Secrets Manager or SSM Parameter Store.
- Private subnets for databases.
- CloudTrail and GuardDuty.

## Learning Outcome

You learn security boundaries locally before designing real IAM policies.
