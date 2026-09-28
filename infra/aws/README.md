# AWS staging binding

`staging/` is the staging-only Terraform root for the reviewed candidate SHA. It defines the VPC/subnet tiers, public HTTPS ALB, private ECS Fargate services, private TLS data services, encrypted EFS media, immutable ECR repositories, Secrets Manager bindings, CloudWatch controls, AWS Backup and optional staging GitHub OIDC role.

Safety properties implemented in code:

- the `environment` variable accepts only `staging`;
- the AWS provider is restricted to the approved account ID;
- ECS tasks receive no public IP and only the ALB is in public subnets;
- RDS and Redis accept traffic only from backend tasks;
- EFS uses encryption, TLS and IAM-authorized access-point mounts;
- RDS has `rds.force_ssl=1`; Redis has at-rest/in-transit encryption plus operator-secret authentication;
- images are digest-pinned and ECR tags are immutable;
- LINE send and supported AI runtime flags are explicitly disabled;
- migration has a separate task definition and is not part of web startup;
- no Terraform backend, state, credential or secret value is committed.

The configuration is not production infrastructure and does not authorize provisioning. Account, region, hostname, certificate, DNS, budget, image digests, secure Redis token, runtime secret values, remote state and explicit operator authorization are still required.
