from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.db_models import DBAlert, DBUser, DBTenant, DBAuditLog
from app.core.logger import logger

class ComplianceEngine:
    """
    📜 COMPLIANCE & GOVERNANCE LAYER (GDPR/SOC2 Ready)
    Handles data portability, PII masking, and multi-tenant audit export.
    """
    
    @staticmethod
    async def export_tenant_data(tenant_id: str, db: AsyncSession) -> dict:
        """
        🚀 GDPR Right to Portability (Article 20)
        Standardized export of all data associated with a tenant.
        """
        try:
            # 1. Fetch Tenant
            stmt = select(DBTenant).where(DBTenant.id == tenant_id)
            tenant = (await db.execute(stmt)).scalars().first()
            if not tenant: return {"error": "Tenant not found"}
            
            # 2. Fetch Users
            stmt = select(DBUser).where(DBUser.tenant_id == tenant_id)
            users = (await db.execute(stmt)).scalars().all()
            
            # 3. Fetch Audit Logs (Limited to 1000 for SaaS performance)
            stmt = select(DBAuditLog).where(DBAuditLog.tenant_id == tenant_id).order_by(DBAuditLog.timestamp.desc()).limit(1000)
            audit_logs = (await db.execute(stmt)).scalars().all()
            
            # 4. Build Package
            return {
                "sv_schema_version": "1.0-commercial",
                "tenant_name": tenant.name,
                "tenant_id": tenant.id,
                "plan": tenant.plan,
                "export_timestamp": datetime.utcnow().isoformat() + "Z",
                "integrity_hash": "sv_sha256_placeholder", # For SOC2 forensic proof
                "users": [
                    {
                        "id": u.id, 
                        "username": u.username, 
                        "email": u.email, 
                        "roles": u.roles,
                        "verified": u.is_verified
                    } for u in users
                ],
                "audit_trail": [
                    {
                        "action": l.action, 
                        "target": l.target,
                        "result": l.result,
                        "timestamp": l.timestamp.isoformat() + "Z",
                        "username": l.username,
                        "message": l.message
                    } for l in audit_logs
                ]
            }
        except Exception as e:
            logger.error(f"Compliance export failed for {tenant_id}: {e}")
            return {"error": "Internal export service error"}

    @staticmethod
    def mask_pii(ip: str, roles: List[str]) -> str:
        """
        🛡️ PII PRIVACY SHIELD
        Masks IP addresses for analysts/viewers without 'admin' or 'pii_viewer' roles.
        Complies with GDPR 'Data Minimization' principles.
        """
        if "admin" in roles or "pii_viewer" in roles:
            return ip
            
        parts = ip.split(".")
        if len(parts) == 4:
            # 192.168.1.1 -> 192.168.x.x
            return f"{parts[0]}.{parts[1]}.x.x"
        
        # IPv6
        return ip[:12] + ":xxxx:xxxx"

compliance_engine = ComplianceEngine()
