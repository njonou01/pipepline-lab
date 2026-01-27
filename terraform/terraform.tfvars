
project_name = "uccnt"
environment  = "dev"
aws_region   = "us-east-1"

# Compute
streamlit_instance_type = "t2.small"

# Network
public_key_path  = "./mykey.pub"
allowed_ssh_cidr = ["0.0.0.0/0"]

# DNS (optional)
create_dns_zone = false
domain_name     = ""

# Notifications
alert_email = "njonougaby45@gmail.com"
enable_ses  = false
