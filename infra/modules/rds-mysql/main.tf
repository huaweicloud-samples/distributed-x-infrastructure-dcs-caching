# 共享关系库模块：RDS for MySQL
# 共享关系库模块：RDS for MySQL，database-caching / jdbc-caching-demo 作为回源数据库。

variable "project_name" {
  description = "项目名称"
  type        = string
}

variable "flavor" {
  description = "RDS 实例规格"
  type        = string
  default     = "rds.mysql.n1.large.2"
}

variable "db_name" {
  description = "初始数据库名"
  type        = string
  default     = "demo"
}

variable "db_password" {
  description = "数据库密码"
  type        = string
  sensitive   = true
}

variable "vpc_id" {
  type = string
}

variable "subnet_id" {
  type = string
}

variable "security_group_id" {
  type = string
}

variable "availability_zones" {
  type = list(string)
}

resource "huaweicloud_rds_instance" "main" {
  name              = "${var.project_name}-mysql"
  flavor            = var.flavor
  vpc_id            = var.vpc_id
  subnet_id         = var.subnet_id
  security_group_id = var.security_group_id
  availability_zone = var.availability_zones

  db {
    type     = "MySQL"
    version  = "8.0"
    password = var.db_password
    port     = 3306
  }

  volume {
    type = "CLOUDSSD"
    size = 40
  }
}

output "instance_id" {
  value = huaweicloud_rds_instance.main.id
}

output "connection_endpoint" {
  description = "MySQL 连接地址（内网 IP）"
  value       = huaweicloud_rds_instance.main.private_ips[0]
}

output "db_name" {
  value = var.db_name
}