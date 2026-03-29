# 🛰️ Deployment Guide: StealthVault AI Production

This guide documents the path from local development to a globally-exposed, production-hardened StealthVault AI instance.

## 🧱 Production Infrastructure Requirements

### Minimum Recommendations
| Resource | For 1-3 Tenants | For Enterprise |
|----------|-----------------|----------------|
| CPU | 2 Cores | 8 Cores |
| RAM | 4 GB | 16 GB+ |
| Storage | 20 GB SSD | 100 GB NVMe |
| OS | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS |

---

## 🚀 The 5-Step Deployment Pipeline

### 1. Automated Provisioning
The fastest way to deploy is using the provided `deploy_vps.sh` script.

```bash
# On your remote VPS ssh
git clone https://github.com/YOUR_USER/stealthvault-ai.git
cd stealthvault-ai
chmod +x deploy_vps.sh
./deploy_vps.sh
```

### 2. Manual SSL Termination (Recommended)
While the `docker-compose` stack exposes port 80/443, using **Nginx + Certbot** on the host is the safest approach.

```nginx
# /etc/nginx/sites-available/stealthvault
server {
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:5173; # Frontend
    }

    location /api {
        proxy_pass http://localhost:8000; # Backend
    }

    location /ws {
        proxy_pass http://localhost:8000; # WebSockets
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
    }
}
```

### 3. Database Persistence & Backups
The production stack uses **PostgreSQL**. 
> [!IMPORTANT]
> Change the default `POSTGRES_PASSWORD` in your production environment variables before launching.

### 4. Neural Model Persistence
AI models are stored in `backend/data/*.pkl`. Ensure this directory is backed up frequently. If metrics show accuracy drift, trigger a manual retrain via the API or UI.

### 5. Firewall Configuration
Ensure the host firewall (UFW) is active:
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp # Only if not using Nginx reverse proxy
sudo ufw enable
```

---

## 🩺 Health & Monitoring

- **API Docs**: `http://your-ip:8000/docs`
- **SOC Metrics**: `http://your-ip:8000/api/v1/soc/status`
- **Docker Logs**: `docker-compose logs -f`

## 🛡️ Hardening Check
1. [ ] JWT Secret Key changed from default.
2. [ ] Postgres password unique and strong.
3. [ ] Nginx rate limiting enabled for `/api/v1/auth`.
4. [ ] Defender Agent set to `SHADOW_MODE` initially.
