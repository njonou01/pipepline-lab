resource "local_file" "setup_env_script" {
  content         = <<-EOT
    #!/bin/bash
    # Script de configuration de l'environnement (A sourcer)
    # Usage: source setup_env.sh

    echo "=== Configuration Environnement UCCNCT ==="
    echo "Kafka Broker: ${aws_instance.kafka.public_ip}:9092"
    echo "Redis Host:   ${aws_instance.kafka.public_ip}"
    
    export KAFKA_BOOTSTRAP="${aws_instance.kafka.public_ip}:9092"
    export REDIS_HOST="${aws_instance.kafka.public_ip}"
    
    echo "Variables d'environnement exportées."
    echo "Pour lancer les collecteurs manuellement :"
    echo "  python3 scripts/collector/run_all.py"
  EOT
  filename        = "../setup_env.sh"
  file_permission = "0755"
}
