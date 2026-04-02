from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.db_models import DBAlert

router = APIRouter(prefix="/stats", tags=["Telemetry & Analytics"])

@router.get("/")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """
    📊 MISSION CRITICAL STATS - SIMPLIFIED
    Provides a real-time tactical overview of alert counts by severity.
    """
    try:
        # 1. Total Alerts
        stmt_total = select(func.count(DBAlert.id))
        res_total = await db.execute(stmt_total)
        total_alerts = res_total.scalar() or 0

        # 2. Severity Counts
        async def get_sev_count(sev: str):
            stmt = select(func.count(DBAlert.id)).where(DBAlert.severity == sev)
            res = await db.execute(stmt)
            return res.scalar() or 0

        critical = await get_sev_count("critical")
        high = await get_sev_count("high")
        medium = await get_sev_count("medium")
        low = await get_sev_count("low")

        return {
            "total_alerts": total_alerts,
            "critical": critical,
            "high": high,
            "medium": medium,
            "low": low
        }
    except Exception as e:
        from fastapi import HTTPException
        import logging
        logging.error(f"Tactical Telemetry Fault: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Tactical analytics engine currently unavailable."
        )
