terraform {
  required_version = ">= 1.6.0, < 2.0.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = ">= 5.0, < 6.0" }
  }
  # Configure an operator-owned encrypted/versioned S3 backend after account selection.
  # backend "s3" {}
}

provider "aws" {
  region = var.aws_region
  default_tags { tags = local.tags }
}

locals {
  name = "${var.project_name}-${var.environment}"
  tags = {
    Project      = var.project_name, Environment = var.environment, ManagedBy = "terraform",
    Repository   = var.repository, Owner = var.owner, CostCenter = var.cost_center,
    CandidateSHA = var.candidate_sha
  }
}
