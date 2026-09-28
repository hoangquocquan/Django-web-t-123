locals {
  ecs_tasks_assume_role = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role" "ecs_execution" {
  name_prefix        = "${local.name}-execution-"
  assume_role_policy = local.ecs_tasks_assume_role
}

resource "aws_iam_role_policy" "ecs_execution" {
  name = "staging-runtime-bootstrap"
  role = aws_iam_role.ecs_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "EcrAuthorizationToken"
        Effect   = "Allow"
        Action   = ["ecr:GetAuthorizationToken"]
        Resource = "*" # AWS does not support resource scoping for this action.
      },
      {
        Sid    = "PullReviewedImages"
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",
        ]
        Resource = [
          aws_ecr_repository.backend.arn,
          aws_ecr_repository.frontend.arn,
        ]
      },
      {
        Sid    = "WriteTaskLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = [
          "${aws_cloudwatch_log_group.backend.arn}:*",
          "${aws_cloudwatch_log_group.frontend.arn}:*",
          "${aws_cloudwatch_log_group.migration.arn}:*",
        ]
      },
      {
        Sid      = "ReadRuntimeSecrets"
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = [for secret in aws_secretsmanager_secret.runtime : secret.arn]
      },
    ]
  })
}

resource "aws_iam_role" "backend_task" {
  name_prefix        = "${local.name}-backend-task-"
  assume_role_policy = local.ecs_tasks_assume_role
}

resource "aws_iam_role_policy" "backend_efs" {
  name = "media-read-write"
  role = aws_iam_role.backend_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "elasticfilesystem:ClientMount",
        "elasticfilesystem:ClientWrite",
      ]
      Resource = aws_efs_file_system.media.arn
      Condition = {
        StringEquals = {
          "elasticfilesystem:AccessPointArn" = aws_efs_access_point.media.arn
        }
      }
    }]
  })
}

resource "aws_iam_role" "frontend_task" {
  name_prefix        = "${local.name}-frontend-task-"
  assume_role_policy = local.ecs_tasks_assume_role
}

resource "aws_iam_role_policy" "frontend_efs" {
  name = "media-read-only"
  role = aws_iam_role.frontend_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["elasticfilesystem:ClientMount"]
      Resource = aws_efs_file_system.media.arn
      Condition = {
        StringEquals = {
          "elasticfilesystem:AccessPointArn" = aws_efs_access_point.media.arn
        }
      }
    }]
  })
}

resource "aws_iam_role" "github_staging" {
  count = var.enable_github_oidc_role ? 1 : 0

  name_prefix = "${local.name}-github-"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = var.github_oidc_provider_arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }
        StringLike = {
          "token.actions.githubusercontent.com:sub" = "repo:${var.repository}:environment:staging"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy" "github_staging" {
  count = var.enable_github_oidc_role ? 1 : 0

  name = "build-migrate-deploy-staging"
  role = aws_iam_role.github_staging[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "EcrAuthorizationToken"
        Effect   = "Allow"
        Action   = ["ecr:GetAuthorizationToken"]
        Resource = "*" # AWS does not support resource scoping for this action.
      },
      {
        Sid    = "PublishReviewedImages"
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:CompleteLayerUpload",
          "ecr:DescribeImages",
          "ecr:InitiateLayerUpload",
          "ecr:PutImage",
          "ecr:UploadLayerPart",
        ]
        Resource = [
          aws_ecr_repository.backend.arn,
          aws_ecr_repository.frontend.arn,
        ]
      },
      {
        Sid    = "RunMigrationTask"
        Effect = "Allow"
        Action = ["ecs:RunTask"]
        Resource = [
          aws_ecs_task_definition.migration.arn,
          "${replace(aws_ecs_task_definition.migration.arn, ":${aws_ecs_task_definition.migration.revision}", "")}:*",
        ]
        Condition = {
          ArnEquals = { "ecs:cluster" = aws_ecs_cluster.staging.arn }
        }
      },
      {
        Sid    = "ObserveMigrationAndServices"
        Effect = "Allow"
        Action = [
          "ecs:DescribeServices",
          "ecs:DescribeTaskDefinition",
          "ecs:DescribeTasks",
        ]
        Resource = "*" # Describe APIs do not consistently support resource-level permissions.
      },
      {
        Sid    = "DeployReviewedServices"
        Effect = "Allow"
        Action = ["ecs:UpdateService"]
        Resource = [
          aws_ecs_service.backend.id,
          aws_ecs_service.frontend.id,
        ]
      },
      {
        Sid    = "PassExactTaskRoles"
        Effect = "Allow"
        Action = ["iam:PassRole"]
        Resource = [
          aws_iam_role.ecs_execution.arn,
          aws_iam_role.backend_task.arn,
          aws_iam_role.frontend_task.arn,
        ]
        Condition = {
          StringEquals = { "iam:PassedToService" = "ecs-tasks.amazonaws.com" }
        }
      },
      {
        Sid    = "CreatePredeploySnapshot"
        Effect = "Allow"
        Action = ["rds:CreateDBSnapshot"]
        Resource = [
          aws_db_instance.staging.arn,
          "arn:${data.aws_partition.current.partition}:rds:${var.aws_region}:${var.aws_account_id}:snapshot:${local.name}-predeploy-*",
        ]
      },
      {
        Sid      = "ObservePredeploySnapshot"
        Effect   = "Allow"
        Action   = ["rds:DescribeDBSnapshots"]
        Resource = "*" # RDS DescribeDBSnapshots does not support resource scoping.
      },
    ]
  })
}
