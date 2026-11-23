# ============================================================================
# 存储补充：OBS 桶（特征存储 / 语义缓存用到的对象存储）
# ============================================================================
# OBS 桶：特征存储 / 语义缓存用到的对象存储（批量预测 JSON / 离线特征文件）。
# 其余按样例可选的服务（GeminiDB DynamoDB 兼容 / FunctionGraph / CCE）在
# docs/deployment-guide.md 中单独说明，不在共享底座里默认创建。
# ============================================================================

resource "huaweicloud_obs_bucket" "assets" {
  bucket        = "${var.project_name}-assets"
  acl           = "private"
  force_destroy = true

  tags = {
    project = var.project_name
  }
}

output "obs_bucket_name" {
  description = "OBS 桶名（特征存储 / 语义缓存的批量数据）"
  value       = huaweicloud_obs_bucket.assets.bucket
}