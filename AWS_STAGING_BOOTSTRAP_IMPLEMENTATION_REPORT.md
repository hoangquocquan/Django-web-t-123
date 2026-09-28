# AWS staging bootstrap implementation report

## Git and scope

```text
START_HEAD=4556d917e6bbabe126ee7b0fe554b4cf18afd1ef
FINAL_HEAD=PR_HEAD (exact immutable SHA is recorded by Git/PR metadata because a commit cannot contain its own hash)
BASE_MAIN=4556d917e6bbabe126ee7b0fe554b4cf18afd1ef
BRANCH=feat/aws-staging-bootstrap
WORKTREE=C:\Users\hoang\.codex\worktrees\aws-staging-bootstrap\WEB Ô TÔ DJANGO
BOOTSTRAP_ROOT_CREATED=YES
FULL_ROOT_REFACTORED=YES
DUPLICATE_RESOURCE_OWNERSHIP=NO
```

The unrelated primary checkout was not modified. The implementation adds no application/business-logic changes.

## Implementation

- Added independent `infra/aws/bootstrap` ownership for the S3 state foundation, optional GitHub account OIDC provider, image-build role, backend/frontend ECR repositories and lifecycle policies, and Redis AUTH secret/version.
- Refactored `infra/aws/staging` to consume ECR URLs/ARNs and the Redis secret ARN rather than create those resources.
- Preserved strict `sha256:<64 lowercase hex>` digest validation and URL-plus-digest image composition.
- Split GitHub identity duties: the build workflow uses the bootstrap image-build role; the deploy workflow uses the full-root deployment role.
- Added an empty S3 backend declaration to the full root and documented the one-time bootstrap local-state migration.
- Added a no-credentials/no-plan/no-apply CI workflow that formats, initializes with `-backend=false`, and validates both Terraform roots.

## Terraform validation

```text
BOOTSTRAP_TERRAFORM_FMT=PASS
BOOTSTRAP_TERRAFORM_INIT=PASS (-backend=false -input=false)
BOOTSTRAP_TERRAFORM_VALIDATE=PASS

STAGING_TERRAFORM_FMT=PASS
STAGING_TERRAFORM_INIT=PASS (-backend=false -input=false)
STAGING_TERRAFORM_VALIDATE=PASS
```

Terraform CLI: v1.16.2. AWS provider selected by the lock files: v5.100.0.

No Terraform plan or apply command was run.

## Regression and security validation

```text
AWS_LEARNING_LAB=PASS (8 passed)
DOCKER_COMPOSE_CONFIG=PASS
SAST=PASS (Bandit: 0 High severity findings)
SECRET_SCAN=NO_MATCH_IN_CHANGED_INFRA/DOCS STATIC PATTERN SCAN; FULL-HISTORY GITLEAKS REQUIRED IN PR CI

SECRETS_FOUND=NO_IN_CHANGED_FILES
STATE_FILE_FOUND=NO_TRACKED_STATE
OIDC_TRUST=EXACT audience sts.amazonaws.com AND subject repo:hoangquocquan/Django-web-t-123:environment:staging
IAM_SCOPE=LEAST_PRIVILEGE; ONLY ECR GetAuthorizationToken AND documented Describe APIs use unavoidable Resource star
ECR_IMMUTABILITY=ENFORCED
```

Additional checks:

```text
ACTION_STAR_UNJUSTIFIED=NO
RESOURCE_STAR_UNJUSTIFIED=NO
STATIC_AWS_KEYS=NO
SECRET_VALUES_COMMITTED=NO
TFSTATE_COMMITTED=NO
REAL_TFVARS_COMMITTED=NO
LONG_LIVED_GITHUB_AWS_KEYS=NO
OIDC_TRUST_BROADENED=NO
```

The S3 HTTPS-only deny policy intentionally uses `s3:*` so every insecure S3 action is denied against the exact bucket and object resources. `ecr:GetAuthorizationToken` requires `Resource = "*"`. Existing full-root Describe API stars remain documented where AWS does not consistently support resource scoping.

## Cost boundary

The bootstrap root contains no NAT Gateway, ALB, ECS service, RDS instance, Redis cluster, or EFS filesystem. It contains only the small prerequisite layer: S3 state foundation, IAM/OIDC, ECR, and the Redis Secrets Manager secret/version.

## AWS boundary

```text
AWS_PLAN_EXECUTED=NO
AWS_APPLY_EXECUTED=NO
AWS_MUTATION=NO
PAID_RESOURCE_CREATED=NO
GITHUB_ENVIRONMENT_CREATED=NO
```

## Decision

```text
READY_FOR_BOOTSTRAP_FINAL_REVIEW=YES
READY_FOR_BOOTSTRAP_PLAN=NO
READY_FOR_BOOTSTRAP_APPLY=NO
READY_FOR_FULL_STAGING_PLAN=NO
```

The remaining blockers are operator-supplied AWS account ID, state bucket/keys, budget alert destination, OIDC provider mode/ARN, Redis token delivery, GitHub environment administration, and later hostname/DNS/ACM/image digest inputs.
