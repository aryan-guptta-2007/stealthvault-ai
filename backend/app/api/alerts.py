"""
StealthVault AI - Alerts API
Endpoints for managing and retrieving security alerts.
"""

from fastapi import APIRouter, Query, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from app.database import get_db
from app.models.db_models import DBAlert
from app.models.alert import ThreatAlert, Severity, NetworkPacket, AnomalyResult, ClassificationResult, RiskScore, BrainAnalysis, GeoLocation
from app.api.auth import get_current_user, get_optional_user
from app.core.limiter import limiter
from fastapi import Request
from pydantic import BaseModel
from app.ai_engine.learner import continuous_learner
from app.collector.extractor import extractor
from app.core.audit import log_audit
import numpy as np


def mask_ip(ip: str | None) -> str:
    """
    🛡️ PRIVACY FIREWALL: Anonymize IP addresses for non-privileged views.
    Ensures that exact hosts are hidden while preserving network context.
    """
    if not ip:
        return "x.x.x.x"
    try:
        # IPv4 Masking (Mask last two octets)
        parts = ip.split('.')
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.x.x"
        
        # IPv6 Masking (Mask last 4 segments)
        ipv6_parts = ip.split(':')
        if len(ipv6_parts) >= 4:
            return f"{':'.join(ipv6_parts[:4])}:xxxx:xxxx:xxxx:xxxx"
            
        return "xxxx:xxxx:xxxx:xxxx"
    except Exception:
        return "x.x.x.x"

router = APIRouter(prefix="/alerts", tags=["Alerts"])

def _db_alert_to_pydantic(db_alert: DBAlert, anonymize: bool = False) -> ThreatAlert:
    packet = NetworkPacket(**db_alert.packet_data)
    brain = BrainAnalysis(**db_alert.brain_analysis) if db_alert.brain_analysis else None
    
    if anonymize:
        # 🧪 ANONYMIZE: Mission-critical identity preservation
        packet.src_ip = mask_ip(str(packet.src_ip))
        packet.dst_ip = mask_ip(str(packet.dst_ip))
        
        # 🔐 ZERO-TRUST: Hide proprietary analysis from public dashboard
        if brain:
            brain.attack_name = "🛡️ PROTECTED"
            brain.description = "Full analysis is only available to authorized SOC personnel. Authentication Required."
            brain.recommended_actions = ["[PROTECTED]"]

    return ThreatAlert(
        id=db_alert.id,
        timestamp=db_alert.timestamp,
        attack_type=db_alert.attack_type,
        packet=packet,
        anomaly=AnomalyResult(**db_alert.anomaly_data),
        classification=ClassificationResult(**db_alert.classification_data),
        risk=RiskScore(**(db_alert.risk_data or {
            "score": db_alert.risk_score,
            "severity": db_alert.severity,
            "anomaly_contribution": 0.0,
            "classification_contribution": 0.0,
            "behavior_flags": []
        })),
        brain_analysis=brain,
        geo_location=GeoLocation(**db_alert.geo_data) if db_alert.geo_data else GeoLocation()
    )

@router.get("/", response_model=list[ThreatAlert])
@limiter.limit("60/minute")
async def get_alerts(
    request: Request,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sortBy: str = Query("timestamp", description="Field to sort by"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order: asc or desc"),
    severity: str | None = Query(None, description="Filter by severity: low, medium, high, critical"),
    current_user: object | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    """Get recent security alerts from database, newest first. Anonymized if public."""
    tenant_id = getattr(current_user, "tenant_id", "default") if current_user else "default"
    is_public = current_user is None
    
    stmt = select(DBAlert).where(DBAlert.tenant_id == tenant_id)
    if severity:
        stmt = stmt.where(DBAlert.severity == severity.lower())
        
    # Apply dynamic sorting and pagination
    from sqlalchemy import asc
    sort_attr = getattr(DBAlert, sortBy, DBAlert.timestamp)
    stmt = stmt.order_by(desc(sort_attr) if order == "desc" else asc(sort_attr))
    stmt = stmt.offset(offset).limit(limit)
    
    result = await db.execute(stmt)
    db_alerts = result.scalars().all()
    pydantic_alerts = [_db_alert_to_pydantic(a, anonymize=is_public) for a in db_alerts]
    
    # 🛡️ SAFE CONVERSION SAFEGUARD
    valid_types = {"Normal", "DDoS", "PortScan", "BruteForce", "Malware", "SQLInjection", "XSS", "Unknown"}
    return [a for a in pydantic_alerts if a.attack_type in valid_types]

@router.get("/critical", response_model=list[ThreatAlert])
@limiter.limit("60/minute")
async def get_critical_alerts(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sortBy: str = Query("timestamp", description="Field to sort by"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order: asc or desc"),
    current_user: object | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    """Get only critical and high severity alerts from DB. Anonymized if public."""
    tenant_id = getattr(current_user, "tenant_id", "default") if current_user else "default"
    is_public = current_user is None
    
    stmt = select(DBAlert).where(
        DBAlert.tenant_id == tenant_id,
        DBAlert.severity.in_(["critical", "high"])
    )
    
    # Apply dynamic sorting and pagination
    from sqlalchemy import asc
    sort_attr = getattr(DBAlert, sortBy, DBAlert.timestamp)
    stmt = stmt.order_by(desc(sort_attr) if order == "desc" else asc(sort_attr))
    stmt = stmt.offset(offset).limit(limit)
    
    result = await db.execute(stmt)
    db_alerts = result.scalars().all()
    pydantic_alerts = [_db_alert_to_pydantic(a, anonymize=is_public) for a in db_alerts]
    
    # 🛡️ SAFE CONVERSION SAFEGUARD
    valid_types = {"Normal", "DDoS", "PortScan", "BruteForce", "Malware", "SQLInjection", "XSS", "Unknown"}
    return [a for a in pydantic_alerts if a.attack_type in valid_types]


@router.get("/count")
@limiter.limit("60/minute")
async def get_alert_counts(request: Request, current_user: object | None = Depends(get_optional_user), db: AsyncSession = Depends(get_db)):
    """Get alert counts by severity from DB."""
    tenant_id = getattr(current_user, "tenant_id", "default") if current_user else "default"
    
    from sqlalchemy import func
    stmt = select(DBAlert.severity, func.count(DBAlert.id)).where(DBAlert.tenant_id == tenant_id).group_by(DBAlert.severity)
    result = await db.execute(stmt)
    
    counts = {"total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0}
    for severity, count in result.all():
        counts[severity] = count
        counts["total"] += count
        
    return counts


@router.get("/{alert_id}", response_model=ThreatAlert)
@limiter.limit("60/minute")
async def get_alert(request: Request, alert_id: str, current_user: object | None = Depends(get_optional_user), db: AsyncSession = Depends(get_db)):
    """Get a specific alert by ID from DB."""
    tenant_id = getattr(current_user, "tenant_id", "default") if current_user else "default"
    is_public = current_user is None
    
    stmt = select(DBAlert).where(DBAlert.id == alert_id, DBAlert.tenant_id == tenant_id)
    result = await db.execute(stmt)
    db_alert = result.scalars().first()
    
    if not db_alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    return _db_alert_to_pydantic(db_alert, anonymize=is_public)


# --- 🧪 FEEDBACK & CONTINUOUS LEARNING ---

class FeedbackRequest(BaseModel):
    """Analyst feedback for a specific alert."""
    label: str  # The corrected AttackType name or value
    is_normal: bool = False

@router.post("/{alert_id}/confirm")
@limiter.limit("20/minute")
async def confirm_alert(
    request: Request,
    alert_id: str,
    payload: FeedbackRequest = Body(...),
    current_user: object = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    ✅ Analyst Confirmation
    Validates the alert and feeds it to the Continuous Learning engine.
    """
    tenant_id = getattr(current_user, "tenant_id", "default")
    
    stmt = select(DBAlert).where(DBAlert.id == alert_id, DBAlert.tenant_id == tenant_id)
    result = await db.execute(stmt)
    db_alert = result.scalars().first()
    
    if not db_alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    # Extract features from the original packet data
    packet = NetworkPacket(**db_alert.packet_data)
    features = extractor.extract(packet)
    feature_array = extractor.to_numpy(features)
    
    # Submit to learner
    learn_result = continuous_learner.add_feedback(
        features=feature_array,
        confirmed_label=payload.label,
        is_normal=payload.is_normal,
        original_confidence=db_alert.risk_score,
        signal_count=1 # Individual confirmation counts as 1 verified signal
    )

    # 🛡️ AUDIT: Analyst Confirmation
    await log_audit(
        action="CONFIRM_ALERT",
        target=alert_id,
        tenant_id=tenant_id,
        user_id=getattr(current_user, "uid", None),
        username=getattr(current_user, "username", "unknown"),
        result="SUCCESS",
        metadata={"label": payload.label, "is_normal": payload.is_normal}
    )
    
    return {
        "status": "confirmed",
        "alert_id": alert_id,
        "label": payload.label,
        "learning": learn_result
    }

@router.post("/{alert_id}/reject")
@limiter.limit("20/minute")
async def reject_alert(
    request: Request,
    alert_id: str,
    current_user: object = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    ❌ Analyst Rejection (False Positive)
    Marks the alert as "Normal" and feeds it to the training set as a counter-example.
    """
    tenant_id = getattr(current_user, "tenant_id", "default")
    
    stmt = select(DBAlert).where(DBAlert.id == alert_id, DBAlert.tenant_id == tenant_id)
    result = await db.execute(stmt)
    db_alert = result.scalars().first()
    
    if not db_alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    packet = NetworkPacket(**db_alert.packet_data)
    features = extractor.extract(packet)
    feature_array = extractor.to_numpy(features)
    
    # Rejection always maps to "Normal"
    learn_result = continuous_learner.add_feedback(
        features=feature_array,
        confirmed_label="Normal",
        is_normal=True,
        original_confidence=db_alert.risk_score,
        signal_count=1
    )

    # 🛡️ AUDIT: Analyst Rejection
    await log_audit(
        action="REJECT_ALERT",
        target=alert_id,
        tenant_id=tenant_id,
        user_id=getattr(current_user, "uid", None),
        username=getattr(current_user, "username", "unknown"),
        result="SUCCESS",
        message="Alert marked as False Positive (Normal)"
    )
    
    return {
        "status": "rejected",
        "alert_id": alert_id,
        "label": "Normal",
        "learning": learn_result
    }
