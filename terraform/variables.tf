
variable "project_name" {
  description = "Nom du projet"
  type        = string
  default     = "uccnct"
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
  default     = "ami-0c7217cdde317cfec" # Ubuntu 22.04 LTS us-east-1
}

variable "streamlit_instance_type" {
  description = "l'instance EC2 pour streamlit"
  type        = string
  default     = "t2.small"
}

variable "public_key_path" {
  description = "Ma clé publique"
  type        = string
  default     = "./mykey.pub"
}

variable "allowed_ssh_cidr" {
  description = "CIDR blocks allowed for SSH"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "domain_name" {
  description = "Domain name for Route 53"
  type        = string
  default     = ""
}

variable "create_dns_zone" {
  description = "Create Route 53 DNS zone"
  type        = bool
  default     = false
}
