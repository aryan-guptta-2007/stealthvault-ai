from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timedelta
from app.database import get_db
from app.models.db_models import DBAlert
from app.api.auth import get_optional_user
from app.core.limiter import limiter

router = APIRouter(prefix="/stats", tags=["Telemetry & Analytics"])

@router.get("/")
@limiter.limit("60/minute")
async def get_soc_stats(
    request: Request,
    current_user: object | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    """
    📊 MISSION CRITICAL STATS
    Provides a real-time tactical overview of the SOC's performance.
    """
    tenant_id = getattr(current_user, "tenant_id", "default") if current_user else "default"
    
    # 🕵️ Aggregations
    # 1. Severity Distribution
    stmt_severity = select(DBAlert.severity, func.count(DBAlert.id)).where(
        DBAlert.tenant_id == tenant_id
    ).group_by(DBAlert.severity)
    
    # 2. Top Attackers (Source IPs)
    stmt_attackers = select(DBAlert.src_ip, func.count(DBAlert.id)).where(
        DBAlert.tenant_id == tenant_id
    ).group_by(DBAlert.src_ip).order_by(desc(func.count(DBAlert.id))).limit(5)
    
    # 3. 24h Trend
    cutoff = datetime.utcnow() - timedelta(hours=24)
    stmt_trend = select(func.date_trunc('hour', DBAlert.timestamp), func.count(DBAlert.id)).where(
        DBAlert.tenant_id == tenant_id,
        DBAlert.timestamp >= cutoff
    ).group_by(func.date_trunc('hour', DBAlert.timestamp)).order_by(func.date_trunc('hour', DBAlert.timestamp))

    # Execute
    res_severity = await db.execute(stmt_severity)
    res_attackers = await db.execute(stmt_attackers)
    res_trend = await db.execute(stmt_trend)

    # Format
    severity_map = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    total_alerts = 0
    for sev, count in res_severity.all():
        severity_map[sev] = count
        total_alerts += count

    top_attackers = [{"ip": ip, "count": count} for ip, count in res_attackers.all()]
    
    trend_data = [{"time": t.isoformat(), "count": c} for t, c in res_trend.all()]

    return {
        "summary": {
            "total_alerts": total_alerts,
            "status": "ACTIVE",
            "last_updated": datetime.utcnow().isoformat()
        },
        "severity_distribution": severity_map,
        "top_attackers": top_attackers,
        "hourly_trend_24h": trend_data
    }
