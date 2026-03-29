import logging
from datetime import datetime
from typing import Optional, Any
from app.database import AsyncSessionLocal
from app.models.db_models import DBAuditLog

logger = logging.getLogger("audit")

async def log_audit(
    action: str,
    target: str,
    tenant_id: str,
    user_id: Optional[str] = None,
    username: str = "system",
    result: str = "SUCCESS",
    message: str = "",
    metadata: Optional[dict[str, Any]] = None
):
    """
    📜 Global Audit Logger
    Persists sensitive security actions to the database for forensic review.
    """
    try:
        async with AsyncSessionLocal() as db:
            audit = DBAuditLog(
                user_id=user_id,
                username=username,
                tenant_id=tenant_id,
                action=action,
                target=target,
                result=result,
                message=message,
                metadata_json=metadata or {}
            )
            db.add(audit)
            await db.commit()
            
        # Also log to system logs with [AUDIT] prefix for rapid grep/Splunk/CloudWatch
        log_level = logging.INFO if result == "SUCCESS" else logging.WARNING
        logger.log(log_level, f"[AUDIT] {action} | {username} | {target} | {result} | {message}")
        
    except Exception as e:
        # We don't want to crash the request if auditing fails, but we MUST know.
        logger.error(f"🚨 Audit Logging Failed: {e}")
