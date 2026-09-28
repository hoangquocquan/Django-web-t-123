# AWS staging architecture

```mermaid
flowchart LR
  DNS[Route53 or external DNS] --> ALB[ALB HTTPS / ACM]
  ALB -->|/api/*| ECS[Django ECS Fargate]
  ALB -->|/*| WEB[Frontend/Nginx ECS Fargate]
  ECS --> RDS[(Private RDS PostgreSQL)]
  ECS --> REDIS[(Private ElastiCache rediss)]
  ECS --> EFS[(Encrypted EFS MEDIA_ROOT)]
  ECS --> SECRETS[Secrets Manager]
  ECS --> CW[CloudWatch logs/metrics]
  RDS --> BACKUP[AWS Backup / RDS snapshots]
  EFS --> BACKUP
  CI[GitHub OIDC CI] --> ECR[ECR immutable SHA images]
  ECR --> ECS
```

Public subnets contain ALB only; app/data services are private. Security groups allow ALB→ECS, ECS→RDS/Redis/EFS only. Same-origin HTTPS routes API and SPA. Detailed health/metrics are protected. Build exact SHA, scan, publish immutable digests, inject secrets, snapshot, run one migration task, update ECS and smoke. Rollback uses a prior digest only after schema review; otherwise forward fix/restore. EFS is used because current Django uses `FileSystemStorage`; S3 media is excluded pending a separate application feature.
