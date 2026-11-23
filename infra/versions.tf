terraform {
  required_version = ">= 1.5"

  required_providers {
    huaweicloud = {
      source  = "huaweicloud/huaweicloud"
      version = "~> 1.70"
    }
  }

  # 本地状态即可；生产环境可将状态迁至 OBS 桶
  backend "local" {}
}

provider "huaweicloud" {
  region = var.region
  # 凭据从环境变量读取：HW_ACCESS_KEY / HW_SECRET_KEY（在华为云『我的凭证』页面获取 AK/SK）
}