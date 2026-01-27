# ========================================
# DATA SOURCE: Ubuntu 22.04 ARM64
# ========================================
data "aws_ami" "ubuntu_arm64" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-arm64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# ========================================
# EC2 INSTANCES - ARM64 GRAVITON2
# ========================================

# EC2 #1: Streamlit Dashboard (ARM64)
resource "aws_instance" "streamlit" {
  ami           = data.aws_ami.ubuntu_arm64.id
  instance_type = "t4g.micro" # 2 vCPU, 1 GB RAM, ARM64
  key_name      = aws_key_pair.main.key_name

  iam_instance_profile   = local.lab_instance_profile
  vpc_security_group_ids = [aws_security_group.streamlit.id]

  root_block_device {
    volume_size = 8 # 8 GB pour OS + Streamlit
    volume_type = "gp3"
  }

  tags = {
    Name         = "${local.name_prefix}-streamlit"
    Role         = "dashboard"
    Architecture = "arm64"
  }
}

# EC2 #2: Kafka + Redis (ARM64)
resource "aws_instance" "kafka" {
  ami           = data.aws_ami.ubuntu_arm64.id
  instance_type = "t4g.small" # 2 vCPU, 2 GB RAM, ARM64
  key_name      = aws_key_pair.main.key_name

  iam_instance_profile   = local.lab_instance_profile
  vpc_security_group_ids = [aws_security_group.kafka.id]

  root_block_device {
    volume_size = 50 # 50 GB pour Kafka logs + Redis
    volume_type = "gp3"
  }

  tags = {
    Name         = "${local.name_prefix}-kafka"
    Role         = "messaging"
    Architecture = "arm64"
  }
}
