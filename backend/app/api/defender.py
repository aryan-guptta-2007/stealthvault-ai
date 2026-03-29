from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List
from app.agents.defender import defender_agent
from app.api.auth import get_current_user
from app.api.rbac import RoleChecker

# RBAC Instances
admin_only = Depends(RoleChecker(["admin"]))
soc_access = Depends(RoleChecker(["admin", "soc_analyst"]))

router = APIRouter(tags=["Defender"])

@router.get("/status")
async def get_defender_status(user: dict = Depends(get_current_user)):
    """Get the current operational status of the Defender Agent."""
    tenant_id = user.get("tenant_id", "default")
    return defender_agent.get_stats(tenant_id)


@router.get("/blocks/active")
async def get_active_blocks(user: dict = Depends(get_current_user)):
    """Retrieve detailed list of currently blocked IPs for the tenant."""
    tenant_id = user.get("tenant_id", "default")
    from app.database import AsyncSessionLocal
    from app.models.db_models import DBBlockedIP
    from sqlalchemy import select, desc
    
    async with AsyncSessionLocal() as db:
        stmt = select(DBBlockedIP).where(DBBlockedIP.tenant_id == tenant_id).order_by(desc(DBBlockedIP.block_timestamp)).limit(50)
        res = await db.execute(stmt)
        blocks = res.scalars().all()
        
        return [
            {
                "ip": b.ip_address,
                "timestamp": b.block_timestamp.isoformat(),
                "reason": b.reason,
                "expires_at": b.expires_at.isoformat() if b.expires_at else None,
                "risk": b.risk_score,
                "confidence": b.confidence,
                "attack_type": b.attack_type,
                "auto": b.auto_blocked
            }
            for b in blocks
        ]

@router.post("/blocks/clear")
async def clear_all_blocks(user: dict = admin_only):
    """🚨 EMERGENCY: Remove all active firewall blocks immediately."""
    tenant_id = user.get("tenant_id", "default")
    try:
        count = defender_agent.clear_all_blocks(tenant_id)
        return {
            "status": "success",
            "message": f"Emergency clear triggered. {count} rules removed.",
            "count": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mode/emergency-brake")
async def emergency_brake(user: dict = admin_only):
    """🚨 THE BIG RED BUTTON: Disarm agent and flush all rules."""
    tenant_id = user.get("tenant_id", "default")
    defender_agent.disarm(tenant_id)
    count = defender_agent.clear_all_blocks(tenant_id)
    return {
        "status": "EMERGENCY_VENTED",
        "message": f"Defender disarmed. {count} rules purged for tenant {tenant_id}."
    }


@router.post("/blocks/unblock/{ip}")
async def unblock_ip(ip: str, user: dict = admin_only):
    """Manually release a specific IP address from the blocklist."""
    tenant_id = user.get("tenant_id", "default")
    try:
        action = defender_agent.unblock(ip, tenant_id)
        return {
            "status": "success" if action.success else "failed",
            "action": action.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mode/arm")
async def arm_defender(user: dict = admin_only):
    """ARM the defender: Autonomous blocking will be ACTIVE (DANGEROUS)."""
    tenant_id = user.get("tenant_id", "default")
    return defender_agent.arm(tenant_id)

@router.post("/mode/disarm")
async def disarm_defender(user: dict = admin_only):
    """DISARM the defender: Switch to Shadow Mode (SAFE)."""
    tenant_id = user.get("tenant_id", "default")
    return defender_agent.disarm(tenant_id)
