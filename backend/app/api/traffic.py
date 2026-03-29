"""
StealthVault AI - Traffic Analysis API
Endpoints for analyzing network packets and retrieving traffic stats.
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.db_models import DBTenant
from datetime import datetime
from app.core.limiter import limiter
from fastapi import Request
from app.models.alert import (
    NetworkPacket,
    ThreatAlert,
    DashboardStats,
    Severity,
)
from app.collector.extractor import extractor
from app.ai_engine.anomaly import anomaly_detector
from app.ai_engine.classifier import attack_classifier
from app.decision.risk_scorer import risk_scorer
from app.decision.brain import security_brain
from app.agents.orchestrator import soc_orchestrator

router = APIRouter(prefix="/traffic", tags=["Traffic Analysis"])

# In-memory storage (will move to DB in production)
alert_store: list[ThreatAlert] = []
packet_count: int = 0


async def get_tenant_from_api_key(
    x_api_key: str = Header(..., description="SaaS API Key for log forwarding"), 
    db: AsyncSession = Depends(get_db)
):
    """Authorize the external packet forwarder using their Tenant API Key."""
    result = await db.execute(select(DBTenant).where(DBTenant.api_key == x_api_key))
    tenant = result.scalars().first()
    if not tenant:
        raise HTTPException(status_code=401, detail="Invalid X-API-Key")
    return tenant.id


@router.post("/analyze", response_model=ThreatAlert)
@limiter.limit("1000/minute")
async def analyze_packet(
    request: Request,
    packet: NetworkPacket,
    tenant_id: str = Depends(get_tenant_from_api_key)
):
    """
    🔬 Analyze a network packet through the SOC Orchestrator.
    """
    global packet_count
    packet_count += 1
    
    # 🌍 SaaS Architecture: Bind the universally unique tenant ID
    packet.tenant_id = tenant_id

    # Use the full SOC pipeline
    soc_verdict = await soc_orchestrator.process(packet)

    # Construct the ThreatAlert for the response
    alert = ThreatAlert(
        id=soc_verdict.detection.packet.id,
        timestamp=soc_verdict.detection.packet.timestamp or datetime.utcnow(),
        packet=soc_verdict.detection.packet,
        anomaly=soc_verdict.detection.anomaly,
        classification=soc_verdict.detection.classification,
        risk=soc_verdict.detection.risk,
        brain_analysis=soc_verdict.intelligence.brain_analysis if soc_verdict.intelligence else None,
    )

    # Store in-memory for legacy /stats compatibility (optional, since we have DB now)
    if soc_verdict.detection.is_threat:
        alert_store.append(alert)
        if len(alert_store) > 1000:
            alert_store.pop(0)

    return alert


@router.post("/analyze/batch")
@limiter.limit("100/minute")
async def analyze_batch(
    request: Request,
    packets: list[NetworkPacket],
    tenant_id: str = Depends(get_tenant_from_api_key)
):
    """Analyze multiple packets at once."""
    results = []
    for packet in packets:
        # Batch requires explicit manual invocation because FastAPI relies on Depends cache per request
        packet.tenant_id = tenant_id
        result = await analyze_packet(packet, tenant_id)
        results.append(result)
    return {"analyzed": len(results), "alerts": results}


@router.get("/stats")
@limiter.limit("60/minute")
async def get_stats(request: Request):
    """Get current traffic analysis statistics."""
    return {
        "total_packets_analyzed": packet_count,
        "total_alerts": len(alert_store),
        "anomaly_detector_trained": anomaly_detector.is_trained,
        "classifier_trained": attack_classifier.is_trained,
    }
