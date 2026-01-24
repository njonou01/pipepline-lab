
data "aws_iam_role" "lab_role" {
  name = "LabRole"
}

data "aws_iam_instance_profile" "lab_profile" {
  name = "LabInstanceProfile"
}

data "aws_caller_identity" "current" {}

locals {
  lab_role_arn         = data.aws_iam_role.lab_role.arn
  lab_role_name        = data.aws_iam_role.lab_role.name
  lab_instance_profile = data.aws_iam_instance_profile.lab_profile.name
  account_id           = data.aws_caller_identity.current.account_id
}
