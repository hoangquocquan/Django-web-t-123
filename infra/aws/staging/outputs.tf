output "candidate_sha" {
  value = var.candidate_sha
}

output "vpc_id" {
  value = aws_vpc.staging.id
}

output "public_subnet_ids" {
  value = aws_subnet.public[*].id
}

output "application_subnet_ids" {
  value = aws_subnet.application[*].id
}

output "backend_security_group_id" {
  value = aws_security_group.backend.id
}

output "alb_dns_name" {
  value = aws_lb.staging.dns_name
}

output "staging_url" {
  value = "https://${var.staging_hostname}"
}

output "ecr_backend" {
  value = aws_ecr_repository.backend.repository_url
}

output "ecr_frontend" {
  value = aws_ecr_repository.frontend.repository_url
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.staging.name
}

output "backend_service_name" {
  value = aws_ecs_service.backend.name
}

output "frontend_service_name" {
  value = aws_ecs_service.frontend.name
}

output "migration_task_definition_arn" {
  value = aws_ecs_task_definition.migration.arn
}

output "rds_identifier" {
  value = aws_db_instance.staging.identifier
}

output "runtime_secret_arns" {
  description = "Secret ARNs to populate out-of-band before starting services."
  value       = { for name, secret in aws_secretsmanager_secret.runtime : name => secret.arn }
}

output "github_staging_role_arn" {
  value = var.enable_github_oidc_role ? aws_iam_role.github_staging[0].arn : null
}
