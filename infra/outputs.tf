output "vpc_id" {
  description = "共享 VPC ID"
  value       = module.vpc.vpc_id
}

output "subnet_id" {
  description = "共享子网 ID"
  value       = module.vpc.subnet_id
}

output "security_group_id" {
  description = "共享安全组 ID"
  value       = module.vpc.security_group_id
}

output "redis_endpoint" {
  description = "DCS Redis 连接地址"
  value       = module.redis.connection_endpoint
}

output "redis_port" {
  description = "DCS Redis 端口"
  value       = module.redis.port
}

output "mysql_endpoint" {
  description = "RDS MySQL 连接地址（内网）"
  value       = module.mysql.connection_endpoint
}

output "mysql_db_name" {
  description = "回源数据库名"
  value       = module.mysql.db_name
}