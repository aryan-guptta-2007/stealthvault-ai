"""
StealthVault AI - Risk Scoring Engine
Combines anomaly detection + attack classification into a unified risk score.
"""

from app.models.alert import (
    AnomalyResult,
    ClassificationResult,
    RiskScore,
    Severity,
    AttackType,
)
from app.config import settings


# Risk multipliers per attack type
ATTACK_SEVERITY_WEIGHTS = {
    AttackType.NORMAL: 0.0,
    AttackType.DDOS: 0.85,
    AttackType.PORT_SCAN: 0.5,
    AttackType.BRUTE_FORCE: 0.75,
    AttackType.MALWARE: 0.95,
    AttackType.SQL_INJECTION: 0.9,
    AttackType.XSS: 0.7,
    AttackType.UNKNOWN: 0.4,
}


class RiskScorer:
    """
    Combines multiple AI signals into a single risk score.
    
    Formula:
        risk = (anomaly_weight * anomaly_score) + (classification_weight * attack_severity)
        
    Where:
        - anomaly_score comes from the Isolation Forest
        - attack_severity is derived from the classifier's prediction + confidence
    """

    ANOMALY_WEIGHT = 0.4
    CLASSIFICATION_WEIGHT = 0.6

    def score(
        self,
        anomaly: AnomalyResult,
        classification: ClassificationResult,
        signal_count: int = 1,
        historical_risk_multiplier: float = 1.0,
    ) -> RiskScore:
        """
        Calculate the combined risk score.
        
        Args:
            anomaly: Anomaly detection result
            classification: Attack classification result
        
        Returns:
            RiskScore with severity level and breakdown
        """
        # Get base severity for the attack type
        attack_weight = ATTACK_SEVERITY_WEIGHTS.get(
            classification.attack_type, 0.4
        )

        # Anomaly contribution: anomaly_score * confidence
        anomaly_contribution = anomaly.anomaly_score * anomaly.confidence

        # Classification contribution: attack_severity * classifier_confidence
        classification_contribution = attack_weight * classification.confidence

        # Combined risk score
        raw_score = (
            self.ANOMALY_WEIGHT * anomaly_contribution
            + self.CLASSIFICATION_WEIGHT * classification_contribution
        )
        
        # 🧠 STATEFUL INTELLIGENCE: Historical penalty for repeat offenders
        raw_score *= historical_risk_multiplier

        # Clamp to [0, 1]
        risk_score = max(0.0, min(1.0, raw_score))

        # Determine severity
        severity = self._determine_severity(risk_score)

        # Behavior flags
        behavior_flags = self._get_behavior_flags(anomaly, classification)

        # ⚔️ CONSENSUS HARDENING: Caps risks if independent signals are lacking.
        if severity in [Severity.HIGH, Severity.CRITICAL] and signal_count < 2:
            severity = Severity.MEDIUM
            behavior_flags.append("CAPPED_LACK_OF_CONSENSUS")
            risk_score = min(risk_score, settings.RISK_HIGH_THRESHOLD - 0.01)

        return RiskScore(
            score=round(risk_score, 4),
            severity=severity,
            anomaly_contribution=round(anomaly_contribution, 4),
            classification_contribution=round(classification_contribution, 4),
            behavior_flags=behavior_flags,
        )

    def _determine_severity(self, score: float) -> Severity:
        """Map risk score to severity level."""
        if score >= settings.RISK_CRITICAL_THRESHOLD:
            return Severity.CRITICAL
        elif score >= settings.RISK_HIGH_THRESHOLD:
            return Severity.HIGH
        elif score >= settings.RISK_MEDIUM_THRESHOLD:
            return Severity.MEDIUM
        else:
            return Severity.LOW

    def _get_behavior_flags(
        self,
        anomaly: AnomalyResult,
        classification: ClassificationResult,
    ) -> list[str]:
        """Generate human-readable behavior flags."""
        flags = []

        if anomaly.is_anomaly and anomaly.anomaly_score > 0.8:
            flags.append("HIGHLY_ANOMALOUS_TRAFFIC")
        elif anomaly.is_anomaly:
            flags.append("ANOMALOUS_TRAFFIC")

        if classification.attack_type != AttackType.NORMAL:
            flags.append(f"ATTACK_DETECTED:{classification.attack_type.value}")

        if classification.confidence > 0.9:
            flags.append("HIGH_CONFIDENCE_DETECTION")
        elif classification.confidence < 0.3:
            flags.append("LOW_CONFIDENCE_DETECTION")

        if anomaly.is_anomaly and classification.attack_type == AttackType.NORMAL:
            flags.append("POTENTIAL_ZERO_DAY")

        return flags


# Singleton
risk_scorer = RiskScorer()
