resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${local.name}/backend"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/ecs/${local.name}/frontend"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "migration" {
  name              = "/ecs/${local.name}/migration"
  retention_in_days = var.log_retention_days
}

resource "aws_ecs_cluster" "staging" {
  name = local.name

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_service_discovery_private_dns_namespace" "staging" {
  name        = "${var.environment}.internal"
  description = "Private service discovery for ${local.name}"
  vpc         = aws_vpc.staging.id
}

locals {
  backend_environment = [
    { name = "DJANGO_SETTINGS_MODULE", value = "config.settings.staging" },
    { name = "ALLOWED_HOSTS", value = var.staging_hostname },
    { name = "CORS_ALLOWED_ORIGINS", value = "" },
    { name = "CSRF_TRUSTED_ORIGINS", value = "https://${var.staging_hostname}" },
    { name = "DATABASE_SSLMODE", value = "require" },
    { name = "MEDIA_ROOT", value = "/app/django_backend/media" },
    { name = "MEDIA_STORAGE_DURABLE", value = "true" },
    { name = "MEDIA_BACKUP_ENABLED", value = "true" },
    { name = "LINE_SEND_ENABLED", value = "false" },
    { name = "LEGACY_DATABASE_ENABLED", value = "false" },
    { name = "AI_SALES_OLLAMA_ENABLED", value = "false" },
    { name = "AI_AGENT_OLLAMA_PLANNER_ENABLED", value = "false" },
    { name = "AI_REDIS_RATE_LIMIT_ENABLED", value = "true" },
    { name = "AI_OLLAMA_CAPACITY_ENABLED", value = "false" },
  ]

  backend_secrets = [
    { name = "SECRET_KEY", valueFrom = aws_secretsmanager_secret.runtime["django-secret-key"].arn },
    { name = "DATABASE_URL", valueFrom = aws_secretsmanager_secret.runtime["database-url"].arn },
    { name = "REDIS_URL", valueFrom = aws_secretsmanager_secret.runtime["redis-url"].arn },
    { name = "METRICS_BEARER_TOKEN", valueFrom = aws_secretsmanager_secret.runtime["metrics-token"].arn },
  ]
}

resource "aws_ecs_task_definition" "backend" {
  family                   = "${local.name}-backend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.backend_cpu
  memory                   = var.backend_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.backend_task.arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  volume {
    name = "media"
    efs_volume_configuration {
      file_system_id     = aws_efs_file_system.media.id
      transit_encryption = "ENABLED"
      authorization_config {
        access_point_id = aws_efs_access_point.media.id
        iam             = "ENABLED"
      }
    }
  }

  container_definitions = jsonencode([{
    name      = "backend"
    image     = local.backend_image
    essential = true
    portMappings = [{
      name          = "http"
      containerPort = 8000
      hostPort      = 8000
      protocol      = "tcp"
    }]
    environment = local.backend_environment
    secrets     = local.backend_secrets
    mountPoints = [{
      sourceVolume  = "media"
      containerPath = "/app/django_backend/media"
      readOnly      = false
    }]
    healthCheck = {
      command     = ["CMD-SHELL", "python -c \"import urllib.request; r=urllib.request.Request('http://127.0.0.1:8000/api/v1/phase6/live/', headers={'X-Forwarded-Proto':'https'}); urllib.request.urlopen(r, timeout=3).read()\""]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 30
    }
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.backend.name
        awslogs-region        = var.aws_region
        awslogs-stream-prefix = "backend"
      }
    }
  }])
}

resource "aws_ecs_task_definition" "frontend" {
  family                   = "${local.name}-frontend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.frontend_cpu
  memory                   = var.frontend_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.frontend_task.arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  volume {
    name = "media"
    efs_volume_configuration {
      file_system_id     = aws_efs_file_system.media.id
      transit_encryption = "ENABLED"
      authorization_config {
        access_point_id = aws_efs_access_point.media.id
        iam             = "ENABLED"
      }
    }
  }

  container_definitions = jsonencode([{
    name      = "frontend"
    image     = local.frontend_image
    essential = true
    portMappings = [{
      name          = "http"
      containerPort = 8080
      hostPort      = 8080
      protocol      = "tcp"
    }]
    mountPoints = [{
      sourceVolume  = "media"
      containerPath = "/srv/media"
      readOnly      = true
    }]
    healthCheck = {
      command     = ["CMD-SHELL", "wget -q -O /dev/null http://127.0.0.1:8080/ || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 20
    }
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.frontend.name
        awslogs-region        = var.aws_region
        awslogs-stream-prefix = "frontend"
      }
    }
  }])
}

resource "aws_ecs_task_definition" "migration" {
  family                   = "${local.name}-migration"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.backend_cpu
  memory                   = var.backend_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.backend_task.arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  volume {
    name = "media"
    efs_volume_configuration {
      file_system_id     = aws_efs_file_system.media.id
      transit_encryption = "ENABLED"
      authorization_config {
        access_point_id = aws_efs_access_point.media.id
        iam             = "ENABLED"
      }
    }
  }

  container_definitions = jsonencode([{
    name        = "migration"
    image       = local.backend_image
    essential   = true
    command     = ["python", "manage.py", "migrate", "--noinput"]
    environment = local.backend_environment
    secrets     = local.backend_secrets
    mountPoints = [{
      sourceVolume  = "media"
      containerPath = "/app/django_backend/media"
      readOnly      = false
    }]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.migration.name
        awslogs-region        = var.aws_region
        awslogs-stream-prefix = "migration"
      }
    }
  }])
}

resource "aws_ecs_service" "backend" {
  name            = "backend"
  cluster         = aws_ecs_cluster.staging.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = var.service_desired_count
  launch_type     = "FARGATE"

  enable_execute_command             = false
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200
  health_check_grace_period_seconds  = 60

  network_configuration {
    subnets          = aws_subnet.application[*].id
    security_groups  = [aws_security_group.backend.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8000
  }

  service_connect_configuration {
    enabled   = true
    namespace = aws_service_discovery_private_dns_namespace.staging.arn

    service {
      port_name      = "http"
      discovery_name = "django"

      client_alias {
        dns_name = "django"
        port     = 8000
      }
    }
  }

  depends_on = [
    aws_lb_listener_rule.backend,
    aws_efs_mount_target.media,
  ]

  lifecycle {
    ignore_changes = [desired_count]
  }
}

resource "aws_ecs_service" "frontend" {
  name            = "frontend"
  cluster         = aws_ecs_cluster.staging.id
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = var.service_desired_count
  launch_type     = "FARGATE"

  enable_execute_command             = false
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200
  health_check_grace_period_seconds  = 60

  network_configuration {
    subnets          = aws_subnet.application[*].id
    security_groups  = [aws_security_group.frontend.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "frontend"
    container_port   = 8080
  }

  service_connect_configuration {
    enabled   = true
    namespace = aws_service_discovery_private_dns_namespace.staging.arn
  }

  depends_on = [
    aws_lb_listener.https,
    aws_ecs_service.backend,
    aws_efs_mount_target.media,
  ]

  lifecycle {
    ignore_changes = [desired_count]
  }
}
