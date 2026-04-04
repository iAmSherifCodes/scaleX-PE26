aws_region       = "us-east-1"
project_name     = "scalex-quest"
environment      = "quest"

# Update this to your published image before apply.
app_image = "ogdmerlin/scalex-pe26:latest"

instance_type    = "t3.micro"

min_size         = 2
desired_capacity = 2
max_size         = 4

# Gold-tier autoscaling thresholds
scale_out_cpu_threshold = 60
scale_in_cpu_threshold  = 25
