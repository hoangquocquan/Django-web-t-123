variable "aws_region" {
  type = string
}
variable "aws_account_id" {
  type    = string
  default = null
}
variable "project_name" {
  type    = string
  default = "django-web-t-123"
}
variable "environment" {
  type    = string
  default = "staging"
}
variable "repository" {
  type    = string
  default = "hoangquocquan/Django-web-t-123"
}
variable "candidate_sha" {
  type    = string
  default = "31da17011adb22a0dab4857f8249985249af0e51"
}
variable "owner" {
  type    = string
  default = "TO_BE_APPROVED"
}
variable "cost_center" {
  type    = string
  default = "TO_BE_APPROVED"
}
variable "vpc_cidr" {
  type    = string
  default = "10.42.0.0/16"
}
variable "availability_zones" {
  type    = list(string)
  default = []
}
variable "rds_instance_class" {
  type    = string
  default = "db.t4g.medium"
}
variable "rds_allocated_storage" {
  type    = number
  default = 50
}
variable "redis_node_type" {
  type    = string
  default = "cache.t4g.small"
}
variable "log_retention_days" {
  type    = number
  default = 14
}
variable "backup_retention_days" {
  type    = number
  default = 7
}
