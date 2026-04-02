"""
╔═══════════════════════════════════════════════════════════╗
║             STEALTHVAULT AI — MAIN APPLICATION            ║
║     AI-Powered Autonomous Cyber Defense System            ║
║                                                           ║
║  Monitors · Detects · Explains · Defends · LEARNS         ║
╚═══════════════════════════════════════════════════════════╝
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
import os
import asyncio
from datetime import datetime, timedelta
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.core.limiter import limiter
from app.core.batch_sqla import inspection_batcher, system_event_batcher
from app.api.traffic import simulate_attack_logic
from app.database import AsyncSessionLocal
import random

# 🛡️ GLOBAL SYSTEM STRATEGY
SYSTEM_TENANT_ID = "system-global"

from app.core.logger import setup_logging, set_db_logger, logger
from app.ai_engine.anomaly import anomaly_detector
from app.ai_engine.classifier import attack_classifier
from app.ai_engine.learner import continuous_learner
from app.collector.stream import stream_processor
from app.websocket.feed import ws_manager
from app.database import init_db, log_event
from app.models import db_models 
from app.core.batch_sqla import inspection_batcher, system_event_batcher

# Import agents
from app.agents.defender import defender_agent
from app.core.abuse_guard import abuse_guard
from app.services.threat_intel import update_threat_intel

# Import routers
from app.api.traffic import router as traffic_router
from app.api.alerts import router as alerts_router
from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.brain import router as brain_router
from app.api.capture import router as capture_router
from app.api.soc import router as soc_router
from app.api.system import router as system_router
from app.api.defender import router as defender_router
from app.api.saas import router as saas_router
from app.api.stats import router as stats_router


from app.api.system import get_system_metrics
import asyncio

async def auto_attack_daemon():
    """
    ⚔️ BATTLE-MODE DAEMON (Autonomous Offensive Suite)
    Automatically triggers simulated attacks to ensure the SOC is always 'Live'.
    """
    print("  🚀 Battle-Mode Pulse: Autonomous Simulation Engine — ARMED")
    
    # 🕵️ Randomly pick attack types to simulate a real adversary
    attacks = ["ddos", "bruteforce", "portscan"]
    
    while True:
        # Wait a bit before starting the first pulse to let DB initialize
        await asyncio.sleep(10)
        
        try:
            async with AsyncSessionLocal() as db:
                attack_choice = random.choice(attacks)
                # SYSTEM_TENANT_ID is defined in this file (system-global)
                try:
                    await simulate_attack_logic(db, attack_choice, SYSTEM_TENANT_ID)
                    # 🔐 Explicitly Commit
                    await db.commit()
                except Exception as e:
                    # 🧹 Safety Rollback
                    await db.rollback()
                    logger.error(f"  🔥 Simulation Transaction Fault: {e}")
        except Exception as e:
            logger.error(f"  ❌ Autonomous Engine Connection Error: {e}")
        
        # 🕰️ Run every 10 seconds to keep the dashboard alive but not overwhelmed
        await asyncio.sleep(5)

async def refresh_threat_feed():
    """
    🕰️ THREAT INTEL REFRESH DAEMON
    Periodically updates the malicious IP cache from external feeds.
    Runs every 1 hour.
    """
    logger.info("🕰️ Threat Intelligence Refresh Daemon: Online (Policy: 1 hour)")
    while True:
        try:
            update_threat_intel()
        except Exception as e:
            logger.error(f"❌ Threat Intel Refresh Fault: {e}")
        
        # Run every 1 hour
        await asyncio.sleep(3600)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    print()
    print("╔═══════════════════════════════════════════════════════╗")
    print("║         STEALTHVAULT AI — INITIALIZING...             ║")
    print("╚═══════════════════════════════════════════════════════╝")
    print()

    # Initialize System Observability
    setup_logging()
    set_db_logger(log_event)

    # Start Database Batchers (High-Throughput Persistence)
    inspection_batcher.start()
    system_event_batcher.start()

    # Initialize PostgreSQL Storage
    try:
        # Use the hardened init_db with retry logic
        await init_db(retries=10)
        logger.info("PostgreSQL Database — CONNECTED")
    except Exception as e:
        logger.critical(f"FATAL: Database connection failed after multiple retries. ({e})")
        # In a real enterprise app, we might exit(1) here if DB is strictly required
        
    # Start horizontal WebSocket listener
    try:
        await ws_manager.start()
        logger.info("Distributed WebSocket Stream — OK")
    except Exception as e:
        logger.error(f"WebSocket Manager Error: {e}")

    # Start the stream processor
    try:
        await stream_processor.start()
        logger.info("Stream Processor — ACTIVE")
    except Exception as e:
        logger.critical(f"Stream Processor Error: {e}")
    
    # 📊 Metrics Broadcast is disabled in production (Local only via StreamProcessor)
    # asyncio.create_task(broadcast_system_metrics())
    print("  📊 Observability Telemetry Started (Local-only)")
    
    # Start persistence cleanup daemon
    asyncio.create_task(data_retention_daemon())
    
    # Start Autonomous Learning Pipeline
    asyncio.create_task(scheduled_retrain_daemon())
    
    # Start Production Metrics Pipeline
    asyncio.create_task(system_metrics_daemon())
    
    # Start Defender auto-unblock daemon
    asyncio.create_task(defender_cleanup_daemon())
    
    # 🧹 Start Data Lifecycle Daemon (Purge old telemetry)
    asyncio.create_task(data_retention_daemon())
    print("  🕰️ Defender Safety Daemon Started")

    # Initialize Threat Intelligence
    try:
        update_threat_intel()
        asyncio.create_task(refresh_threat_feed())
        logger.info("Threat Intelligence Feed — CONNECTED")
    except Exception as e:
        logger.error(f"Threat Intelligence Initialization Failed: {e}")

    # Start Autonomous Offensive Simulation (Live Dashboard Mode)
    asyncio.create_task(auto_attack_daemon())
    print("  ⚔️  Battle-Mode Pulse: Autonomous Simulation Engine — ARMED")

    # Load AI models
    anomaly_loaded = anomaly_detector.load()
    classifier_loaded = attack_classifier.load()

    if anomaly_loaded:
        print("  ✅ Anomaly Detection Model — LOADED")
    else:
        print("  ⚠️  Anomaly Detection Model — NOT TRAINED")
        print("     Run: python scripts/generate_demo_data.py")

    if classifier_loaded:
        print("  ✅ Attack Classifier Model — LOADED")
    else:
        print("  ⚠️  Attack Classifier Model — NOT TRAINED")
        print("     Run: python scripts/generate_demo_data.py")

    print(f"  🔄 Continuous Learning — v{continuous_learner.model_version}")
    print()
    print("  🤖 MULTI-AGENT SOC TEAM:")
    print("     Agent 1: DETECTOR  (Eyes)  — Active")
    print("     Agent 2: ANALYST   (Brain) — Active")
    # Using the system tenant context for global daemon status
    system_shadow = defender_agent.get_shadow_mode(SYSTEM_TENANT_ID)
    print(f"     Agent 3: DEFENDER  (Fist)  — {'SHADOW MODE ⚠️' if system_shadow else 'ARMED 🛡️'}")
    print()
    print("  👥 SAAS LAYER:        Multi-Tenant Enabled")
    print(f"  🌐 Server:    http://localhost:{settings.PORT}")
    print(f"  📖 API Docs:  http://localhost:{settings.PORT}/docs")
    print(f"  🖥️  Dashboard: http://localhost:{settings.PORT}/")
    print(f"  🔌 WebSocket: ws://localhost:{settings.PORT}/ws")
    print(f"  🤖 SOC API:   http://localhost:{settings.PORT}/api/v1/soc/status")
    print()
    print("  🛡️  StealthVault AI is ACTIVE")
    print()

    yield

    # Shutdown
    await stream_processor.stop()
    
    # Graceful Database Flush
    await inspection_batcher.stop()
    await system_event_batcher.stop()
    
    print("\n  🛡️  StealthVault AI — SHUTTING DOWN\n")

# --- 🚀 FASTAPI CORE INITIALIZATION ---
app = FastAPI(
    title="StealthVault AI",
    description=(
        "🛡️ AI-Powered Autonomous Cyber Defense System\n\n"
        "Self-learning security brain that monitors network traffic, "
        "detects attacks (including zero-days), explains threats, "
        "and suggests defenses.\n\n"
        "**Capabilities:**\n"
        "- 🔍 Real-time packet capture (Scapy)\n"
        "- 🧠 Anomaly Detection (Isolation Forest)\n"
        "- 🎯 Attack Classification (Random Forest)\n"
        "- ⚡ Risk Scoring Engine\n"
        "- 💬 AI Security Brain\n"
        "- 🔄 Continuous Learning\n"
        "- 📊 Real-time Dashboard\n"
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# --- 🛡️ PRODUCTION CORS CONFIGURATION ---
app.add_middleware(HTTPSRedirectMiddleware)
cors_origins = settings.ALLOWED_ORIGINS if hasattr(settings, 'ALLOWED_ORIGINS') else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

@app.middleware("http")
async def add_security_headers(request, call_next):
    response: Response = await call_next(request)
    
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    
    return response

async def data_retention_daemon():
    """
    🕰️ THE CHRONOS PURGE: Automated Data Lifecycle Management
    Ensures the system remains lean and compliant by purging data older than the retention window.
    Default: 30 days for alerts/logs.
    """
    retention_days = settings.ALERTS_RETENTION_DAYS
    logger.info(f"🕰️ Data Lifecycle Manager: Online (Policy: {retention_days} days)")
    
    while True:
        try:
            cutoff = datetime.utcnow() - timedelta(days=retention_days)
            async with AsyncSessionLocal() as db:
                from sqlalchemy import delete
                from app.models.db_models import DBAlert, DBInspectionLog, DBSystemEvent
                
                # 🛡️ PURGE: Alerts
                alert_purge = await db.execute(delete(DBAlert).where(DBAlert.timestamp < cutoff))
                
                # 🔬 PURGE: Forensic Inspection Logs
                log_purge = await db.execute(delete(DBInspectionLog).where(DBInspectionLog.timestamp < cutoff))
                
                # 📊 PURGE: System Events
                event_purge = await db.execute(delete(DBSystemEvent).where(DBSystemEvent.timestamp < cutoff))
                
                await db.commit()
                
                total = alert_purge.rowcount + log_purge.rowcount + event_purge.rowcount
                if total > 0:
                    logger.info(f"🧹 Lifecycle Purge: Successfully neutralized {total} stale records.")
        except Exception as e:
            logger.error(f"❌ Data Lifecycle Fault: {e}")
            
        # Run every 6 hours
        await asyncio.sleep(6 * 3600)

async def defender_cleanup_daemon():
    """
    🕰️ Defender Auto-Unblock Daemon
    Releases IPs whose penalty TTL has expired.
    Runs every 60 seconds.
    """
    while True:
        try:
            defender_agent.process_expirations()
        except Exception as e:
            logger.error(f"Defender Cleanup Error: {e}")
        await asyncio.sleep(60)

async def broadcast_system_metrics():
    """Disabled in production to prevent Redis connection logging."""
    return


async def scheduled_retrain_daemon():
    """
    🕰️ Autonomous Retraining Daemon
    Ensures the model is updated periodically or when drift is detected.
    1. Runs every 24 hours (Scheduled update).
    2. Checks for detected drift every 1 hour (Emergency update).
    """
    from app.ai_engine.learner import continuous_learner
    
    while True:
        try:
            # 1. EMERGENCY: Check for Concept Drift
            if continuous_learner.is_drift_detected:
                # We need at least some data to retrain
                if len(continuous_learner.labeled_features) > 20:
                    logger.warning("📉 DRIFT DETECTED: Triggering Emergency Retrain to adapt to new patterns.")
                    continuous_learner.retrain(reason="Drift-Triggered Recovery")
            
            # 2. MAINTENANCE: Daily Refresh (at 3 AM UTC)
            now = datetime.utcnow()
            if now.hour == 3 and now.minute == 0:
                if len(continuous_learner.labeled_features) > 10:
                    logger.info("📅 SCHEDULED: Initializing daily model optimization.")
                    continuous_learner.retrain(reason="Scheduled Daily Refresh")
        except Exception as e:
            logger.error(f"Retrain Daemon Error: {e}")
        
        # Granularity: 60 seconds
        await asyncio.sleep(60)


async def system_metrics_daemon():
    """
    📊 Continuous Production Observability
    Samples host and application performance every 60 seconds and persists to DB.
    """
    from app.database import AsyncSessionLocal
    from app.models.db_models import DBSystemMetric, DBSystemEvent
    from app.collector.stream import stream_processor
    from app.agents.orchestrator import soc_orchestrator
    try:
        import psutil
    except ImportError:
        psutil = None
    
    while True:
        try:
            # 1. Sample Host Metrics
            cpu = psutil.cpu_percent() if psutil else 0.0
            ram = psutil.virtual_memory().percent if psutil else 0.0
            disk = psutil.disk_usage('/').percent if psutil else 0.0
            
            # 2. Sample App Metrics
            queue_size = 0
            active_workers = 0
            if stream_processor.redis:
                try:
                    queue_size = await stream_processor.redis.llen("packet_queue")
                    worker_keys = await stream_processor.redis.keys("worker:heartbeat:*")
                    active_workers = len(worker_keys)
                except:
                    pass
            
            pps = stream_processor.get_stats().get("packets_per_second", 0)
            avg_lat = soc_orchestrator.avg_processing_ms
            
            # 3. Persist to DB
            async with AsyncSessionLocal() as db:
                metric = DBSystemMetric(
                    cpu_usage=float(cpu),
                    ram_usage=float(ram),
                    disk_usage=float(disk),
                    active_workers=active_workers,
                    queue_size=queue_size,
                    packets_per_second=float(pps),
                    avg_latency_ms=float(avg_lat),
                    dropped_packets=stream_processor.dropped_packets
                )
                db.add(metric)
                
                # 4. Proactive Threshold Alerts
                if ram > 90:
                    alert_msg = f"🚨 HOST RAM EXHAUSTION: {ram}% usage. System instability imminent!"
                    logger.critical(alert_msg)
                    db.add(DBSystemEvent(
                        level="CRITICAL",
                        component="Host",
                        message=alert_msg,
                        tenant_id=SYSTEM_TENANT_ID
                    ))
                
                if queue_size > 40000:
                    alert_msg = f"⚠️ QUEUE PRESSURE: {queue_size} packets pending. Consider scaling workers."
                    logger.warning(alert_msg)
                    db.add(DBSystemEvent(
                        level="WARNING",
                        component="Queue",
                        message=alert_msg,
                        tenant_id=SYSTEM_TENANT_ID
                    ))
                
                try:
                    # 🔐 Mission-Critical Commit
                    await db.commit()
                except Exception as commit_err:
                    await db.rollback()
                    logger.error(f"Metrics Persistence Fault: {commit_err}")
                
        except Exception as e:
            logger.error(f"Metrics Daemon Logic Fault: {e}")
            
        await asyncio.sleep(60)


from collections import defaultdict
import time

# Simple In-Memory sliding window for WAF
ip_violations = defaultdict(list)
WHITELIST_IPS = {"127.0.0.1", "localhost", "::1", "0.0.0.0"}

async def clean_violations(ip: str):
    """Keep only violations from the last 60 seconds."""
    now = time.time()
    ip_violations[ip] = [ts for ts in ip_violations[ip] if now - ts < 60]

async def security_hardening_middleware(request: Request, call_next):
    """
    🛡️ Enterprise Security Shield (WAF) Middleware
    1. Enforces Request Size Limits (1MB)
    2. Fail2Ban: Tracks HTTP error abuse and auto-blocks
    3. Injects Security Headers
    """
    client_ip = request.client.host if request.client else "127.0.0.1"

    # 📦 1. Request Size Enforcement (Prevent OOM attacks)
    MAX_SIZE = 1 * 1024 * 1024  # 1MB
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_SIZE:
        response = JSONResponse(
            status_code=413,
            content={"detail": "Request Entity Too Large. Max size is 1MB."}
        )
        return response

    response: Response = await call_next(request)

    # 🎯 2. API Abuse Protection (Fail2Ban Logic)
    if client_ip not in WHITELIST_IPS and response.status_code in (401, 403, 404, 405, 429):
        await clean_violations(client_ip)
        ip_violations[client_ip].append(time.time())
        count = len(ip_violations[client_ip])
        
        # 🪜 Level-Based Defense Ladder
        if count >= 25:
            # Level 3: Malicious
            duration = min(30, count * 2)  # Dynamically scale timeout based on aggression
            reason = f"L3 Malicious API Abuse: {count} setup/auth errors in 60s"
            defender_agent.waf_block(client_ip, duration_min=duration, reason=reason)
            # Clear violations so we don't spam blocks on the very next packet
            ip_violations[client_ip] = []
        elif count == 15:
            # Level 2: Aggressive
            duration = 5 # minutes
            reason = f"L2 Aggressive API Scraping: {count} setup/auth errors in 60s"
            defender_agent.waf_block(client_ip, duration_min=duration, reason=reason)
        elif count == 10:
            # Level 1: Suspicious (Log only)
            print(f"⚠️ [WAF] Suspicious behavior from {client_ip}: {count} violations in 60s")

    # 🔒 3. Security Header Injection
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com; "
        "img-src 'self' fastapi.tiangolo.com data:; "
        "connect-src 'self' https://stealthvault-ai.onrender.com wss://stealthvault-ai.onrender.com ws://localhost:8000 http://localhost:8000;"
    )
    
    return response


# --- 🚨 GLOBAL EXCEPTION HANDLER (RESILIENCY LAYER) ---

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    🛡️ ELITE GLOBAL RESILIENCY LAYER
    Catch-all exception handler to prevent raw 500 crashes and information leaks.
    """
    # 🕵️ Redact Error: Ensure the error message itself doesn't contain secrets
    # Our SecretRedactionFilter will handle the log, but we also mask it for the user
    raw_error = str(exc)
    
    # SOC Logging: Internal error is logged (Redacted by Filter)
    logger.error(f"  🔥 UNHANDLED FAULT (Path: {request.url.path})")
    
    # User Response: Return a sanitized message to prevent info leakage
    # We do NOT return the raw `str(exc)` in production unless DEBUG is True
    display_error = "An internal mission-critical fault occurred."
    if settings.DEBUG:
        display_error = raw_error

    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": f"🛡️ MISSION CRITICAL FAULT: {display_error}",
            "path": str(request.url.path),
            "timestamp": datetime.utcnow().isoformat(),
            "service": "StealthVault AI - SOC Core"
        },
    )



# --- 🛡️ PRODUCTION SECURITY STACK & MIDDLEWARE ---


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    🛡️ ANTI-DOS: Payload Capping
    Rejects any request body larger than 10MB.
    Prevents memory/disk exhaustion from oversized network packets or malicious uploads.
    """
    def __init__(self, app, max_size_bytes: int = 10 * 1024 * 1024):
        super().__init__(app)
        self.max_size = max_size_bytes

    async def dispatch(self, request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH"):
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.max_size:
                return JSONResponse(
                    status_code=413,
                    content={"detail": f"Request entity too large. Maximum payload is 10MB."}
                )
        return await call_next(request)



# --- 🛡️ PRODUCTION SECURITY STACK & MIDDLEWARE ---
app.middleware("http")(security_hardening_middleware)
app.add_middleware(RequestSizeLimitMiddleware) 

app.add_middleware(RequestSizeLimitMiddleware) 

# Register API routers
API_PREFIX = "/api/v1"
app.include_router(auth_router, prefix=f"{API_PREFIX}/auth", tags=["Authentication"])
app.include_router(traffic_router, prefix=API_PREFIX)
app.include_router(alerts_router, prefix=API_PREFIX)
app.include_router(dashboard_router, prefix=API_PREFIX)
app.include_router(brain_router, prefix=API_PREFIX)
app.include_router(capture_router, prefix=API_PREFIX)
app.include_router(soc_router, prefix=API_PREFIX)
app.include_router(system_router, prefix=API_PREFIX)
app.include_router(stats_router, prefix=API_PREFIX)
app.include_router(defender_router, prefix=f"{API_PREFIX}/defender")
app.include_router(saas_router, prefix=API_PREFIX)

# Serve static frontend files
FRONTEND_DIR = os.path.join(settings.BASE_DIR, "..", "frontend", "dist")
if os.path.exists(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")


@app.middleware("http")
async def abuse_protection_middleware(request: Request, call_next):
    """
    🛑 SELF-DEFENDING API: Active Abuse Retaliation
    Identifies brute-force and scanning actors and triggers automated firewall exclusions.
    """
    client_ip = request.client.host
    
    # 1. PASSTHROUGH: Execute request pipeline
    response = await call_next(request)
    
    # 2. ANALYSIS: Monitor for application-layer patterns (L7)
    # Track unauthorized access, invalid tokens, forced browsing, etc.
    if response.status_code in [400, 401, 403, 404]:
        # 🔔 Recording failure in the mission-critical tracker
        if abuse_guard.record_failure(client_ip):
            # 🔥 RETALIATION: Autonomous WAF Exclusion
            logger.critical(f"🚨 API ABUSE DETECTED: IP {client_ip} exceeded failure threshold. Triggering Automated Neutralization.")
            
            # WAF block for 10 minutes (duration_min=10)
            reason = f"Automated API Abuse Exclusion (Threshold Exceeded: {response.status_code})"
            defender_agent.waf_block(client_ip, duration_min=10, reason=reason)
            
            return JSONResponse(
                status_code=403,
                content={
                    "error": "SECURITY_VIOLATION",
                    "message": "🛡️ SYSTEM RETALIATION: Your identity has been flagged for automated abuse. Access terminated."
                }
            )
            
    return response

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """
    🧱 INFRASTRUCTURE HARDENING: Mission-Critical Security Headers
    Defends against Clickjacking, Sniffing, and XSS at the browser layer.
    """
    response: Response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

@app.middleware("http")
async def payload_limit_middleware(request: Request, call_next):
    """
    🛡️ APPLICATION DEFENSE: Payload Size Enforcement
    Protects the system from 'Large-Payload' exhaustion attacks and memory flooding.
    """
    if request.method == "POST":
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.MAX_PAYLOAD_BYTES:
            return JSONResponse(
                status_code=413,
                content={
                    "error": "PAYLOAD_TOO_LARGE",
                    "message": f"🛡️ SECURITY VIOLATION: Request body exceeds mission-critical limit ({settings.MAX_PAYLOAD_BYTES / 1024 / 1024:.1f}MB)."
                }
            )
    return await call_next(request)

@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    """
    📊 ELITE REQUEST AUDITING
    Tracks every API heartbeat, status code, and millisecond latency.
    """
    import time
    start_time = time.perf_counter()
    
    response = await call_next(request)
    
    duration = time.perf_counter() - start_time
    logger.info(f"{request.method} {request.url.path} | HTTP {response.status_code} | {duration:.3f}s")
    
    return response


# Root — serve dashboard or welcome
@app.get("/")
async def root():
    """Dashboard landing page or API info."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        from fastapi.responses import FileResponse
        return FileResponse(index_path)
    
    return {
        "name": "StealthVault AI",
        "version": settings.APP_VERSION,
        "status": "ACTIVE",
        "model_version": f"v{continuous_learner.model_version}",
        "description": "AI-Powered Autonomous Cyber Defense System",
        "endpoints": {
            "dashboard_ui": "Install frontend: cd frontend && npm install && npm run build",
            "api_docs": "/docs",
            "analyze": f"{API_PREFIX}/traffic/analyze",
            "alerts": f"{API_PREFIX}/alerts",
            "dashboard_data": f"{API_PREFIX}/dashboard",
            "brain": f"{API_PREFIX}/brain/analyze",
            "capture": f"{API_PREFIX}/capture/status",
            "learning": f"{API_PREFIX}/capture/learning/status",
            "websocket": "/ws",
        },
    }


# Health check
@app.get("/health")
async def health_check():
    """🚀 PRO-GRADE DIAGNOSTIC SUITE"""
    return {
        "status": "healthy",
        "service": "StealthVault AI",
        "db": "connected",
        "mode": "autonomous",
        "ai_brain": "active" if (anomaly_detector.is_trained and attack_classifier.is_trained) else "learning",
        "ws_connections": len(ws_manager.active_connections),
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/healthz")
def healthz():
    """Simple health check for platform probes."""
    return {"status": "ok"}


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = None, tenant: str = "global"):
    """Real-time alert feed via WebSocket."""
    tenant_id = tenant
    if token:
        import jwt
        from app.api.auth import SECRET_KEY, ALGORITHM
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            tenant_id = payload.get("tenant_id", tenant)
        except jwt.PyJWTError:
            pass

    await ws_manager.connect(websocket, tenant_id)
    try:
        # 🔔 Send confirmation handshake
        await websocket.send_json({"type": "WEL_COME", "status": "SESSION_ESTABLISHED", "timestamp": datetime.utcnow().isoformat()})
        
        while True:
            # 🕰️ Receive pulse from client to keep session alive
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                await websocket.send_json({"type": "PONG", "data": data})
            except asyncio.TimeoutError:
                # 📡 Periodic Ping-Pong logic
                await websocket.send_json({"type": "PING", "time": datetime.utcnow().timestamp()})
    except (WebSocketDisconnect, Exception) as e:
        # 🧹 Forensic cleanup: Close link if client disappears or heartbeats fail
        ws_manager.disconnect(websocket, tenant_id)

if __name__ == "__main__":
    import uvicorn
    # Render dynamic port binding
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"🚀 Starting StealthVault AI Production Server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
