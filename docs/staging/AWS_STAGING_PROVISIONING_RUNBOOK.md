# AWS staging provisioning runbook

Future operator procedure; it does not authorize or execute provisioning.

1. Select account, region, domain, cost category and budget alert.
2. Establish bootstrap IAM and GitHub OIDC trust restricted to this repository/staging environment.
3. Configure encrypted/versioned Terraform state and locking; never commit state.
4. Review/apply VPC, subnets, routes and least-privilege security groups.
5. Create ECR repositories/scanning/lifecycle.
6. Create private TLS RDS with backups.
7. Create private authenticated TLS Redis/Valkey.
8. Create encrypted EFS and mount targets.
9. Create Secrets Manager placeholders; inject values directly after approval.
10. Create ECS roles, cluster, task definitions and CloudWatch log groups.
11. Create ALB, targets, HTTPS/redirect listeners and ACM/DNS binding.
12. Configure CloudWatch dashboards/alarms and alert routing.
13. Configure RDS/EFS backup vault and isolated restore procedure.
14. Build/push exact SHA images and record digests.
15. Snapshot/backup, run one-off ECS migration task, then deploy services.
16. Wait for stability; run health/read-only smoke and complete checklist.
17. Run staging dress rehearsal with LINE production send disabled.

Stop on any failed preflight, migration, health, backup or smoke. No blind destructive rollback.
