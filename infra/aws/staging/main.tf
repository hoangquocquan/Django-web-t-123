data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

locals {
  name = "${var.project_name}-${var.environment}"
  azs  = length(var.availability_zones) == 2 ? var.availability_zones : slice(data.aws_availability_zones.available.names, 0, 2)

  tags = {
    Project      = var.project_name
    Environment  = var.environment
    ManagedBy    = "terraform"
    Repository   = var.repository
    Owner        = var.owner
    CostCenter   = var.cost_center
    CandidateSHA = var.candidate_sha
  }

  backend_image  = "${var.backend_ecr_repository_url}@${var.backend_image_digest}"
  frontend_image = "${var.frontend_ecr_repository_url}@${var.frontend_image_digest}"

  expected_backend_ecr_url  = "${var.aws_account_id}.dkr.ecr.${var.aws_region}.${data.aws_partition.current.dns_suffix}/${local.name}/backend"
  expected_frontend_ecr_url = "${var.aws_account_id}.dkr.ecr.${var.aws_region}.${data.aws_partition.current.dns_suffix}/${local.name}/frontend"
  expected_backend_ecr_arn  = "arn:${data.aws_partition.current.partition}:ecr:${var.aws_region}:${var.aws_account_id}:repository/${local.name}/backend"
  expected_frontend_ecr_arn = "arn:${data.aws_partition.current.partition}:ecr:${var.aws_region}:${var.aws_account_id}:repository/${local.name}/frontend"
}

check "selected_account" {
  assert {
    condition     = data.aws_caller_identity.current.account_id == var.aws_account_id
    error_message = "The active AWS account must match aws_account_id."
  }
}

check "bootstrap_resource_binding" {
  assert {
    condition = (
      var.backend_ecr_repository_url == local.expected_backend_ecr_url &&
      var.frontend_ecr_repository_url == local.expected_frontend_ecr_url &&
      var.backend_ecr_repository_arn == local.expected_backend_ecr_arn &&
      var.frontend_ecr_repository_arn == local.expected_frontend_ecr_arn &&
      startswith(var.redis_auth_secret_arn, "arn:${data.aws_partition.current.partition}:secretsmanager:${var.aws_region}:${var.aws_account_id}:secret:/${var.project_name}/${var.environment}/redis-auth-") &&
      (!var.enable_github_deploy_role || var.github_oidc_provider_arn == "arn:${data.aws_partition.current.partition}:iam::${var.aws_account_id}:oidc-provider/token.actions.githubusercontent.com")
    )
    error_message = "ECR URL/ARN, Redis secret ARN and enabled OIDC provider inputs must match bootstrap-owned/selected resources in the selected account and region."
  }
}
