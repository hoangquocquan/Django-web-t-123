# AWS Staging Bootstrap — Final Blocker Remediation

Remediation date: 2026-09-29 (Asia/Tokyo)

```text
PR_NUMBER=15
START_HEAD=2e4a26d7ce68e9641a955f1bdc2dcb4267028bfd
FINAL_HEAD=SELF (resolve the commit containing this report with git rev-parse HEAD)
BASE_MAIN=4556d917e6bbabe126ee7b0fe554b4cf18afd1ef

BLOCKER_1_EXACT_ECR_IDENTITIES=RESOLVED
BLOCKER_2_REDIS_DOC_CONTRACT=RESOLVED
BLOCKER_3_BUDGET_THRESHOLDS=RESOLVED
```

`FINAL_HEAD` is expressed as `SELF` because a Git commit cannot contain its own hash: changing the report to insert that hash would create a different hash. The exact pushed PR head and its CI result are recorded in the final handoff after push.

## Blocker 1 — exact ECR identities

Both Terraform roots retain a single `project_name` source of truth and now validate that it equals `django-web-t-123`. Both roots already restrict `environment` to `staging`. The bootstrap ECR resources continue deriving their names from `local.name`, so there is no alternate naming path.

```text
PROJECT_NAME_INVARIANT=YES
BACKEND_ECR_IDENTITY=django-web-t-123-staging/backend
FRONTEND_ECR_IDENTITY=django-web-t-123-staging/frontend
```

## Blocker 2 — Redis ownership contract

The staging variable now states that its ARN comes from the bootstrap-owned Secrets Manager secret, that staging consumes only the reference, and that the secret value must not be put in staging tfvars. The example ARN now uses the actual bootstrap identity prefix `/django-web-t-123/staging/redis-auth` and satisfies the full-root binding shape.

```text
REDIS_SECRET_OWNERSHIP_DOC_MATCH=YES
REDIS_SECRET_EXAMPLE_MATCH=YES
```

## Blocker 3 — budget alert thresholds

The operator checklist, readiness report, bootstrap runbook, and cost guardrails now consistently document the approved monthly amount and proposed alert thresholds. The notification destination remains an actual operator input; no email address was invented and no AWS Budget resource was added.

```text
MONTHLY_BUDGET_USD=50
BUDGET_ALERT_THRESHOLDS=50%,80%,100%
BUDGET_ALERT_DESTINATION=REQUIRED_OPERATOR_INPUT
```

## Local validation

The following checks were executed after the remediation:

```text
BOOTSTRAP_TERRAFORM_FMT=PASS
BOOTSTRAP_TERRAFORM_INIT_BACKEND_FALSE=PASS
BOOTSTRAP_TERRAFORM_VALIDATE=PASS

STAGING_TERRAFORM_FMT=PASS
STAGING_TERRAFORM_INIT_BACKEND_FALSE=PASS
STAGING_TERRAFORM_VALIDATE=PASS

AWS_LEARNING_LAB=PASS (8 tests)
SAST=PASS (Bandit; 0 High findings)
SECRET_SCAN=PENDING_EXACT_HEAD_CI
IAC_SCAN=PENDING_EXACT_HEAD_CI
CI=PENDING_EXACT_HEAD_CI
```

Gitleaks and Trivy are not installed locally. Their results must come from the exact pushed PR head in GitHub Actions; they are intentionally not claimed as passing in advance.

## Static security and ownership review

```text
STATIC_AWS_KEYS=NO
SECRET_VALUES_COMMITTED=NO
TFSTATE_COMMITTED=NO
REAL_TFVARS_COMMITTED=NO
OIDC_TRUST_BROADENED=NO
DUPLICATE_RESOURCE_OWNERSHIP=NO
```

No OIDC, IAM, resource ownership, or runtime architecture code changed in this remediation. The only Terraform behavior change is validation of the existing project-name contract.

## Scope

```text
APPLICATION_CODE_CHANGED=NO
BUSINESS_LOGIC_CHANGED=NO
DATABASE_SCHEMA_CHANGED=NO
RAG_CHANGED=NO
AI_SALES_CHANGED=NO
LINE_N8N_PRODUCTION_BEHAVIOR_CHANGED=NO
SCOPE_CLEAN=YES
```

## Mutation boundary

```text
AWS_PLAN_EXECUTED=NO
AWS_APPLY_EXECUTED=NO
AWS_MUTATION=NO
PAID_RESOURCE_CREATED=NO
IMAGE_PUBLICATION=NO
GITHUB_ADMIN_MUTATION=NO
MERGE_PERFORMED=NO
```

Pushing the source commit to the existing PR branch is the only authorized remote write in this remediation. The PR must receive an independent final re-review after exact-head CI completes.
