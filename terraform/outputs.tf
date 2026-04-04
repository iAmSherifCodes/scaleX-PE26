output "alb_dns_name" {
  description = "DNS name of the ALB"
  value       = aws_lb.app.dns_name
}

output "alb_url" {
  description = "HTTP URL for the app"
  value       = "http://${aws_lb.app.dns_name}"
}

output "asg_name" {
  description = "Auto Scaling Group name"
  value       = aws_autoscaling_group.app.name
}

output "vpc_id" {
  description = "Created VPC ID"
  value       = module.vpc.vpc_id
}
