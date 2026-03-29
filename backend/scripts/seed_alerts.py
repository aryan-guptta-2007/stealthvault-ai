import asyncio
import uuid
from datetime import datetime
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.db_models import DBAlert, DBTenant

async def seed_alerts():
    print("🚀 Seeding manual alerts for multi-tenant verification...")
    async with AsyncSessionLocal() as db:
        # 1. Ensure tenants exist
        res = await db.execute(select(DBTenant).where(DBTenant.id == "default"))
        if not res.scalars().first():
            print("❌ Default tenant missing. Run init_tenants.py first.")
            return
            
        res = await db.execute(select(DBTenant).where(DBTenant.id == "acme-corp"))
        if not res.scalars().first():
            print("❌ Acme tenant missing. Run init_tenants.py first.")
            return

        # 2. Insert alert for Default
        alert_default = DBAlert(
            id=str(uuid.uuid4())[:12],
            tenant_id="default",
            timestamp=datetime.utcnow(),
            src_ip="1.2.3.4",
            dst_ip="10.0.0.5",
            attack_type="DDoS",
            risk_score=0.9,
            severity="high",
            packet_data={"protocol": "TCP"},
            anomaly_data={"score": 0.8},
            classification_data={"type": "DDoS"},
            risk_data={"score": 0.9}
        )
        db.add(alert_default)
        
        # 3. Insert 5 alerts for Acme
        for i in range(5):
            alert_acme = DBAlert(
                id=str(uuid.uuid4())[:12],
                tenant_id="acme-corp",
                timestamp=datetime.utcnow(),
                src_ip="192.168.1.99",
                dst_ip="172.16.0.10",
                attack_type="PortScan",
                risk_score=0.7,
                severity="medium",
                packet_data={"protocol": "TCP", "port": i},
                anomaly_data={"score": 0.5},
                classification_data={"type": "PortScan"},
                risk_data={"score": 0.7}
            )
            db.add(alert_acme)
            
        await db.commit()
        print("✅ Seeded: 1 alert for Default, 5 alerts for Acme.")

if __name__ == "__main__":
    asyncio.run(seed_alerts())
