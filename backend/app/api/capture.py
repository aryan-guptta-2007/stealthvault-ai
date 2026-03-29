"""
StealthVault AI - Capture Control API
Endpoints for live network capture and continuous learning.
"""

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import asyncio
import threading

from app.collector.sniffer import live_sniffer, SCAPY_AVAILABLE
from app.collector.stream import stream_processor
from app.ai_engine.learner import continuous_learner
from app.models.alert import AttackType
from fastapi import Depends, Request
from app.api.auth import get_current_user, get_optional_user
from app.core.limiter import limiter

router = APIRouter(prefix="/capture", tags=["Live Capture"])


class CaptureRequest(BaseModel):
    """Request to start live capture."""
    interface: Optional[str] = None
    count: int = 0  # 0 = infinite
    timeout: Optional[int] = 60
    bpf_filter: Optional[str] = None


class FeedbackRequest(BaseModel):
    """Analyst feedback on an alert."""
    alert_id: str
    confirmed_label: str  # AttackType value
    is_false_positive: bool = False
    notes: str = ""


@router.get("/status")
@limiter.limit("60/minute")
async def capture_status(request: Request, current_user: object | None = Depends(get_optional_user)):
    """Get current capture and processing status."""
    return {
        "scapy_available": SCAPY_AVAILABLE,
        "sniffer": live_sniffer.get_stats(),
        "processor": stream_processor.get_stats(),
        "learner": continuous_learner.get_status(),
    }


@router.post("/start")
@limiter.limit("10/minute")
async def start_capture(request: Request, payload: CaptureRequest, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    """
    🔍 Start live network packet capture.
    
    ⚠️ Requires Npcap + admin privileges on Windows.
    """
    if not SCAPY_AVAILABLE:
        return {
            "error": "Scapy is not installed",
            "fix": "pip install scapy",
            "also": "Install Npcap from https://npcap.com",
        }

    if live_sniffer.is_running:
        return {"error": "Capture already running", "stats": live_sniffer.get_stats()}

    # Start stream processor if not running
    if not stream_processor.is_running:
        asyncio.create_task(stream_processor.start())

    # Start capture in background thread
    def run_capture():
        live_sniffer.start_capture(
            interface=payload.interface,
            count=payload.count,
            timeout=payload.timeout,
            bpf_filter=payload.bpf_filter,
            queue=stream_processor.queue,
        )

    thread = threading.Thread(target=run_capture, daemon=True)
    thread.start()

    return {
        "status": "capture_started",
        "config": payload.model_dump(),
        "message": "Live capture started. Check /capture/status for updates.",
    }


@router.post("/stop")
@limiter.limit("10/minute")
async def stop_capture(request: Request, current_user: dict = Depends(get_current_user)):
    """Stop live capture."""
    live_sniffer.stop()
    return {
        "status": "capture_stopped",
        "stats": live_sniffer.get_stats(),
    }


@router.post("/feedback")
@limiter.limit("60/minute")
async def submit_feedback(request: Request, payload: FeedbackRequest, current_user: dict = Depends(get_current_user)):
    """
    🧠 Submit analyst feedback for continuous learning.
    
    When you confirm or correct an alert's classification,
    the AI models learn from your feedback and improve over time.
    """
    # Find the alert in stream processor's store
    alert = None
    for a in stream_processor.alert_store:
        if a.id == payload.alert_id:
            alert = a
            break

    # Also check the traffic API store
    if not alert:
        from app.api.traffic import alert_store
        for a in alert_store:
            if a.id == payload.alert_id:
                alert = a
                break

    if not alert:
        return {"error": "Alert not found", "alert_id": payload.alert_id}

    # Extract features from the alert's packet
    from app.collector.extractor import extractor
    features = extractor.extract(alert.packet)
    feature_array = extractor.to_numpy(features)

    # Determine the label
    if payload.is_false_positive:
        confirmed_label = AttackType.NORMAL.value
    else:
        confirmed_label = payload.confirmed_label

    # Submit to continuous learner
    result = continuous_learner.add_feedback(
        features=feature_array,
        confirmed_label=confirmed_label,
        is_normal=(confirmed_label == AttackType.NORMAL.value),
    )

    # 📉 PERSIST FEEDBACK TO DB
    try:
        from app.database import AsyncSessionLocal
        from app.models.db_models import DBAlert
        from sqlalchemy import update
        
        async def update_db_feedback():
            async with AsyncSessionLocal() as db:
                stmt = (
                    update(DBAlert)
                    .where(DBAlert.id == payload.alert_id)
                    .values(feedback_label=confirmed_label, is_correct=(confirmed_label == alert.attack_type))
                )
                await db.execute(stmt)
                await db.commit()
        
        asyncio.create_task(update_db_feedback())
    except Exception as e:
        print(f"⚠️ Failed to persist feedback to DB: {e}")

    return {
        "status": "feedback_accepted",
        "confirmed_label": confirmed_label,
        "learning": result,
    }


@router.post("/retrain")
@limiter.limit("5/minute")
async def force_retrain(request: Request, current_user: dict = Depends(get_current_user)):
    """Force an immediate model retrain with accumulated feedback."""
    if len(continuous_learner.labeled_features) == 0:
        return {"error": "No feedback data to retrain with"}

    result = continuous_learner.retrain()
    return result


@router.get("/learning/status")
@limiter.limit("60/minute")
async def learning_status(request: Request, current_user: object | None = Depends(get_optional_user)):
    """Get continuous learning details."""
    return continuous_learner.get_status()


@router.get("/metrics")
@limiter.limit("60/minute")
async def get_model_metrics(request: Request, current_user: object | None = Depends(get_optional_user)):
    """
    📈 PERFORMANCE TELEMETRY
    Returns historical accuracy/precision data for Model Health dashboard.
    """
    from app.database import AsyncSessionLocal
    from app.models.db_models import DBModelMetric
    from sqlalchemy import select, desc
    
    async with AsyncSessionLocal() as db:
        stmt = select(DBModelMetric).order_by(desc(DBModelMetric.timestamp)).limit(20)
        res = await db.execute(stmt)
        metrics = res.scalars().all()
        
        return [
            {
                "version": m.version,
                "timestamp": m.timestamp.isoformat(),
                "accuracy": m.accuracy,
                "precision": m.precision,
                "recall": m.recall,
                "f1": m.f1_score,
                "samples": m.total_samples
            }
            for m in metrics
        ]
