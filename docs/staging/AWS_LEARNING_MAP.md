# AWS learning map

| Service | What it is | Why this project needs it | Main risk / lesson |
|---|---|---|---|
| IAM | identities/policies | least-privilege ECS, CI, backup | avoid wildcard actions; learn trust conditions |
| VPC | private network | isolate app/data | understand subnets/routes |
| Security Groups | stateful firewall | only ALB→ECS→data paths | never broad ingress |
| ECR | image registry | immutable SHA artifacts | use digests/scanning |
| ECS/Fargate | managed containers | Django/frontend without EC2 | separate task/execution roles |
| ALB | HTTPS routing | `/api/*` backend, SPA frontend | health/proxy correctness |
| ACM | certificates | TLS termination | region and DNS validation |
| Route 53 | DNS | staging hostname | avoid production hostname mix-up |
| RDS | PostgreSQL | relational data | private/TLS/backups |
| ElastiCache | Redis | cache/session/rate controls | rediss/auth/private network |
| EFS | durable filesystem | current FileSystemStorage media | access points/backup |
| Secrets Manager | secret store | runtime injection | no values in Git/logs |
| CloudWatch | logs/metrics/alarms | operational evidence | retention and alert routing |
| AWS Backup | recovery | RDS/EFS restore | test restore |
| GitHub OIDC | keyless CI auth | ECR/deploy without long-lived keys | restrict repository/branch/environment |

LINE/n8n production send is not part of this staging design.
