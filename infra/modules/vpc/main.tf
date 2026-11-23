# 共享网络模块：VPC + 子网 + 安全组
# 所有缓存样例共用一套 VPC 底座，避免每个样例重复声明网络资源。

variable "project_name" {
  description = "项目名称，用于资源命名前缀"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC 网段"
  type        = string
  default     = "10.0.0.0/16"
}

variable "subnet_cidr" {
  description = "子网网段"
  type        = string
  default     = "10.0.1.0/24"
}

resource "huaweicloud_vpc" "main" {
  name = "${var.project_name}-vpc"
  cidr = var.vpc_cidr
}

resource "huaweicloud_vpc_subnet" "main" {
  name       = "${var.project_name}-subnet"
  vpc_id     = huaweicloud_vpc.main.id
  cidr       = var.subnet_cidr
  gateway_ip = cidrhost(var.subnet_cidr, 1)
}

# 安全组：缓存/数据库互访端口对内网放行（Redis 6379 / MySQL 3306 / 应用 8080）
resource "huaweicloud_networking_secgroup" "main" {
  name        = "${var.project_name}-sg"
  description = "Security group for cache and database samples (internal access)"
}

locals {
  # 端口 -> 协议，统一 TCP
  internal_ports = {
    redis = 6379

    mysql    = 3306
    app_http = 8080
  }
}

resource "huaweicloud_networking_secgroup_rule" "internal_ingress" {
  for_each = local.internal_ports

  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = each.value
  port_range_max    = each.value
  remote_ip_prefix  = var.vpc_cidr
  security_group_id = huaweicloud_networking_secgroup.main.id
}

# 出站放行（应用安装依赖、访问外部服务）
resource "huaweicloud_networking_secgroup_rule" "egress_tcp" {
  direction         = "egress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 1
  port_range_max    = 65535
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = huaweicloud_networking_secgroup.main.id
}

output "vpc_id" {
  value = huaweicloud_vpc.main.id
}

output "subnet_id" {
  value = huaweicloud_vpc_subnet.main.id
}

output "security_group_id" {
  value = huaweicloud_networking_secgroup.main.id
}