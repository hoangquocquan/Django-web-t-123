variable "aws_region" {
  description = "AWS region selected by the staging operator."
  type        = string

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
}

variable "environment" {
  type    = string
  default = "staging"

  validation {
    condition     = var.environment == "staging"
    error_message = "This root module is staging-only; environment must equal staging."
  }
}

variable "repository" {
  type    = string
  default = "hoangquocquan/Django-web-t-123"
}

variable "candidate_sha" {
  description = "Exact reviewed Git commit represented by the image digests."
  type        = string

  validation {
    condition     = can(regex("^[0-9a-f]{40}$", var.candidate_sha))
    error_message = "candidate_sha must be a full lowercase 40-character Git SHA."
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

variable "vpc_cidr" {
  type    = string
  default = "10.42.0.0/16"
}

variable "availability_zones" {
  description = "Exactly two AZs, or an empty list to select the first two available AZs."
  type        = list(string)
  default     = []

  validation {
    condition     = length(var.availability_zones) == 0 || length(var.availability_zones) == 2
    error_message = "availability_zones must be empty or contain exactly two AZs."
  }
}

variable "staging_hostname" {
  description = "Approved staging hostname without a URL scheme."
  type        = string

  validation {
    condition     = can(regex("^[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?$", var.staging_hostname)) && strcontains(var.staging_hostname, ".") && !strcontains(var.staging_hostname, "..")
    error_message = "staging_hostname must be a valid DNS hostname."
  }
}

variable "certificate_arn" {
  description = "Operator-approved ACM certificate ARN in aws_region."
  type        = string

  validation {
    condition     = can(regex("^arn:[^:]+:acm:[^:]+:[0-9]{12}:certificate/", var.certificate_arn))
    error_message = "certificate_arn must be an ACM certificate ARN."
  }
}

variable "route53_zone_id" {
  description = "Optional Route 53 public hosted-zone ID. Leave null for external DNS."
  type        = string
  default     = null
  nullable    = true
}

variable "backend_image_digest" {
  description = "Immutable sha256 digest produced for candidate_sha."
  type        = string

  validation {
    condition     = can(regex("^sha256:[0-9a-f]{64}$", var.backend_image_digest))
    error_message = "backend_image_digest must be sha256 followed by 64 lowercase hex characters."
  }
}

variable "frontend_image_digest" {
  description = "Immutable sha256 digest produced for candidate_sha."
  type        = string

  validation {
    condition     = can(regex("^sha256:[0-9a-f]{64}$", var.frontend_image_digest))
    error_message = "frontend_image_digest must be sha256 followed by 64 lowercase hex characters."
  }
}

variable "backend_ecr_repository_url" {
  description = "Bootstrap-owned backend ECR repository URL, without tag or digest."
  type        = string

  validation {
    condition     = can(regex("^[0-9]{12}\\.dkr\\.ecr\\.[a-z0-9-]+\\.amazonaws\\.com(?:\\.cn)?/[a-z0-9][a-z0-9._/-]*$", var.backend_ecr_repository_url))
    error_message = "backend_ecr_repository_url must be a valid ECR repository URL without a tag or digest."
  }
}

variable "backend_ecr_repository_arn" {
  description = "Bootstrap-owned backend ECR repository ARN used for least-privilege image pulls and verification."
  type        = string

  validation {
    condition     = can(regex("^arn:[^:]+:ecr:[^:]+:[0-9]{12}:repository/[a-z0-9][a-z0-9._/-]*$", var.backend_ecr_repository_arn))
    error_message = "backend_ecr_repository_arn must be a valid ECR repository ARN."
  }
}

variable "frontend_ecr_repository_url" {
  description = "Bootstrap-owned frontend ECR repository URL, without tag or digest."
  type        = string

  validation {
    condition     = can(regex("^[0-9]{12}\\.dkr\\.ecr\\.[a-z0-9-]+\\.amazonaws\\.com(?:\\.cn)?/[a-z0-9][a-z0-9._/-]*$", var.frontend_ecr_repository_url))
    error_message = "frontend_ecr_repository_url must be a valid ECR repository URL without a tag or digest."
  }
}

variable "frontend_ecr_repository_arn" {
  description = "Bootstrap-owned frontend ECR repository ARN used for least-privilege image pulls and verification."
  type        = string

  validation {
    condition     = can(regex("^arn:[^:]+:ecr:[^:]+:[0-9]{12}:repository/[a-z0-9][a-z0-9._/-]*$", var.frontend_ecr_repository_arn))
    error_message = "frontend_ecr_repository_arn must be a valid ECR repository ARN."
  }
}

variable "backend_cpu" {
  type    = number
  default = 512
}

variable "backend_memory" {
  type    = number
  default = 1024
}

variable "frontend_cpu" {
  type    = number
  default = 256
}

variable "frontend_memory" {
  type    = number
  default = 512
}

variable "service_desired_count" {
  description = "Initial service count. Keep 0 during binding; the gated deployment workflow raises it after migration."
  type        = number
  default     = 0

  validation {
    condition     = var.service_desired_count >= 0 && var.service_desired_count <= 2
    error_message = "service_desired_count must be between 0 and 2 for staging."
  }
}

variable "rds_instance_class" {
  type    = string
  default = "db.t4g.small"
}

variable "rds_allocated_storage" {
  type    = number
  default = 30
}

variable "database_name" {
  type    = string
  default = "mecprecision"
}

variable "database_username" {
  type    = string
  default = "mecprecision_admin"
}

variable "rds_deletion_protection" {
  type    = bool
  default = true
}

variable "redis_node_type" {
  type    = string
  default = "cache.t4g.micro"
}

variable "redis_num_cache_clusters" {
  description = "Use 1 for low-cost staging or 2 for automatic failover."
  type        = number
  default     = 1

  validation {
    condition     = contains([1, 2], var.redis_num_cache_clusters)
    error_message = "redis_num_cache_clusters must be 1 or 2."
  }
}

variable "redis_auth_secret_arn" {
  description = "ARN of an operator-managed Secrets Manager secret whose entire value is the Redis auth token."
  type        = string

  validation {
    condition     = can(regex("^arn:[^:]+:secretsmanager:[^:]+:[0-9]{12}:secret:", var.redis_auth_secret_arn))
    error_message = "redis_auth_secret_arn must be a Secrets Manager secret ARN."
  }
}

variable "log_retention_days" {
  type    = number
  default = 14
}

variable "backup_retention_days" {
  type    = number
  default = 7
}

variable "enable_github_deploy_role" {
  description = "Create the staging deployment role, separate from the bootstrap-owned image-build role."
  type        = bool
  default     = false
}

variable "github_oidc_provider_arn" {
  description = "Bootstrap-selected account-level GitHub OIDC provider ARN. Required when enable_github_deploy_role is true."
  type        = string
  default     = null
  nullable    = true

  validation {
    condition     = !var.enable_github_deploy_role || (var.github_oidc_provider_arn != null && can(regex("^arn:[^:]+:iam::[0-9]{12}:oidc-provider/token.actions.githubusercontent.com$", var.github_oidc_provider_arn)))
    error_message = "github_oidc_provider_arn must identify the GitHub Actions OIDC provider when the deploy role is enabled."
  }
}

variable "alb_deletion_protection" {
  type    = bool
  default = true
}
