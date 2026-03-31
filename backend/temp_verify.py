import asyncio
from app.database import AsyncSessionLocal
from app.models.db_models import DBBlockedIP, DBSystemEvent
from sqlalchemy import select, desc

async def verify_simulation():
    async with AsyncSessionLocal() as db:
        # 1. Check Simulator Events
        print("🔍 Checking Simulation Logs...")
        stmt_events = select(DBSystemEvent).where(DBSystemEvent.component == "Simulator").order_by(desc(DBSystemEvent.timestamp)).limit(3)
        res_events = await db.execute(stmt_events)
        events = res_events.scalars().all()
        for e in events:
            print(f" - [{e.timestamp}] {e.level}: {e.message}")
            
        # 2. Check Blocked IPs (Quarantine)
        print("\n🛡️ Checking Active Quarantine...")
        stmt_blocks = select(DBBlockedIP).order_by(desc(DBBlockedIP.block_timestamp)).limit(5)
        res_blocks = await db.execute(stmt_blocks)
        blocks = res_blocks.scalars().all()
        print(f"Total Quarantined: {len(blocks)}")
        for b in blocks:
            print(f" - [{b.block_timestamp}] {b.ip_address}: {b.attack_type} ({b.reason})")

if __name__ == "__main__":
    asyncio.run(verify_simulation())
