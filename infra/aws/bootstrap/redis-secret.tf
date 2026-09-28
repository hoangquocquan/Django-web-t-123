resource "aws_secretsmanager_secret" "redis_auth" {
  name                    = "/${var.project_name}/${var.environment}/redis-auth"
  description             = "Redis AUTH token prerequisite for ${local.name}"
  recovery_window_in_days = 7

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_secretsmanager_secret_version" "redis_auth" {
  secret_id     = aws_secretsmanager_secret.redis_auth.id
  secret_string = var.redis_auth_token
}
