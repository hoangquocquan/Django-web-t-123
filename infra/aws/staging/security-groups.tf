resource "aws_security_group" "alb" {
  name_prefix            = "${local.name}-alb-"
  description            = "Public HTTPS entry point only"
  vpc_id                 = aws_vpc.staging.id
  revoke_rules_on_delete = true
}

resource "aws_vpc_security_group_ingress_rule" "alb_http" {
  security_group_id = aws_security_group.alb.id
  description       = "HTTP redirect from the internet"
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "alb_https" {
  security_group_id = aws_security_group.alb.id
  description       = "HTTPS from the internet"
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
}

resource "aws_security_group" "backend" {
  name_prefix            = "${local.name}-backend-"
  description            = "Private Django tasks"
  vpc_id                 = aws_vpc.staging.id
  revoke_rules_on_delete = true
}

resource "aws_security_group" "frontend" {
  name_prefix            = "${local.name}-frontend-"
  description            = "Private frontend tasks"
  vpc_id                 = aws_vpc.staging.id
  revoke_rules_on_delete = true
}

resource "aws_vpc_security_group_ingress_rule" "backend_from_alb" {
  security_group_id            = aws_security_group.backend.id
  description                  = "Django traffic from ALB"
  referenced_security_group_id = aws_security_group.alb.id
  from_port                    = 8000
  to_port                      = 8000
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "backend_from_frontend" {
  security_group_id            = aws_security_group.backend.id
  description                  = "Nginx compatibility proxy to Django"
  referenced_security_group_id = aws_security_group.frontend.id
  from_port                    = 8000
  to_port                      = 8000
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "frontend_from_alb" {
  security_group_id            = aws_security_group.frontend.id
  description                  = "Frontend traffic from ALB"
  referenced_security_group_id = aws_security_group.alb.id
  from_port                    = 8080
  to_port                      = 8080
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "alb_to_backend" {
  security_group_id            = aws_security_group.alb.id
  description                  = "ALB to Django targets"
  referenced_security_group_id = aws_security_group.backend.id
  from_port                    = 8000
  to_port                      = 8000
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "alb_to_frontend" {
  security_group_id            = aws_security_group.alb.id
  description                  = "ALB to frontend targets"
  referenced_security_group_id = aws_security_group.frontend.id
  from_port                    = 8080
  to_port                      = 8080
  ip_protocol                  = "tcp"
}

resource "aws_security_group" "rds" {
  name_prefix            = "${local.name}-rds-"
  description            = "PostgreSQL from Django tasks only"
  vpc_id                 = aws_vpc.staging.id
  revoke_rules_on_delete = true
}

resource "aws_vpc_security_group_ingress_rule" "rds_from_backend" {
  security_group_id            = aws_security_group.rds.id
  referenced_security_group_id = aws_security_group.backend.id
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "backend_to_rds" {
  security_group_id            = aws_security_group.backend.id
  referenced_security_group_id = aws_security_group.rds.id
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
}

resource "aws_security_group" "redis" {
  name_prefix            = "${local.name}-redis-"
  description            = "Redis TLS from Django tasks only"
  vpc_id                 = aws_vpc.staging.id
  revoke_rules_on_delete = true
}

resource "aws_vpc_security_group_ingress_rule" "redis_from_backend" {
  security_group_id            = aws_security_group.redis.id
  referenced_security_group_id = aws_security_group.backend.id
  from_port                    = 6379
  to_port                      = 6379
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "backend_to_redis" {
  security_group_id            = aws_security_group.backend.id
  referenced_security_group_id = aws_security_group.redis.id
  from_port                    = 6379
  to_port                      = 6379
  ip_protocol                  = "tcp"
}

resource "aws_security_group" "efs" {
  name_prefix            = "${local.name}-efs-"
  description            = "NFS from application tasks only"
  vpc_id                 = aws_vpc.staging.id
  revoke_rules_on_delete = true
}

resource "aws_vpc_security_group_ingress_rule" "efs_from_backend" {
  security_group_id            = aws_security_group.efs.id
  referenced_security_group_id = aws_security_group.backend.id
  from_port                    = 2049
  to_port                      = 2049
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "efs_from_frontend" {
  security_group_id            = aws_security_group.efs.id
  referenced_security_group_id = aws_security_group.frontend.id
  from_port                    = 2049
  to_port                      = 2049
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "backend_to_efs" {
  security_group_id            = aws_security_group.backend.id
  referenced_security_group_id = aws_security_group.efs.id
  from_port                    = 2049
  to_port                      = 2049
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "frontend_to_efs" {
  security_group_id            = aws_security_group.frontend.id
  referenced_security_group_id = aws_security_group.efs.id
  from_port                    = 2049
  to_port                      = 2049
  ip_protocol                  = "tcp"
}

resource "aws_security_group" "endpoints" {
  name_prefix            = "${local.name}-endpoints-"
  description            = "Private AWS API endpoints for Fargate"
  vpc_id                 = aws_vpc.staging.id
  revoke_rules_on_delete = true
}

resource "aws_vpc_security_group_ingress_rule" "endpoints_from_backend" {
  security_group_id            = aws_security_group.endpoints.id
  referenced_security_group_id = aws_security_group.backend.id
  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "endpoints_from_frontend" {
  security_group_id            = aws_security_group.endpoints.id
  referenced_security_group_id = aws_security_group.frontend.id
  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "backend_to_endpoints" {
  security_group_id            = aws_security_group.backend.id
  referenced_security_group_id = aws_security_group.endpoints.id
  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "frontend_to_endpoints" {
  security_group_id            = aws_security_group.frontend.id
  referenced_security_group_id = aws_security_group.endpoints.id
  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "frontend_to_backend" {
  security_group_id            = aws_security_group.frontend.id
  referenced_security_group_id = aws_security_group.backend.id
  from_port                    = 8000
  to_port                      = 8000
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "backend_dns_udp" {
  security_group_id = aws_security_group.backend.id
  cidr_ipv4         = var.vpc_cidr
  from_port         = 53
  to_port           = 53
  ip_protocol       = "udp"
}

resource "aws_vpc_security_group_egress_rule" "backend_dns_tcp" {
  security_group_id = aws_security_group.backend.id
  cidr_ipv4         = var.vpc_cidr
  from_port         = 53
  to_port           = 53
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "frontend_dns_udp" {
  security_group_id = aws_security_group.frontend.id
  cidr_ipv4         = var.vpc_cidr
  from_port         = 53
  to_port           = 53
  ip_protocol       = "udp"
}

resource "aws_vpc_security_group_egress_rule" "frontend_dns_tcp" {
  security_group_id = aws_security_group.frontend.id
  cidr_ipv4         = var.vpc_cidr
  from_port         = 53
  to_port           = 53
  ip_protocol       = "tcp"
}
