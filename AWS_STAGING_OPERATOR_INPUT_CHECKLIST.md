# AWS staging operator input checklist

Never place secret values in this checklist.

| Input | Current decision/status | Required before |
|---|---|---|
| AWS account ID | `REQUIRED_OPERATOR_INPUT` | Bootstrap plan |
| AWS region | `ap-northeast-1` | Bootstrap plan |
| Monthly budget | `USD 50` | Bootstrap plan |
| Budget alert thresholds | `50%`, `80%`, `100%` | Bootstrap plan |
| Budget alert destination | `REQUIRED_OPERATOR_INPUT` | Bootstrap plan |
| Owner and cost center | `REQUIRED_OPERATOR_INPUT` | Bootstrap plan |
| State bucket name | `REQUIRED_OPERATOR_INPUT` | Bootstrap plan |
| Bootstrap/staging state keys | `REQUIRED_OPERATOR_INPUT`; must differ | Backend migration/full init |
| State encryption | `SSE-S3` | Bootstrap plan |
| State locking | `NATIVE_S3_LOCKFILE` | Backend migration |
| OIDC provider mode | `REQUIRED_OPERATOR_INPUT`: `create` or `existing` | Bootstrap plan |
| Existing OIDC provider ARN | Required only for `existing` mode | Bootstrap plan |
| Redis AUTH token | Required through approved secret channel; never document value | Bootstrap plan |
| Staging hostname | `REQUIRED_OPERATOR_INPUT` | Full staging plan |
| DNS provider/ownership | `REQUIRED_OPERATOR_INPUT` | Full staging plan |
| ACM certificate ARN | `REQUIRED_OPERATOR_INPUT` | Full staging plan |
| GitHub `staging` administrator | `REQUIRED_OPERATOR_INPUT` | Image build |
| Exact candidate SHA | Required after bootstrap review | Image build |
| Backend/frontend image digests | Blocked until image build | Full staging plan |

## Bootstrap output handoff

Record only non-secret outputs from the reviewed bootstrap state: state bucket identity, OIDC provider ARN, image-build role ARN, ECR names/URLs/ARNs, and Redis secret ARN. Never record `redis_auth_token` or state contents.
