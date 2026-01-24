
resource "aws_instance" "streamlit" {
  ami           = var.ami_id
  instance_type = var.streamlit_instance_type
  key_name      = aws_key_pair.main.key_name

  iam_instance_profile   = local.lab_instance_profile
  vpc_security_group_ids = [aws_security_group.streamlit.id]

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  tags = {
    Name = "${local.name_prefix}-streamlit"
    Role = "dashboard"
  }
}
