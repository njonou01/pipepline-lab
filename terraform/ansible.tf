
resource "local_file" "ansible_inventory" {
  content = <<-EOF
[streamlit]
${aws_eip.streamlit.public_ip}

[streamlit:vars]
ansible_user=ubuntu
ansible_ssh_private_key_file=../terraform/mykey.pem
ansible_python_interpreter=/usr/bin/python3

aws_region=${var.aws_region}
raw_bucket=${aws_s3_bucket.raw.id}
processed_bucket=${aws_s3_bucket.processed.id}
curated_bucket=${aws_s3_bucket.curated.id}
glue_database=${aws_glue_catalog_database.main.name}
EOF

  filename = "${path.module}/../ansible/inventory/hosts.ini"

  depends_on = [aws_eip.streamlit]
}

resource "null_resource" "ansible_provisioner" {
  triggers = {
    instance_id = aws_instance.streamlit.id
    inventory   = local_file.ansible_inventory.content
  }

  provisioner "local-exec" {
    command     = "sleep 60 && ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i inventory/hosts.ini playbooks/streamlit.yml"
    working_dir = "${path.module}/../ansible"
  }

  depends_on = [
    local_file.ansible_inventory,
    aws_instance.streamlit,
    aws_eip.streamlit
  ]
}
