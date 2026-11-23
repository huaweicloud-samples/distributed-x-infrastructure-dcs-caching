variable "region" {
  description = "华为云区域"
  type        = string
  default     = "cn-north-4"
}

variable "project_name" {
  description = "项目名称，用于资源命名前缀"
  type        = string
  default     = "dcs-caching"
}

variable "availability_zones" {
  description = "可用区列表"
  type        = list(string)
  default     = ["cn-north-4a"]
}

variable "redis_password" {
  description = "DCS Redis 访问密码"
  type        = string
  sensitive   = true
}

variable "rds_flavor" {
  description = "RDS MySQL 规格"
  type        = string
  default     = "rds.mysql.n1.large.2"
}

variable "rds_db_name" {
  description = "回源数据库名（与 seed.sql 建库名一致）"
  type        = string
  default     = "tutorial"
}

variable "rds_password" {
  description = "RDS MySQL 密码"
  type        = string
  sensitive   = true
}
variable "ecs_password" {
  description = "ECS 登录密码"
  type        = string
  sensitive   = true
}
