# 🏗️ StealthVault AI - Terraform Infrastructure
# Provision a production-ready AWS EC2 instance for the SOC.

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  default = "us-east-1"
}

variable "github_repo" {
  description = "Git repo to clone (https protocol)"
  default = "https://github.com/aryan-guptta-2007/stealthvault-ai.git"
}

# 🌐 Virtual Private Cloud (VPC)
resource "aws_security_group" "soc_sg" {
  name        = "stealthvault_production_sg"
  description = "StealthVault AI SOC Security Group (HTTP/HTTPS/SSH)"

  # SSH for Administration
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # 🛡️ In prod, restrict to your management range
  }

  # Dashboard (HTTP)
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Dashboard (HTTPS)
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # SOC Real-time WebSockets
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Outbound access
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 🖥️ The StealthVault EC2 Instance
resource "aws_instance" "stealthvault_soc" {
  ami           = "ami-0ebfd141b2259b671" # Amazon Linux 2023 or Ubuntu 24.04
  instance_type = "t3.medium"
  
  vpc_security_group_ids = [aws_security_group.soc_sg.id]
  
  root_block_device {
    volume_size = 30
    volume_type = "gp3"
  }

  user_data = <<-EOF
              #!/bin/bash
              # 🚀 Continuous Delivery Bootstrap
              yum update -y
              yum install -y git docker
              service docker start
              usermod -a -G docker ec2-user
              
              # Pull the Repo
              git clone ${var.github_repo} /home/ec2-user/stealthvault-ai
              cd /home/ec2-user/stealthvault-ai
              
              # Run Deployment
              chmod +x deploy_vps.sh
              # Note: Domain needs to be handled via DNS (Route53) in full IaC
              ./deploy_vps.sh --unattended
              EOF

  tags = {
    Name    = "StealthVault-SOC-Production"
    Project = "StealthVault-AI"
  }
}

output "public_ip" {
  value = aws_instance.stealthvault_soc.public_ip
}
