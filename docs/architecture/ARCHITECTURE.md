# Architecture

## Application architecture

```mermaid
flowchart LR
    C[Customer] --> R[React Frontend]
    R --> D[Django REST API]
    D --> P[(PostgreSQL)]
    D --> A[AI Sales Assistant]
    A --> G[RAG Retrieval]
    G --> P
    A --> L[LLM]
    D --> Q[RFQ]
    Q --> N[n8n]
    N --> LINE[LINE]
```

## AWS-oriented staging / target architecture

```mermaid
flowchart LR
    I[Internet] --> ALB[Application Load Balancer]
    ALB --> ECS[ECS Service]
    ECS --> RDS[(RDS PostgreSQL)]
    ECS --> S3[S3]
    ECS --> CW[CloudWatch]
    ECS --> SM[Secrets Manager]
    GA[GitHub Actions] --> ECR[ECR]
    ECR --> ECS
```

The AWS diagram describes staging / target architecture, not a claim that every component is in production. Secrets and credentials must never be committed.
