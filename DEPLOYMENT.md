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

### 1. Automated VPS Provisioning (The Fast Path)
The fastest way to deploy is using the upgraded `deploy_vps.sh` script, which now handles automated secret generation and firewall hardening.

```bash
# On your remote host
git clone https://github.com/aryan-guptta-2007/stealthvault-ai.git
cd stealthvault-ai
chmod +x deploy_vps.sh
./deploy_vps.sh
```

### 2. Infrastructure as Code (The Enterprise Path)
For professional multi-cloud deployments, use the provided **Terraform** modules in `deploy/terraform/`.

```bash
cd deploy/terraform
terraform init
terraform plan
terraform apply
```
This will provision a hardened **AWS EC2** instance, VPC, and Security Groups tailored for the SOC.

### 3. CI/CD Pipeline (Automated Delivery)
StealthVault AI includes a pre-configured **GitHub Actions** workflow in `.github/workflows/main.yml`:
- **CI**: Runs linting and build checks on every Pull Request.
- **CD**: Automatically builds and pushes production Docker images to the **GitHub Container Registry (GHCR)** on every push to `main`.

### 4. Hardened Orchestration (Docker Compose Prod)
Production deployments use `docker-compose.prod.yml`, which includes:
- **Nginx Reverse Proxy**: Entrypoint for all traffic.
- **SSL Termination**: Automated via Let's Encrypt (Certbot).
- **Resource Isolation**: CPU and RAM limits for AI workers to prevent system DoS.

To launch manually:
```bash
docker compose -f docker-compose.prod.yml up -d
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
