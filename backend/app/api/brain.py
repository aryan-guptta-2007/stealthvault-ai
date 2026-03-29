"""
StealthVault AI - Brain API
Endpoint for the AI Security Brain to explain threats.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from app.models.alert import (
    BrainAnalysis,
    AnomalyResult,
    ClassificationResult,
    RiskScore,
    AttackType,
    Severity,
)
from app.decision.brain import security_brain
from app.api.traffic import alert_store

router = APIRouter(prefix="/brain", tags=["AI Brain"])


class BrainRequest(BaseModel):
    """Request model for AI brain analysis."""
    alert_id: str | None = None
    attack_type: str | None = None


@router.post("/analyze", response_model=BrainAnalysis)
async def analyze_threat(request: BrainRequest):
    """
    🧠 Ask the AI Security Brain to explain a threat.
    
    Either provide an alert_id to analyze an existing alert,
    or an attack_type to get general information about an attack.
    """
    if request.alert_id:
        # Find the alert
        for alert in alert_store:
            if alert.id == request.alert_id:
                return security_brain.analyze(
                    alert.anomaly, alert.classification, alert.risk
                )
        return {"error": "Alert not found"}

    if request.attack_type:
        # General analysis for an attack type
        try:
            attack = AttackType(request.attack_type)
        except ValueError:
            attack = AttackType.UNKNOWN

        # Create mock results for general info
        anomaly = AnomalyResult(is_anomaly=True, anomaly_score=0.8, confidence=0.9)
        classification = ClassificationResult(
            attack_type=attack, confidence=0.9, probabilities={}
        )
        risk = RiskScore(
            score=0.8,
            severity=Severity.HIGH,
            anomaly_contribution=0.4,
            classification_contribution=0.6,
        )
        return security_brain.analyze(anomaly, classification, risk)

    return BrainAnalysis(
        attack_name="No Input",
        description="Please provide either an alert_id or attack_type.",
        danger_level="N/A",
        what_is_happening="No threat data provided.",
        how_to_stop="Provide an alert_id or attack_type to get analysis.",
        technical_details="N/A",
        recommended_actions=["Provide alert_id or attack_type"],
    )


@router.get("/attacks")
async def list_attack_types():
    """List all known attack types the brain can explain."""
    return {
        "attack_types": [
            {"value": at.value, "name": at.name}
            for at in AttackType
        ]
    }
