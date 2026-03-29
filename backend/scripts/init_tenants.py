import asyncio
import argparse
from sqlalchemy.future import select

# To run this script locally without starting the whole app:
# set PYTHONPATH to the project backend dir and run:
# python scripts/init_tenants.py

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import AsyncSessionLocal, init_db, engine, Base
from app.models.db_models import DBTenant, DBUser

async def seed_tenants(drop_tables: bool = False):
    print(f"🌱 Initializing PostgreSQL database schema (drop={drop_tables})...")
    
    if drop_tables:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            
    await init_db()

    async with AsyncSessionLocal() as db:
        print("\n🔍 Checking for existing tenants...")
        
        # Check Default Tenant
        result = await db.execute(select(DBTenant).where(DBTenant.id == "default"))
        default_tenant = result.scalars().first()
        
        if not default_tenant:
            print("  ➕ Creating Default Tenant (STARTUP-TIER)...")
            default_tenant = DBTenant(
                id="default",
                name="StealthVault Local HQ",
                api_key="sv_local_dev_key"
            )
            db.add(default_tenant)

        # Check Demo SaaS Tenant
        result = await db.execute(select(DBTenant).where(DBTenant.id == "acme-corp"))
        acme_tenant = result.scalars().first()
        
        if not acme_tenant:
            print("  ➕ Creating Demo SaaS Tenant 'Acme Corp' (ENTERPRISE-TIER)...")
            acme_tenant = DBTenant(
                id="acme-corp",
                name="Acme Corporation Security",
                api_key="sv_acme_enterprise_key"
            )
            db.add(acme_tenant)

        # Ensure Admin User exists for default tenant
        result = await db.execute(select(DBUser).where(DBUser.username == "admin"))
        admin_user = result.scalars().first()
        
        if not admin_user:
            print("  ➕ Creating Admin User (default tenant)...")
            admin_user = DBUser(
                username="admin",
                password_hash="admin", # Keep simple for MVP
                tenant_id="default",
                roles=["admin"]
            )
            db.add(admin_user)

        # Ensure Client User exists for acme tenant
        result = await db.execute(select(DBUser).where(DBUser.username == "acme-admin"))
        acme_admin = result.scalars().first()
        
        if not acme_admin:
            print("  ➕ Creating Acme Admin User (acme-corp tenant)...")
            acme_admin = DBUser(
                username="acme-admin",
                password_hash="acme123", # Keep simple for MVP
                tenant_id="acme-corp",
                roles=["admin"]
            )
            db.add(acme_admin)

        await db.commit()
        print("\n✅ Database Seeding Complete!")
        print("\n🔑 Quick Reference:")
        print("  Default UI Login: admin / admin")
        print("  Default API Key:  sv_local_dev_key")
        print("  Acme UI Login:    acme-admin / acme123")
        print("  Acme API Key:     sv_acme_enterprise_key\n")

if __name__ == "__main__":
    import sys
    drop = "--drop" in sys.argv
    asyncio.run(seed_tenants(drop_tables=drop))
