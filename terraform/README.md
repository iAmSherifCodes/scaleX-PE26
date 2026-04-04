Terraform AWS Scalability Stack

This folder provisions Silver and Gold infrastructure for the scalability quest:
- VPC across 2 Availability Zones
- Public ALB (traffic cop)
- Auto Scaling Group of EC2 instances (clone army)
- CloudWatch CPU alarms for scale out and scale in (gold auto scaling)

Prerequisites
- AWS CLI configured with credentials and default account access
- Terraform 1.5+
- A pushed container image for this app

Quick start
1. Copy values into terraform.tfvars (or pass with -var), especially app_image.
2. Run:
   terraform init
   terraform plan
   terraform apply

Friend run checklist (exact)
1. Open `terraform/terraform.tfvars` and set `app_image` to a real image.
2. Run `cd terraform`.
3. Run `terraform init`.
4. Run `terraform plan` and confirm resources look correct.
5. Run `terraform apply` and type `yes`.
6. Copy `alb_url` output and test `http://<alb_dns>/health`.
7. When done, run `terraform destroy` to avoid charges.

Required variable
- app_image must point to your image, for example:
  app_image = "yourdockeruser/scalex-pe26:latest"

Outputs
- alb_dns_name
- alb_url
- asg_name
- vpc_id

Cost cleanup
- Destroy everything when done:
  terraform destroy
