output "state_bucket_name" {
  value = aws_s3_bucket.terraform_state.id
}

output "state_bucket_region" {
  value = var.aws_region
}

output "github_oidc_provider_arn" {
  value = local.github_oidc_provider_arn
}

output "github_image_build_role_arn" {
  value = aws_iam_role.github_image_build.arn
}

output "backend_ecr_repository_name" {
  value = aws_ecr_repository.backend.name
}

output "backend_ecr_repository_url" {
  value = aws_ecr_repository.backend.repository_url
}

output "backend_ecr_repository_arn" {
  value = aws_ecr_repository.backend.arn
}

output "frontend_ecr_repository_name" {
  value = aws_ecr_repository.frontend.name
}

output "frontend_ecr_repository_url" {
  value = aws_ecr_repository.frontend.repository_url
}

output "frontend_ecr_repository_arn" {
  value = aws_ecr_repository.frontend.arn
}

output "redis_auth_secret_arn" {
  value = aws_secretsmanager_secret.redis_auth.arn
}
