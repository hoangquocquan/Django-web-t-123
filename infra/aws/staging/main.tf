data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_vpc" "staging" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
}

resource "aws_subnet" "data" {
  count             = 2
  vpc_id            = aws_vpc.staging.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, count.index + 8)
  availability_zone = length(var.availability_zones) > count.index ? var.availability_zones[count.index] : data.aws_availability_zones.available.names[count.index]
}

resource "aws_ecr_repository" "backend" {
  name                 = "${local.name}/backend"
  image_tag_mutability = "IMMUTABLE"
  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "frontend" {
  name                 = "${local.name}/frontend"
  image_tag_mutability = "IMMUTABLE"
  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${local.name}/backend"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/ecs/${local.name}/frontend"
  retention_in_days = var.log_retention_days
}

resource "aws_ecs_cluster" "staging" {
  name = local.name
}

resource "aws_secretsmanager_secret" "staging" {
  for_each                = toset(["django-secret-key", "database", "redis", "metrics-token"])
  name                    = "/${var.project_name}/${var.environment}/${each.key}"
  recovery_window_in_days = 7
}

resource "aws_efs_file_system" "media" {
  encrypted = true
}

resource "aws_db_subnet_group" "staging" {
  name       = local.name
  subnet_ids = aws_subnet.data[*].id
}

resource "aws_db_instance" "staging" {
  identifier              = local.name
  engine                  = "postgres"
  engine_version          = "16"
  instance_class          = var.rds_instance_class
  allocated_storage       = var.rds_allocated_storage
  storage_encrypted       = true
  backup_retention_period = var.backup_retention_days
  publicly_accessible     = false
  deletion_protection     = false
  db_subnet_group_name    = aws_db_subnet_group.staging.name
  skip_final_snapshot     = true
}

resource "aws_elasticache_subnet_group" "staging" {
  name       = local.name
  subnet_ids = aws_subnet.data[*].id
}

resource "aws_elasticache_replication_group" "staging" {
  replication_group_id       = replace(local.name, "_", "-")
  description                = "Staging Redis/Valkey TLS service"
  node_type                  = var.redis_node_type
  num_cache_clusters         = 2
  automatic_failover_enabled = true
  transit_encryption_enabled = true
  at_rest_encryption_enabled = true
  subnet_group_name          = aws_elasticache_subnet_group.staging.name
}

resource "aws_backup_vault" "staging" {
  name = local.name
}

output "candidate_sha" {
  value = var.candidate_sha
}
output "vpc_id" {
  value = aws_vpc.staging.id
}
output "ecr_backend" {
  value = aws_ecr_repository.backend.repository_url
}
output "ecr_frontend" {
  value = aws_ecr_repository.frontend.repository_url
}
