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


from app.api.system import get_system_metrics
import asyncio

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
    print("  🕰️ Defender Safety Daemon Started")

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

async def data_retention_daemon():
    """
    🧹 Data Retention Daemon
    Purges old inspection logs to prevent database bloat.
    Default: Keep 7 days of full audit trails.
    """
    from app.database import AsyncSessionLocal
    from app.models.db_models import DBInspectionLog, DBSystemEvent
    from sqlalchemy import delete
    import logging

    RETENTION_DAYS = 7
    
    while True:
        try:
            cutoff = datetime.utcnow() - timedelta(days=RETENTION_DAYS)
            async with AsyncSessionLocal() as db:
                # Purge Inspection Logs
                stmt1 = delete(DBInspectionLog).where(DBInspectionLog.timestamp < cutoff)
                res1 = await db.execute(stmt1)
                
                # Purge System Events
                stmt2 = delete(DBSystemEvent).where(DBSystemEvent.timestamp < cutoff)
                res2 = await db.execute(stmt2)
                
                await db.commit()
                
                total = res1.rowcount + res2.rowcount
                if total > 0:
                    logging.info(f"🧹 Cleanup: Purged {total} old logs (older than {cutoff}).")
        except Exception as e:
            logging.error(f"❌ Cleanup Error: {e}")
        
        # Run once every 6 hours
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
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"Metrics Daemon Error: {e}")
            
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
    Catch-all exception handler for structured error responses.
    Prevents raw 500 Internal Server Errors from reaching the client.
    """
    import traceback
    from fastapi.responses import JSONResponse
    from app.database import log_event
    
    # Generate unique Request ID for tracing
    import uuid
    request_id = str(uuid.uuid4())
    
    # Log detailed error to console and DB
    error_msg = f"🔥 UNHANDLED ERROR [{request_id}]: {str(exc)}"
    stack_trace = traceback.format_exc()
    
    # Persist the failure to the dashboard
    log_event(
        level="CRITICAL",
        component="FastAPI-Shield",
        message=error_msg,
        stack_trace=stack_trace,
        metadata={"path": request.url.path, "method": request.method}
    )
    
    # Return structured JSON
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "request_id": request_id,
            "type": type(exc).__name__,
            "detail": f"🛡️ CRITICAL FAULT: {str(exc)}", # Expose for rapid debugging
            "timestamp": datetime.utcnow().isoformat()
        }
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
app.include_router(defender_router, prefix=f"{API_PREFIX}/defender")
app.include_router(saas_router, prefix=API_PREFIX)

# Serve static frontend files
FRONTEND_DIR = os.path.join(settings.BASE_DIR, "..", "frontend", "dist")
if os.path.exists(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")


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
    return {
        "status": "healthy",
        "anomaly_model": "loaded" if anomaly_detector.is_trained else "not_trained",
        "classifier_model": "loaded" if attack_classifier.is_trained else "not_trained",
        "model_version": f"v{continuous_learner.model_version}",
        "stream_processor": "running" if stream_processor.is_running else "idle",
        "ws_connections": len(ws_manager.active_connections),
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
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"type": "PONG", "data": data})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, tenant_id)

if __name__ == "__main__":
    import uvicorn
    # Render dynamic port binding
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"🚀 Starting StealthVault AI Production Server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
