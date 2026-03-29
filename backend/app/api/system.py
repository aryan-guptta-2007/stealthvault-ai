"""
StealthVault AI - System Observability API
Exposes real-time internal telemetry, ML confidence trends, queue pressure, and active worker count.
"""

import time
import asyncio
try:
    import psutil
except ImportError:
    psutil = None
from fastapi import APIRouter
from app.collector.stream import stream_processor
from app.agents.orchestrator import soc_orchestrator
from app.models.db_models import DBSystemEvent
from sqlalchemy import select, desc
from app.api.rbac import RoleChecker
from fastapi import Depends
from app.core.compliance import compliance_engine
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

# RBAC Instances
soc_access = Depends(RoleChecker(["admin", "soc_analyst"]))

router = APIRouter(prefix="/system", tags=["System Observability"])

@router.get("/health")
async def health_check():
    """
    💓 Deep Health Check: Pings Postgres and Redis to verify active connectivity.
    """
    from app.database import engine
    from sqlalchemy import text
    import logging

    health = {
        "status": "healthy",
        "database": "disconnected",
        "redis": "disconnected",
        "stream_processor": "running" if stream_processor.is_running else "idle",
        "timestamp": time.time()
    }

    # 1. Ping PostgreSQL
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            health["database"] = "connected"
    except Exception as e:
        health["status"] = "degraded"
        health["database"] = f"error: {str(e)}"
        logging.error(f"PostgreSQL Health Check Failed: {e}")

    # 2. Ping Redis
    try:
        if stream_processor.redis:
            await stream_processor.redis.ping()
            health["redis"] = "connected"
    except Exception as e:
        health["status"] = "degraded"
        health["redis"] = f"error: {str(e)}"
        logging.error(f"Redis Health Check Failed: {e}")

    return health

@router.get("/metrics")
async def get_system_metrics(user: dict = soc_access):
    """
    🔬 Full Observability Plane: Returns real-time distributed cluster health.
    Includes Redis backing pressures, AI Worker Heartbeats, and ML telemetry.
    """
    # 1. Query Redis Queue Pressures
    packet_queue_size = 0
    dl_size = 0
    active_workers = 0

    if stream_processor.is_running and stream_processor.redis:
        try:
            packet_queue_size = await stream_processor.redis.llen("packet_queue")
            dl_size = await stream_processor.redis.llen("redis_dlq")
            worker_keys = await stream_processor.redis.keys("worker:heartbeat:*")
            active_workers = len(worker_keys)
        except Exception as e:
            print(f"⚠️ Redis Telemetry Error: {e}")

    # 2. Aggregated metrics & Latencies
    stream_stats = stream_processor.get_stats()
    orch = soc_orchestrator
    
    # 3. Calculate Health Score (0-100)
    # Penalize for: No workers (-50), High DLQ (-1/packet), High Latency (-1 per 10ms over 100ms)
    health_score = 100
    if active_workers == 0: health_score -= 50
    health_score -= min(dl_size, 30)
    if orch.avg_processing_ms > 100:
        health_score -= min(int((orch.avg_processing_ms - 100) / 10), 20)
    
    return {
        "status": "online" if stream_processor.is_running else "offline",
        "health_score": max(0, health_score),
        "cluster_health": {
            "active_ai_workers": active_workers,
            "packet_queue_size": packet_queue_size,
            "dead_letter_queue_size": dl_size,
        },
        "performance": {
            "total_processing_ms": round(orch.avg_processing_ms, 2),
            "detector_stage_ms": round(orch.avg_detector_ms, 2),
            "analyst_stage_ms": round(orch.avg_analyst_ms, 2),
            "packets_per_second": stream_stats.get("packets_per_second", 0),
        },
        "ml_telemetry": {
            "average_confidence": round(orch.avg_confidence_score, 4),
            "unknown_percentage": round(orch.total_unknowns / max(orch.total_processed, 1), 4),
            "total_unknowns": orch.total_unknowns,
        },
        "totals": {
            "total_processed": orch.total_processed,
            "total_dropped_by_backpressure": stream_stats.get("total_dropped", 0),
        },
        "host": {
            "cpu_percent": psutil.cpu_percent() if psutil else 0,
            "ram_percent": psutil.virtual_memory().percent if psutil else 0,
            "disk_percent": psutil.disk_usage('/').percent if psutil else 0,
        },
        "worker_registry": [
            {
                "id": k.split(":")[-1],
                "status": "online",
            } for k in (await stream_processor.redis.keys("worker:heartbeat:*"))
        ] if stream_processor.redis else [],
        "timestamp": time.time()
    }

@router.get("/events")
async def get_system_events(user: dict = soc_access, limit: int = 50):
    """
    🩺 God View: Retrieve recent internal system events and errors.
    """
    tenant_id = user.get("tenant_id", "default")
    from app.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        stmt = select(DBSystemEvent).where(DBSystemEvent.tenant_id == tenant_id).order_by(desc(DBSystemEvent.timestamp)).limit(limit)
        result = await db.execute(stmt)
        events = result.scalars().all()
        
        return [
            {
                "id": e.id,
                "timestamp": e.timestamp.isoformat(),
                "level": e.level,
                "component": e.component,
                "message": e.message,
                "metadata": e.metadata_json
            } for e in events
        ]


@router.get("/compliance/export")
async def export_tenant_compliance_data(
    current_user: dict = Depends(RoleChecker(["admin", "billing_admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    🚀 GDPR COMPLIANCE EXPORT (Article 20)
    Official data portability engine for SaaS tenants.
    """
    tenant_id = current_user.get("tenant_id", "default")
    # 🔍 AUDIT: Export Action
    from app.core.audit import log_audit
    await log_audit(
        action="DATA_EXPORT",
        target=tenant_id,
        tenant_id=tenant_id,
        result="SUCCESS",
        message="Full forensic data export initiated."
    )
    
    return await compliance_engine.export_tenant_data(tenant_id, db)
