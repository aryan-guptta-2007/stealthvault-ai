"""
StealthVault AI - Database Configuration
Async SQLAlchemy setup for PostgreSQL.
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

# Fallback to local SQLite if PostgreSQL URL isn't explicitly provided via environment
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://stealthadmin:stealthpassword@localhost:5432/stealthvault"
)

# Create the async database engine with resilience settings
engine = create_async_engine(
    DATABASE_URL, 
    echo=False, 
    future=True,
    pool_size=50,
    max_overflow=20,
    pool_pre_ping=True,      # 🛡️ Checks connection health before use
    pool_recycle=3600,     # ♻️ Recycles connections every hour to prevent stale links
    connect_args={
        "command_timeout": 5, # 🕰️ Don't hang forever if DB is slow
    }
)

# Create a session factory
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
SessionLocal = AsyncSessionLocal # ⚡ Alias for compatibility across project

Base = declarative_base()

async def get_db():
    """Dependency injection to get DB session in FastAPI endpoints."""
    async with AsyncSessionLocal() as session:
        yield session

async def init_db(retries: int = 5):
    """Initializes the database tables with retry logic (used on startup)."""
    import asyncio
    from sqlalchemy.exc import OperationalError
    
    attempt = 0
    while attempt < retries:
        try:
            async with engine.begin() as conn:
                # Create all tables if they don't exist
                await conn.run_sync(Base.metadata.create_all)
            print("  ✅ PostgreSQL Database Structure — VERIFIED")
            return
        except (OperationalError, Exception) as e:
            attempt += 1
            if attempt >= retries:
                print(f"  ❌ PostgreSQL Failure after {retries} attempts: {e}")
                raise
            wait = 2 ** attempt
            print(f"  ⚠️  DB Connection Failed (Attempt {attempt}/{retries}). Retrying in {wait}s...")
            await asyncio.sleep(wait)

async def persist_soc_results(verdict, story=None, retries: int = 3):
    """
    🔬 CENTRAL PERSISTENCE ENGINE
    Persists the full SOC results to PostgreSQL for auditing and long-term analysis.
    
    Args:
        verdict: The SOCVerdict object containing detection, intelligence, and defense data.
        story: Optional AttackStory object if this packet updated a narrative.
    """
    from app.models.db_models import DBAlert, DBBlockedIP, DBInspectionLog, DBAttackStory, DBIPReputation
    from sqlalchemy.exc import IntegrityError, OperationalError
    from sqlalchemy import select, update
    from app.core.batch_sqla import inspection_batcher
    import asyncio
    from datetime import datetime
    
    attempt = 0
    while attempt < retries:
        async with AsyncSessionLocal() as db:
            try:
                # 1. ALWAYS: Buffer the Inspection Log (Batching for Scale)
                db_log = DBInspectionLog(
                    tenant_id=verdict.detection.packet.tenant_id,
                    timestamp=verdict.detection.packet.timestamp or datetime.utcnow(),
                    src_ip=verdict.detection.packet.src_ip,
                    dst_ip=verdict.detection.packet.dst_ip,
                    src_port=verdict.detection.packet.src_port,
                    dst_port=verdict.detection.packet.dst_port,
                    protocol=verdict.detection.packet.protocol.value,
                    risk_score=verdict.detection.risk.score,
                    is_threat=verdict.detection.is_threat,
                    attack_type=verdict.detection.classification.attack_type.value,
                    processing_time_ms=verdict.processing_time_ms,
                    decision_details={
                        "anomaly": verdict.detection.anomaly.model_dump(mode="json"),
                        "classification": verdict.detection.classification.model_dump(mode="json"),
                        "risk": verdict.detection.risk.model_dump(mode="json"),
                        "signal_count": verdict.detection.signal_count
                    }
                )
                await inspection_batcher.add(db_log)

                # 2. IF THREAT: Store as Alert
                if verdict.detection.is_threat:
                    db_alert = DBAlert(
                        tenant_id=verdict.detection.packet.tenant_id,
                        timestamp=verdict.detection.packet.timestamp or datetime.utcnow(),
                        src_ip=verdict.detection.packet.src_ip,
                        dst_ip=verdict.detection.packet.dst_ip,
                        attack_type=verdict.detection.classification.attack_type.value,
                        risk_score=verdict.detection.risk.score,
                        severity=verdict.detection.risk.severity.value,
                        packet_data=verdict.detection.packet.model_dump(mode="json"),
                        anomaly_data=verdict.detection.anomaly.model_dump(mode="json"),
                        classification_data=verdict.detection.classification.model_dump(mode="json"),
                        risk_data=verdict.detection.risk.model_dump(mode="json"),
                        brain_analysis=verdict.intelligence.brain_analysis.model_dump(mode="json") if verdict.intelligence and verdict.intelligence.brain_analysis else None
                    )
                    db.add(db_alert)
                
                # 3. DEFENSE ACTION: Store if occurred
                if verdict.defense_action and verdict.defense_action.success:
                    db_block = DBBlockedIP(
                        tenant_id=verdict.detection.packet.tenant_id,
                        ip_address=verdict.detection.packet.src_ip,
                        reason=verdict.defense_action.reason,
                        expires_at=datetime.fromtimestamp(verdict.defense_action.timestamp + 3600) # Default 1h if not specified
                    )
                    db.add(db_block)

                # 4. STORY SYNC: Update the Attack Narrative
                if story:
                    # Using attacker_ip + tenant_id as primary key
                    story_stmt = select(DBAttackStory).where(
                        DBAttackStory.attacker_ip == story.attacker_ip,
                        DBAttackStory.tenant_id == verdict.detection.packet.tenant_id
                    )
                    res = await db.execute(story_stmt)
                    db_story = res.scalars().first()
                    
                    if not db_story:
                        db_story = DBAttackStory(
                            attacker_ip=story.attacker_ip,
                            tenant_id=verdict.detection.packet.tenant_id
                        )
                        db.add(db_story)
                    
                    db_story.target_ip = story.target_ip
                    db_story.last_update = datetime.utcnow()
                    db_story.status = "active" if story.is_active else "closed"
                    db_story.current_phase = story.phases[-1].phase_name if story.phases else "unknown"
                    db_story.confidence = story.phases[-1].prediction_confidence if story.phases and story.phases[-1].is_predicted else 0.0
                    db_story.audit_story_data = story.to_dict()

                # 5. REPUTATION SYNC: Persist long-term behavioral profile
                from app.decision.ip_reputation import ip_reputation_engine
                ip_profile = await ip_reputation_engine.get_profile(
                    verdict.detection.packet.src_ip, 
                    verdict.detection.packet.tenant_id
                )
                
                rep_stmt = select(DBIPReputation).where(
                    DBIPReputation.ip_address == verdict.detection.packet.src_ip,
                    DBIPReputation.tenant_id == verdict.detection.packet.tenant_id
                )
                res_rep = await db.execute(rep_stmt)
                db_rep = res_rep.scalars().first()
                
                if not db_rep:
                    db_rep = DBIPReputation(
                        ip_address=verdict.detection.packet.src_ip,
                        tenant_id=verdict.detection.packet.tenant_id,
                        first_seen=datetime.fromisoformat(ip_profile["first_seen"])
                    )
                    db.add(db_rep)
                    
                db_rep.reputation_score = ip_profile["historical_risk_multiplier"]
                db_rep.total_alerts = ip_profile["total_threats"]
                db_rep.last_seen = datetime.utcnow()
                db_rep.behavior_profile = ip_profile # Store full JSON metadata

                await db.commit()
                return # SUCCESS
            except IntegrityError:
                await db.rollback()
                return # Don't retry on constraint violations
            except OperationalError as e:
                attempt += 1
                await db.rollback()
                if attempt < retries:
                    await asyncio.sleep(2 ** attempt)
                else:
                    print(f"❌ DB Persistence Failed: {e}")
            except Exception as e:
                await db.rollback()
                print(f"❌ Unexpected Persistence Error: {e}")
                return
        attempt += 1

async def persist_system_event(level: str, component: str, message: str, tenant_id: str = "default", stack_trace: str = None, metadata: dict = None):
    """
    🩺 LOG SYSTEM EVENTS
    Persists internal events (INFO/WARNING/ERROR) to the database for observability.
    Runs as a background task to avoid blocking the main SOC pipeline.
    """
    from app.models.db_models import DBSystemEvent
    from datetime import datetime
    
    from app.core.batch_sqla import system_event_batcher
    
    try:
        event = DBSystemEvent(
            tenant_id=tenant_id,
            level=level,
            component=component,
            message=message,
            stack_trace=stack_trace,
            metadata_json=metadata
        )
        await system_event_batcher.add(event)
    except Exception as e:
        print(f"⚠️ Failed to buffer system event: {e}")

def log_event(level: str, component: str, message: str, tenant_id: str = "default", stack_trace: str = None, metadata: dict = None):
    """
    Convenience wrapper to log an event asynchronously.
    """
    import asyncio
    asyncio.create_task(persist_system_event(level, component, message, tenant_id, stack_trace, metadata))
