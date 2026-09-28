resource "aws_ecr_repository" "backend" {
  name                 = "${local.name}/backend"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }
}

resource "aws_ecr_repository" "frontend" {
  name                 = "${local.name}/frontend"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }
}

resource "aws_ecr_lifecycle_policy" "images" {
  for_each = {
    backend  = aws_ecr_repository.backend.name
    frontend = aws_ecr_repository.frontend.name
  }

  repository = each.value
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Retain the latest 20 staging images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 20
      }
      action = { type = "expire" }
    }]
  })
}

resource "aws_secretsmanager_secret" "runtime" {
  for_each = toset([
    "django-secret-key",
    "database-url",
    "redis-url",
    "metrics-token",
  ])

  name                    = "/${var.project_name}/${var.environment}/${each.key}"
  description             = "Operator-populated ${each.key} for ${local.name}; value is not managed in Git"
  recovery_window_in_days = 7

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_efs_file_system" "media" {
  encrypted        = true
  performance_mode = "generalPurpose"
  throughput_mode  = "bursting"

  lifecycle_policy {
    transition_to_ia = "AFTER_30_DAYS"
  }

  tags = { Name = "${local.name}-media" }
}

resource "aws_efs_access_point" "media" {
  file_system_id = aws_efs_file_system.media.id

  posix_user {
    uid = 1000
    gid = 1000
  }

  root_directory {
    path = "/media"
    creation_info {
      owner_uid   = 1000
      owner_gid   = 1000
      permissions = "0775"
    }
  }
}

resource "aws_efs_mount_target" "media" {
  count = 2

  file_system_id  = aws_efs_file_system.media.id
  subnet_id       = aws_subnet.data[count.index].id
  security_groups = [aws_security_group.efs.id]
}

resource "aws_db_subnet_group" "staging" {
  name       = local.name
  subnet_ids = aws_subnet.data[*].id
}

resource "aws_db_parameter_group" "postgres16_tls" {
  name_prefix = "${local.name}-postgres16-"
  family      = "postgres16"
  description = "Require TLS for ${local.name} PostgreSQL"

  parameter {
    name         = "rds.force_ssl"
    value        = "1"
    apply_method = "pending-reboot"
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_db_instance" "staging" {
  identifier = local.name

  engine                      = "postgres"
  engine_version              = "16"
  instance_class              = var.rds_instance_class
  db_name                     = var.database_name
  username                    = var.database_username
  manage_master_user_password = true

  allocated_storage     = var.rds_allocated_storage
  max_allocated_storage = var.rds_allocated_storage * 2
  storage_type          = "gp3"
  storage_encrypted     = true

  port                   = 5432
  publicly_accessible    = false
  multi_az               = false
  db_subnet_group_name   = aws_db_subnet_group.staging.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  parameter_group_name   = aws_db_parameter_group.postgres16_tls.name

  backup_retention_period   = var.backup_retention_days
  copy_tags_to_snapshot     = true
  deletion_protection       = var.rds_deletion_protection
  skip_final_snapshot       = false
  final_snapshot_identifier = "${local.name}-final"

  auto_minor_version_upgrade = true
  apply_immediately          = false

  tags = { Name = local.name }
}

resource "aws_elasticache_subnet_group" "staging" {
  name       = local.name
  subnet_ids = aws_subnet.data[*].id
}

data "aws_secretsmanager_secret_version" "redis_auth" {
  secret_id = var.redis_auth_secret_arn
}

resource "aws_elasticache_replication_group" "staging" {
  replication_group_id = replace(local.name, "_", "-")
  description          = "Private authenticated TLS Redis for ${local.name}"

  engine         = "redis"
  engine_version = "7.1"
  node_type      = var.redis_node_type
  port           = 6379

  num_cache_clusters         = var.redis_num_cache_clusters
  automatic_failover_enabled = var.redis_num_cache_clusters > 1
  multi_az_enabled           = var.redis_num_cache_clusters > 1

  transit_encryption_enabled = true
  at_rest_encryption_enabled = true
  auth_token                 = data.aws_secretsmanager_secret_version.redis_auth.secret_string
  auth_token_update_strategy = "ROTATE"

  subnet_group_name  = aws_elasticache_subnet_group.staging.name
  security_group_ids = [aws_security_group.redis.id]

  snapshot_retention_limit = var.backup_retention_days
  apply_immediately        = false

  tags = { Name = local.name }
}
