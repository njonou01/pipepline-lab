# ========================================
# ANSIBLE INVENTORY AND PROVISIONER
# ========================================

# Generate dynamic inventory for both VMs
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

[kafka]
${aws_eip.kafka.public_ip}

[kafka:vars]
ansible_user=ubuntu
ansible_ssh_private_key_file=../terraform/mykey.pem
ansible_python_interpreter=/usr/bin/python3

aws_region=${var.aws_region}
raw_bucket=${aws_s3_bucket.raw.id}
kafka_broker=${aws_eip.kafka.public_ip}:9092
redis_host=${aws_eip.kafka.public_ip}
EOF

  filename = "${path.module}/../ansible/inventory/hosts.ini"

  depends_on = [
    aws_eip.streamlit,
    aws_eip.kafka
  ]
}

# Provision Streamlit VM
resource "null_resource" "ansible_streamlit" {
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

# Provision Kafka VM
resource "null_resource" "ansible_kafka" {
  triggers = {
    instance_id = aws_instance.kafka.id
    inventory   = local_file.ansible_inventory.content
  }

  provisioner "local-exec" {
    command     = "sleep 90 && ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i inventory/hosts.ini playbooks/kafka.yml"
    working_dir = "${path.module}/../ansible"
  }

  depends_on = [
    local_file.ansible_inventory,
    aws_instance.kafka,
    aws_eip.kafka
  ]
}
