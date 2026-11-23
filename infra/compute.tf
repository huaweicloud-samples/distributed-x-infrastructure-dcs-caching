# ============================================================================
# 计算节点（ECS）+ 公网 EIP：用于 SSH 上去跑「数据库查询缓存」业务逻辑
# ============================================================================
# 说明：DCS / RDS 均为 VPC 内网；example.py 需要一台同 VPC 的 ECS 来运行。
# EIP 仅用于 SSH 登录（随资源释放）。
# ============================================================================

# 公共 Ubuntu 镜像（按最新）
data "huaweicloud_images_image" "ubuntu" {
  name        = "Ubuntu 22.04 server 64bit"
  most_recent = true
  visibility  = "public"
}

resource "huaweicloud_compute_instance" "app" {
  name               = "${var.project_name}-ecs"
  flavor_name        = "s6.large.2"
  image_id           = data.huaweicloud_images_image.ubuntu.id
  security_group_ids = [module.vpc.security_group_id]
  availability_zone  = var.availability_zones[0]
  admin_pass         = var.ecs_password

  system_disk_type = "GPSSD"
  system_disk_size = 40

  network {
    uuid = module.vpc.subnet_id
  }
}

# 公网 EIP（SSH 用，按流量计费）
resource "huaweicloud_vpc_eip" "app" {
  publicip {
    type = "5_bgp"
  }

  bandwidth {
    name        = "${var.project_name}-eip-bw"
    size        = 5
    share_type  = "PER"
    charge_mode = "traffic"
  }
}

resource "huaweicloud_vpc_eip_associate" "app" {
  public_ip = huaweicloud_vpc_eip.app.address
  port_id   = huaweicloud_compute_instance.app.network[0].port
}

# SSH 入站规则（22 端口，调试期对公网开放；可改为你的固定 IP）
resource "huaweicloud_networking_secgroup_rule" "allow_ssh" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 22
  port_range_max    = 22
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = module.vpc.security_group_id
}

output "ecs_floating_ip" {
  description = "ECS 公网 IP（SSH 登录用）"
  value       = huaweicloud_vpc_eip.app.address
}