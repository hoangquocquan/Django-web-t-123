# AWS Learning Lab

This folder simulates AWS architecture locally. It does not create cloud
resources and does not require an AWS account.

## Local AWS Concept Mapping

| AWS concept | Local lab equivalent |
| --- | --- |
| EC2 / ECS service | Django Docker container |
| RDS PostgreSQL | PostgreSQL container |
| S3 | MinIO container |
| Application Load Balancer | Nginx reverse proxy |
| CI/CD | GitHub Actions simulation workflow |

## Start

```powershell
docker compose -f docker/aws-lab/docker-compose.aws-lab.yml up --build
```

Open:

- Public website: `http://localhost:8088/`
- Health check: `http://localhost:8088/api/v1/health/`
- MinIO console: `http://localhost:9001/`

## Stop

```powershell
docker compose -f docker/aws-lab/docker-compose.aws-lab.yml down
```

## Safety

This lab is local only. It does not deploy AWS resources.
