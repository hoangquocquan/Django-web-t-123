terraform {
  required_version = ">= 1.6.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0, < 6.0"
    }
  }

  # The first state-foundation apply must use tightly controlled local state.
  # After the bucket exists, add `backend "s3" {}` and migrate with an
  # operator-reviewed partial backend configuration. See README.md.
}

provider "aws" {
  region              = var.aws_region
  allowed_account_ids = [var.aws_account_id]

  default_tags {
    tags = local.tags
  }
}

data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}

check "selected_account" {
  assert {
    condition     = data.aws_caller_identity.current.account_id == var.aws_account_id
    error_message = "The active AWS account must match aws_account_id."
  }
}

check "existing_oidc_provider_account" {
  assert {
    condition = (
      var.oidc_provider_mode == "create" ||
      var.existing_github_oidc_provider_arn == "arn:${data.aws_partition.current.partition}:iam::${var.aws_account_id}:oidc-provider/token.actions.githubusercontent.com"
    )
    error_message = "The existing GitHub OIDC provider must belong to aws_account_id in the active AWS partition."
  }
}
