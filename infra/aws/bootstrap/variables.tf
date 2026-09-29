variable "aws_region" {
  description = "AWS region selected by the staging operator."
  type        = string
  default     = "ap-northeast-1"

  validation {
    condition     = can(regex("^[a-z]{2}(-gov)?-[a-z]+-[0-9]+$", var.aws_region))
    error_message = "aws_region must be a valid AWS region name."
  }
}

variable "aws_account_id" {
  description = "Approved 12-digit staging AWS account ID."
  type        = string

  validation {
    condition     = can(regex("^[0-9]{12}$", var.aws_account_id))
    error_message = "aws_account_id must contain exactly 12 digits."
  }
}

variable "project_name" {
  type    = string
  default = "django-web-t-123"

  validation {
    condition     = var.project_name == "django-web-t-123"
    error_message = "project_name must be django-web-t-123 to preserve the exact staging resource identities."
  }
}

variable "environment" {
  type    = string
  default = "staging"

  validation {
    condition     = var.environment == "staging"
    error_message = "This bootstrap root is staging-only; environment must equal staging."
  }
}

variable "repository" {
  description = "Exact GitHub owner/repository permitted by the OIDC trust policy."
  type        = string
  default     = "hoangquocquan/Django-web-t-123"

  validation {
    condition     = var.repository == "hoangquocquan/Django-web-t-123"
    error_message = "repository must remain hoangquocquan/Django-web-t-123 for this staging binding."
  }
}

variable "owner" {
  description = "Approved operational owner tag."
  type        = string
}

variable "cost_center" {
  description = "Approved staging cost-center tag."
  type        = string
}

variable "state_bucket_name" {
  description = "Globally unique operator-approved S3 bucket name for Terraform state."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$", var.state_bucket_name)) && !can(regex("\\.\\.", var.state_bucket_name)) && !can(regex("^[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+$", var.state_bucket_name))
    error_message = "state_bucket_name must be a valid 3-63 character S3 bucket name and cannot be an IPv4 address."
  }
}

variable "oidc_provider_mode" {
  description = "Create the account-level GitHub OIDC provider, or use an existing provider ARN."
  type        = string

  validation {
    condition     = contains(["create", "existing"], var.oidc_provider_mode)
    error_message = "oidc_provider_mode must be create or existing."
  }
}

variable "existing_github_oidc_provider_arn" {
  description = "Existing GitHub Actions OIDC provider ARN; required only when oidc_provider_mode is existing."
  type        = string
  default     = null
  nullable    = true

  validation {
    condition = (
      var.oidc_provider_mode == "create"
      ? var.existing_github_oidc_provider_arn == null
      : var.existing_github_oidc_provider_arn != null && can(regex("^arn:[^:]+:iam::[0-9]{12}:oidc-provider/token.actions.githubusercontent.com$", var.existing_github_oidc_provider_arn))
    )
    error_message = "Set existing_github_oidc_provider_arn only for existing mode, using the exact GitHub Actions provider ARN."
  }
}

variable "redis_auth_token" {
  description = "Redis AUTH token written to Secrets Manager. This sensitive value is stored in Terraform state."
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.redis_auth_token) >= 16 && length(var.redis_auth_token) <= 128 && can(regex("^[A-Za-z0-9!&#$^<>-]+$", var.redis_auth_token))
    error_message = "redis_auth_token must be 16-128 characters and use only alphanumerics or ! & # $ ^ < > -."
  }
}
