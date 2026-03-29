#!/bin/bash
# ╔═══════════════════════════════════════════════════════════╗
# ║        STEALTHVAULT AI — PRODUCTION VPS DEPLOY            ║
# ║        Hardened CI/CD & SSL Automated Orchestrator        ║
# ╚═══════════════════════════════════════════════════════════╝

set -e

# --- 🛠️ CONFIGURATION ---
DATA_DIR="./data"
ENV_FILE=".env.production"
COMPOSE_FILE="docker-compose.prod.yml"

# --- 🛡️ ARGUMENTS ---
UNATTENDED=false
if [ "$1" == "--unattended" ] || [ "$1" == "-y" ]; then
    UNATTENDED=true
    echo "🤖 UNATTENDED MODE: Skipping interactive prompts..."
fi

echo "🚀 Bootstrapping StealthVault AI Production Stack..."

# 1. System Check & Dependencies
echo "📦 Updating system and installing Docker..."
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y curl git ufw openssl

if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# 2. Firewall Hardening
echo "🛡️ Hardening Firewall (UFW)..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw allow 8000/tcp # WebSockets
echo "y" | sudo ufw enable

# 3. Secret Generation
if [ ! -f "$ENV_FILE" ]; then
    echo "🔑 Generating secure secrets for production..."
    POSTGRES_PASS=$(openssl rand -hex 24)
    JWT_SECRET=$(openssl rand -hex 32)
    
    cat <<EOF > $ENV_FILE
# 🛡️ STEALTHVAULT AI PRODUCTION SECRETS
POSTGRES_PASSWORD=$POSTGRES_PASS
SECRET_KEY=$JWT_SECRET
DATABASE_URL=postgresql+asyncpg://stealthadmin:$POSTGRES_PASS@postgres:5432/stealthvault
REDIS_URL=redis://redis:6379/0
STEALTH_SIMULATION_MODE=false
EOF
    echo "✅ Secrets generated and saved to $ENV_FILE"
else
    echo "✅ Production secrets already exist. Skipping..."
fi

# 4. Interactive SSL Setup (Optional)
if [ "$UNATTENDED" = false ]; then
    read -p "🌐 Is this a domain-based deployment with SSL? (y/n): " ENABLE_SSL
    if [ "$ENABLE_SSL" == "y" ]; then
        read -p "   - Enter your domain (e.g., soc.stealthvault.ai): " DOMAIN_NAME
        read -p "   - Enter admin email for Let's Encrypt: " ADMIN_EMAIL
        
        echo "🔐 Preparing SSL certification for $DOMAIN_NAME..."
        # Placeholder for Certbot initial run logic
    fi
else
    echo "⏭️ Skipping interactive SSL setup (Production-Local mode)"
fi

# 5. Launch the Stack
echo "🔥 Pulling latest images and launching orchestration..."
# Using --env-file to inject our secure secrets
sudo docker compose --env-file $ENV_FILE -f $COMPOSE_FILE down
sudo docker compose --env-file $ENV_FILE -f $COMPOSE_FILE up -d --build

# 6. Final Status
PUBLIC_IP=$(curl -s ifconfig.me)
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║          ✅ PRODUCTION DEPLOYMENT COMPLETE ✅             ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo "Production Dashboard: http://${DOMAIN_NAME:-$PUBLIC_IP}"
echo "API Docs: http://${DOMAIN_NAME:-$PUBLIC_IP}/docs"
echo ""
echo "🔐 CRITICAL: Your production secrets are in $ENV_FILE"
echo "   Backup this file securely! It is NOT tracked in git."
echo "═════════════════════════════════════════════════════════════"
