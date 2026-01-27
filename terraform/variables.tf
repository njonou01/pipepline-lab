
variable "project_name" {
  description = "Nom du projet"
  type        = string
  default     = "uccnt"
}

variable "environment" {
  description = "L'environement"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_tags" {
  description = "Tag pour toutes nos ressources"
  type        = map(string)
  default = {
    Project     = "uccnct-data-pipepline"
    Environment = "prod"
    ManagedBy   = "Terraform"
  }
}

variable "ami_id" {
  description = "AMI ID pour l'instance EC2  Ubuntu"
  type        = string
  default     = "ami-0c7217cdde317cfec" # Ubuntu 22.04 LTS us-east-1 x86
}

variable "ami_id_arm" {
  description = "AMI ID pour instances EC2 ARM64"
  type        = string
  default     = "ami-0a0d8589b597f6eac" # Ubuntu 22.04 LTS us-east-1 ARM64
}

variable "streamlit_instance_type" {
  description = "l'instance EC2 pour streamlit"
  type        = string
  default     = "t4g.micro"
}

variable "public_key_path" {
  description = "Ma clé publique"
  type        = string
  default     = "./mykey.pub"
}

variable "allowed_ssh_cidr" {
  description = "CIDR block pour les accès ssh"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "create_dns_zone" {
  description = "Creation de zone route 53 ?"
  type        = bool
  default     = false
}

variable "domain_name" {
  description = "Nom de domaine"
  type        = string
  default     = "uccnct.com"
}

variable "alert_email" {
  description = "Email pour les alertes SNS"
  type        = string
  default     = "admin@example.com"
}

variable "enable_ses" {
  description = "Activer SES pour les emails"
  type        = bool
  default     = false
}

