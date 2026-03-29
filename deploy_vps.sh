#!/bin/bash
# ╔═══════════════════════════════════════════════════════════╗
# ║        STEALTHVAULT AI — VPS DEPLOYMENT SCRIPT            ║
# ║        Run this script on a fresh Ubuntu 24.04/22.04 LTS  ║
# ╚═══════════════════════════════════════════════════════════╝

set -e

echo "🚀 Starting StealthVault AI Production Deployment..."

# 1. Update System
echo "📦 Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install Dependencies
echo "🛠️ Installing dependencies..."
sudo apt-get install -y curl ufw git

# 3. Install Docker & Docker Compose
if ! command -v docker &> /dev/null
then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
else
    echo "✅ Docker is already installed."
fi

if ! command -v docker-compose &> /dev/null
then
    echo "🐳 Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# 4. Configure Firewall (UFW)
echo "🛡️ Configuring Firewall (UFW)..."
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Core Services
sudo ufw allow 22/tcp      # SSH (Admin access)
sudo ufw allow 80/tcp      # HTTP (Dashboard)
sudo ufw allow 443/tcp     # HTTPS
sudo ufw allow 8000/tcp    # FastAPI Backend & WebSockets
# (Optional) Honeypot Ports for Defender Agent
sudo ufw allow 21/tcp      # FTP Honeypot
sudo ufw allow 23/tcp      # Telnet Honeypot

echo "y" | sudo ufw enable
sudo ufw status

# 5. Build and Start the Stack
echo "🔥 Building and Launching StealthVault AI Stack..."
# Check if docker-compose.yml exists in the current directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ ERROR: docker-compose.yml not found!"
    echo "Please run this script from the root of the StealthVault AI repository."
    exit 1
fi

# Start services
sudo docker-compose down
sudo docker-compose up -d --build

# 6. Final Outputs
PUBLIC_IP=$(curl -s ifconfig.me)
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║          ✅ DEPLOYMENT SUCCESSFUL ✅                      ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo "StealthVault AI is now LIVE and exposed to the internet."
echo "Dashboard:  http://${PUBLIC_IP}"
echo ""
echo "Botnets and scanners will discover this IP automatically."
echo "Watch the live dashboard as real attacks roll in!"
echo ""
echo "To view logs in real-time:"
echo "  sudo docker-compose logs -f backend"
echo "═════════════════════════════════════════════════════════════"
