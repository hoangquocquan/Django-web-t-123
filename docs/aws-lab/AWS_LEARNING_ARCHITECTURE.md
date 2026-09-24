# AWS Learning Architecture

## Complete Local Architecture

```mermaid
flowchart TD
    USER["Browser"] --> NGINX["Nginx container\nALB simulation"]
    NGINX --> DJANGO["Django container\nEC2/ECS simulation"]
    DJANGO --> POSTGRES["PostgreSQL container\nRDS simulation"]
    DJANGO --> MINIO["MinIO container\nS3 simulation"]
    GHA["GitHub Actions"] --> TEST["Tests + Docker build\nCI/CD simulation"]
```

## Request Flow

1. Browser opens `http://localhost:8088/`.
2. Nginx receives the request.
3. Nginx forwards to Django.
4. Django renders public pages or APIs.
5. Django reads/writes local database or storage simulation as needed.

## Data Flow

```mermaid
sequenceDiagram
    participant User
    participant Nginx
    participant Django
    participant PostgreSQL
    participant MinIO

    User->>Nginx: HTTP request
    Nginx->>Django: Proxy request
    Django->>PostgreSQL: Query relational data
    Django->>MinIO: Future object storage access
    Django-->>Nginx: HTML/API response
    Nginx-->>User: Response
```

## AWS Equivalent Mapping

| AWS service | Local service |
| --- | --- |
| EC2 / ECS | Django container |
| RDS PostgreSQL | PostgreSQL container |
| S3 | MinIO |
| ALB | Nginx |
| GitHub Actions deployment | GitHub Actions lab workflow |

## Safety Boundary

This lab is local only. It does not require AWS credentials and does not create
cloud resources.
