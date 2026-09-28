# AWS staging cost guardrails

- Monthly budget: `MONTHLY_BUDGET_TO_BE_APPROVED`; no amount is assumed.
- Create a budget alert before paid provisioning; destination is operator-supplied.
- Tag every resource with `Project`, `Environment=staging`, `ManagedBy=terraform`, `Repository`, `Owner`, `CostCenter`, `CandidateSHA`.
- Use scheduled shutdown only for nonessential staging; never schedule deletion of database/media.
- Bound CloudWatch retention, snapshot retention and ECR image count.
- NAT Gateway is a material recurring cost: standard mode preserves egress; cost-optimized mode requires reviewed endpoints and must not weaken isolation.
- AI/GPU remains disabled initially and is the largest optional cost driver.

No AWS Budget, alert, resource or subscription was created by this change.
