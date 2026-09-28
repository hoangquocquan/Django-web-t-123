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

  backend_image  = "${aws_ecr_repository.backend.repository_url}@${var.backend_image_digest}"
  frontend_image = "${aws_ecr_repository.frontend.repository_url}@${var.frontend_image_digest}"
}

check "selected_account" {
  assert {
    condition     = data.aws_caller_identity.current.account_id == var.aws_account_id
    error_message = "The active AWS account must match aws_account_id."
  }
}
