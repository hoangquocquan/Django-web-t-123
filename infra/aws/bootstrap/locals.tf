locals {
  name = "${var.project_name}-${var.environment}"

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Repository  = var.repository
    Owner       = var.owner
    CostCenter  = var.cost_center
    Layer       = "bootstrap"
  }

  github_oidc_provider_arn = var.oidc_provider_mode == "create" ? aws_iam_openid_connect_provider.github[0].arn : var.existing_github_oidc_provider_arn
}
