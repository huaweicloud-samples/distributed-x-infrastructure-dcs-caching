# ============================================================================
# 分布式缓存基础设施（DCS）— 主入口
# ============================================================================
# 本仓库围绕「托管缓存服务（DCS）做缓存模式」展开。
# 主入口把各缓存样例共用的底座一次性拉起：VPC + DCS Redis + RDS MySQL。
# ============================================================================

module "vpc" {
  source       = "./modules/vpc"
  project_name = var.project_name
}

# ---------------------------------------------------------------------------
# 核心缓存：DCS Redis（对应 Redis/Valkey 兼容实例）
# 注：DCS 单机版不支持 security_group_id（报 DCS.4872），故不传该字段，
#     实例位于私有子网内，同 VPC 可访问。
# ---------------------------------------------------------------------------
module "redis" {
  source = "./modules/dcs"

  project_name       = var.project_name
  engine             = "Redis"
  engine_version     = "5.0"
  capacity           = 0.125
  flavor             = "redis.single.xu1.tiny.128"
  password           = var.redis_password
  vpc_id             = module.vpc.vpc_id
  subnet_id          = module.vpc.subnet_id
  availability_zones = var.availability_zones
}

# ---------------------------------------------------------------------------
# 回源数据库：RDS MySQL（database-caching / jdbc-caching-demo 的查询来源）
# ---------------------------------------------------------------------------
module "mysql" {
  source = "./modules/rds-mysql"

  project_name       = var.project_name
  flavor             = var.rds_flavor
  db_name            = var.rds_db_name
  db_password        = var.rds_password
  vpc_id             = module.vpc.vpc_id
  subnet_id          = module.vpc.subnet_id
  security_group_id  = module.vpc.security_group_id
  availability_zones = var.availability_zones
}