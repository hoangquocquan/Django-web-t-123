# AWS staging binding

`bootstrap/` is the prerequisite Terraform root. It owns remote-state foundation, GitHub image-build OIDC binding, immutable ECR repositories and the Redis AUTH secret/version.

`staging/` is the full staging Terraform root for the reviewed candidate SHA. It consumes bootstrap outputs and defines the VPC/subnet tiers, public HTTPS ALB, private ECS Fargate services, private TLS data services, encrypted EFS media, runtime Secrets Manager containers, CloudWatch controls, AWS Backup and a distinct optional GitHub deployment role.

Safety properties implemented in code:

- the `environment` variable accepts only `staging`;
- the AWS provider is restricted to the approved account ID;
- ECS tasks receive no public IP and only the ALB is in public subnets;
- RDS and Redis accept traffic only from backend tasks;
- EFS uses encryption, TLS and IAM-authorized access-point mounts;
- RDS has `rds.force_ssl=1`; Redis has at-rest/in-transit encryption plus operator-secret authentication;
- images are composed from bootstrap-owned ECR URLs and validated immutable digests;
- LINE send and supported AI runtime flags are explicitly disabled;
- migration has a separate task definition and is not part of web startup;
- no populated backend configuration, state, credential or secret value is committed.

The configuration is not production infrastructure and does not authorize provisioning. Account, region, hostname, certificate, DNS, budget, image digests, secure Redis token, runtime secret values, remote state and explicit operator authorization are still required.
