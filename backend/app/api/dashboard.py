"""
StealthVault AI - Dashboard API
Aggregated statistics endpoint for the dashboard UI.
"""

from collections import Counter
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.database import get_db
from app.models.db_models import DBAlert
from app.models.alert import DashboardStats, Severity
from app.api.auth import get_current_user, get_optional_user
from app.api.traffic import packet_count
from app.core.limiter import limiter
from fastapi import Request
from app.api.traffic import packet_count

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/", response_model=DashboardStats)
@limiter.limit("60/minute")
async def get_dashboard(request: Request, current_user: object | None = Depends(get_optional_user), db: AsyncSession = Depends(get_db)):
    """Get aggregated dashboard statistics scoped by tenant from PostgreSQL. Anonymized if public."""
    tenant_id = getattr(current_user, "tenant_id", "default") if current_user else "default"
    is_public = current_user is None
    
    # Total Alerts
    total_result = await db.execute(select(func.count(DBAlert.id)).where(DBAlert.tenant_id == tenant_id))
    total_alerts = total_result.scalar() or 0
    
    # Counts by severity
    sev_result = await db.execute(
        select(DBAlert.severity, func.count(DBAlert.id))
        .where(DBAlert.tenant_id == tenant_id)
        .group_by(DBAlert.severity)
    )
    sev_counts = {row[0]: row[1] for row in sev_result.all()}
    
    critical = sev_counts.get(Severity.CRITICAL.value, 0)
    high = sev_counts.get(Severity.HIGH.value, 0)
    medium = sev_counts.get(Severity.MEDIUM.value, 0)
    low = sev_counts.get(Severity.LOW.value, 0)

    # Attack type distribution
    attack_result = await db.execute(
        select(DBAlert.attack_type, func.count(DBAlert.id))
        .where(DBAlert.tenant_id == tenant_id)
        .group_by(DBAlert.attack_type)
        .order_by(func.count(DBAlert.id).desc())
        .limit(10)
    )
    attack_distribution = {row[0]: row[1] for row in attack_result.all()}

    # Average risk score
    risk_result = await db.execute(
        select(func.avg(DBAlert.risk_score))
        .where(DBAlert.tenant_id == tenant_id)
    )
    avg_risk = risk_result.scalar() or 0.0

    # Top attackers (by source IP frequency)
    ip_result = await db.execute(
        select(DBAlert.src_ip, func.count(DBAlert.id))
        .where(DBAlert.tenant_id == tenant_id)
        .group_by(DBAlert.src_ip)
        .order_by(func.count(DBAlert.id).desc())
        .limit(10)
    )
    
    top_attackers = []
    for row in ip_result.all():
        ip = row[0]
        if is_public and ip:
            parts = ip.split('.')
            if len(parts) == 4:
                ip = f"{parts[0]}.{parts[1]}.x.x"
        top_attackers.append({"ip": ip, "count": row[1], "severity": "high"})

    return DashboardStats(
        total_packets_analyzed=total_alerts * 5, # Extrapolate packets for tenant
        total_alerts=total_alerts,
        critical_alerts=critical,
        high_alerts=high,
        medium_alerts=medium,
        low_alerts=low,
        attack_distribution=attack_distribution,
        avg_risk_score=round(avg_risk, 4),
        top_attackers=top_attackers,
        packets_per_minute=0.0,  # Will be calculated with real-time tracking
        system_status="ACTIVE" if packet_count > 0 else "IDLE",
    )
