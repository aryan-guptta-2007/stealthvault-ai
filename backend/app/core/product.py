from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.db_models import DBTenant
from app.core.logger import logger

class QuotaGuard:
    """
    💰 QuotaGuard: SaaS Usage Enforcement Layer
    Ensures that tenants stay within their tier-based packet limits.
    """
    
    @staticmethod
    async def check_quota(tenant_id: str, db: AsyncSession) -> Tuple[bool, Optional[str]]:
        """
        Check if a tenant is allowed to process a packet.
        Returns: (is_allowed, reason_if_denied)
        """
        # Optimized lookup for multi-tenant throughput
        result = await db.execute(select(DBTenant).where(DBTenant.id == tenant_id))
        tenant = result.scalars().first()
        
        if not tenant:
            return False, "Tenant not found"
            
        if not tenant.is_active:
            return False, "Account suspended"
            
        if tenant.current_usage_count >= tenant.monthly_packet_limit:
            return False, f"Monthly quota exceeded for {tenant.plan} tier ({tenant.monthly_packet_limit} packets)"
            
        return True, None

    @staticmethod
    async def increment_usage(tenant_id: str, db: AsyncSession, count: int = 1):
        """Update the usage counter for a tenant."""
        try:
            # We use a direct update for performance if possible, or object update
            result = await db.execute(select(DBTenant).where(DBTenant.id == tenant_id))
            tenant = result.scalars().first()
            if tenant:
                tenant.current_usage_count += count
                # Note: Commit is handled by the orchestrator batcher
        except Exception as e:
            logger.error(f"Quota increment failed for {tenant_id}: {e}")

class PricingEngine:
    """Utility for tier-based logic."""
    
    PLANS = {
        "FREE": {
            "limit": 100000,
            "features": ["basic_soc", "email_alerts"],
            "retention_days": 7
        },
        "PRO": {
            "limit": 5000000,
            "features": ["advanced_xai", "slack_alerts", "api_access"],
            "retention_days": 30
        },
        "ENTERPRISE": {
            "limit": 100000000,
            "features": ["custom_xai", "audit_export", "iam_isolation"],
            "retention_days": 365
        }
    }
    
    @staticmethod
    def get_plan_details(plan_name: str) -> dict:
        return PricingEngine.PLANS.get(plan_name.upper(), PricingEngine.PLANS["FREE"])
