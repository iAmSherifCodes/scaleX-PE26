variable "aws_region" {
  description = "AWS region to deploy to"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name prefix for all resources"
  type        = string
  default     = "scalex-quest"
}

variable "environment" {
  description = "Environment tag"
  type        = string
  default     = "quest"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "private_subnet_cidrs" {
  description = "Private subnet CIDRs"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "public_subnet_cidrs" {
  description = "Public subnet CIDRs"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24"]
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "app_image" {
  description = "Container image for the app"
  type        = string
  default     = "ogdmerlin/scalex-pe26:latest"
}

variable "app_container_port" {
  description = "Port exposed inside container"
  type        = number
  default     = 5000
}

variable "app_host_port" {
  description = "Port exposed on EC2 host"
  type        = number
  default     = 80
}

variable "health_check_path" {
  description = "ALB health check endpoint"
  type        = string
  default     = "/health"
}

variable "min_size" {
  description = "Minimum ASG size"
  type        = number
  default     = 2
}

variable "desired_capacity" {
  description = "Desired ASG size"
  type        = number
  default     = 2
}

variable "max_size" {
  description = "Maximum ASG size"
  type        = number
  default     = 4
}

variable "scale_out_cpu_threshold" {
  description = "CPU threshold to scale out"
  type        = number
  default     = 60
}

variable "scale_in_cpu_threshold" {
  description = "CPU threshold to scale in"
  type        = number
  default     = 25
}
