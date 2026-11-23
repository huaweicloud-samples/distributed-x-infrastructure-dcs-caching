# 共享缓存模块：DCS 实例（Redis / Memcached 两种引擎）
# 共享缓存模块：DCS 实例（Redis / Memcached 两种引擎）。

variable "project_name" {
  description = "项目名称"
  type        = string
}

variable "engine" {
  description = "缓存引擎：Redis 或 Memcached"
  type        = string
  default     = "Redis"
  validation {
    condition     = contains(["Redis", "Memcached"], var.engine)
    error_message = "engine 仅支持 Redis 或 Memcached"
  }
}

variable "engine_version" {
  description = "引擎版本"
  type        = string
  default     = "5.0"
}

variable "capacity" {
  description = "缓存容量（GB）"
  type        = number
  default     = 0.125
}

variable "flavor" {
  description = "DCS 实例规格"
  type        = string
  default     = "redis.single.xu1.tiny.128"
}

variable "password" {
  description = "缓存实例访问密码（留空则免密，不推荐）"
  type        = string
  sensitive   = true
  default     = ""
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "subnet_id" {
  description = "子网 ID"
  type        = string
}

variable "availability_zones" {
  description = "可用区列表"
  type        = list(string)
}

resource "huaweicloud_dcs_instance" "main" {
  name               = "${var.project_name}-${lower(var.engine)}"
  engine             = var.engine
  engine_version     = var.engine_version
  capacity           = var.capacity
  flavor             = var.flavor
  password           = var.password != "" ? var.password : null
  vpc_id             = var.vpc_id
  subnet_id          = var.subnet_id
  availability_zones = var.availability_zones
}

output "instance_id" {
  value = huaweicloud_dcs_instance.main.id
}

output "connection_endpoint" {
  description = "缓存客户端连接地址（内网域名）"
  value       = huaweicloud_dcs_instance.main.domain_name
}

output "port" {
  description = "缓存端口（Redis 6379 / Memcached 11211）"
  value       = huaweicloud_dcs_instance.main.port
}

output "engine" {
  value = huaweicloud_dcs_instance.main.engine
}