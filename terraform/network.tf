
resource "aws_key_pair" "main" {
  key_name   = "${local.name_prefix}-key"
  public_key = file(var.public_key_path)

  tags = {
    Name = "${local.name_prefix}-key"
  }
}

resource "aws_security_group" "streamlit" {
  name        = "${local.name_prefix}-streamlit-sg"
  description = "Security group for Streamlit dashboard"

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_ssh_cidr
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Streamlit direct"
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${local.name_prefix}-streamlit-sg"
  }
}

resource "aws_eip" "streamlit" {
  instance = aws_instance.streamlit.id
  domain   = "vpc"

  tags = {
    Name = "${local.name_prefix}-streamlit-eip"
  }
}

resource "aws_route53_zone" "main" {
  count = var.create_dns_zone ? 1 : 0
  name  = var.domain_name

  tags = {
    Name = "${local.name_prefix}-dns-zone"
  }
}

resource "aws_route53_record" "streamlit" {
  count   = var.create_dns_zone ? 1 : 0
  zone_id = aws_route53_zone.main[0].zone_id
  name    = "dashboard.${var.domain_name}"
  type    = "A"
  ttl     = 300
  records = [aws_eip.streamlit.public_ip]
}
