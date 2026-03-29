#!/bin/bash
# 🛡️ StealthVault AI - Uptime Watchdog
# Ensures 24/7 autonomous SOC operations.

LOG_FILE="/var/log/stealthvault_watchdog.log"
COMPOSE_FILE="docker-compose.prod.yml"

echo "[$(date)] 🔍 Starting health check..." >> $LOG_FILE

# 1. 🌐 Check if the API is responsive
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/system/health)

if [ "$STATUS_CODE" -ne 200 ]; then
    echo "[$(date)] ⚠️ SOC API is DOWN (Status: $STATUS_CODE). Attempting recovery..." >> $LOG_FILE
    
    # Restart core services
    docker-compose -f $COMPOSE_FILE restart backend worker_anomaly worker_risk
    
    echo "[$(date)] ✅ Recovery command executed." >> $LOG_FILE
else
    echo "[$(date)] ✨ SOC System Healthy." >> $LOG_FILE
fi

# 2. 🧹 Cleanup old container logs (Optional but good for 24/7 VPS)
# docker system prune -f --filter "until=24h"

echo "[$(date)] ✅ Watchdog cycle complete." >> $LOG_FILE
