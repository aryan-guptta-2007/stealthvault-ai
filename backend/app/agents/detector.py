"""
╔═══════════════════════════════════════════════════════════╗
║            AGENT 1: DETECTOR — The Eyes                   ║
║  Detects anomalies and classifies attacks.                ║
║  Sees everything. Misses nothing.                         ║
╚═══════════════════════════════════════════════════════════╝

Role in the AI SOC Team:
    Detector → [Analyst] → [Defender]
    
This agent wraps the anomaly detector + classifier into a single
decision unit that produces a unified, distributed threat assessment.
"""

import time
import asyncio
import redis.asyncio as redis
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field

from app.models.alert import (
    NetworkPacket,
    AnomalyResult,
    ClassificationResult,
    RiskScore,
    AttackType,
    Severity,
)
from app.database import log_event
from app.collector.extractor import extractor
from app.ai_engine.anomaly import anomaly_detector
from app.ai_engine.classifier import attack_classifier
from app.decision.risk_scorer import risk_scorer
from app.decision.ip_reputation import ip_reputation_engine


@dataclass
class DetectionVerdict:
    """Output of the Detector Agent — a unified threat assessment."""
    packet: NetworkPacket
    features: any  # numpy array
    anomaly: AnomalyResult
    classification: ClassificationResult
    risk: RiskScore
    timestamp: float = field(default_factory=time.time)
    
    # Multi-signal confidence scoring
    signal_count: int = 0          # How many signals agree this is a threat
    combined_confidence: float = 0.0  # Weighted confidence across all signals
    
    # 🛡️ Defender Safety Lock
    is_repeat_offender: bool = False
    
    @property
    def is_threat(self) -> bool:
        return self.risk.severity in [Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
    
    @property
    def is_critical(self) -> bool:
        return self.risk.severity == Severity.CRITICAL
    
    @property
    def needs_defense(self) -> bool:
        """Should Agent 3 (Defender) take autonomous action?"""
        return (
            self.risk.score >= 0.85
            and self.combined_confidence >= 0.85
            and self.is_repeat_offender
        )


class DetectorAgent:
    """
    🧠 Agent 1: The Detector
    
    Responsibilities:
    - Extract features from raw packets
    - Run anomaly detection (Isolation Forest)
    - Run attack classification (Random Forest)
    - Compute risk score
    - Consolidate Distributed Behaviors
    - Cap Risk based on Signal Consensus
    """
    
    def __init__(self):
        self.total_inspected: int = 0
        self.total_threats: int = 0
        self.total_escalated: int = 0
        # ⚡ Resilient Redis client for sync requests
        self.redis = redis.Redis(
            host='localhost', 
            port=6379, 
            db=0, 
            decode_responses=True,
            retry_on_timeout=True,
            socket_keepalive=True,
            socket_connect_timeout=5
        )
    
    def _ensure_models_loaded(self):
        if not anomaly_detector.is_trained:
            anomaly_detector.load()
        if not attack_classifier.is_trained:
            attack_classifier.load()

    async def inspect(self, packet: NetworkPacket) -> DetectionVerdict:
        """
        Full inspection pipeline for a single packet.
        Returns a DetectionVerdict with multi-signal confidence.
        """
        self._ensure_models_loaded()
        self.total_inspected += 1
        now = time.time()
        
        try:
            # Step 1: Feature extraction
            features = extractor.extract(packet)
            feature_array = extractor.to_numpy(features)
            
            # Step 2: Anomaly detection
            anomaly = anomaly_detector.predict(feature_array)
            
            # Step 3: Attack classification
            classification = attack_classifier.predict(feature_array)
        except Exception as e:
            log_event("ERROR", "DetectorAgent", f"Inspection failed for {packet.src_ip}: {e}", stack_trace=str(e))
            # Safe fallback: Treat as normal but log the failure
            anomaly = AnomalyResult(is_anomaly=False, confidence=1.0, reason="System Error fallback")
            classification = ClassificationResult(attack_type=AttackType.NORMAL, confidence=1.0)
            risk = RiskScore(score=0.0, severity=Severity.LOW)
            return DetectionVerdict(packet, None, anomaly, classification, risk)
        
        # Step 4: Distributed Multi-signal analysis & State
        signal_count = 0
        confidence_sum = 0.0
        
        # Signal 1: ML Anomaly says it's abnormal
        if anomaly.is_anomaly:
            signal_count += 1
            confidence_sum += min(anomaly.anomaly_score, 1.0)
        
        # Signal 2: ML Classifier says it's an attack
        if classification.attack_type not in [AttackType.NORMAL, AttackType.UNKNOWN]:
            signal_count += 1
            confidence_sum += classification.confidence
            
        # Signal 3 & 4: Distributed Temporal IP State per Tenant
        src_ip = packet.src_ip
        tenant_id = getattr(packet, "tenant_id", "default")
        
        # Step 4: Stateful behavior (Port Scanning / Brute Force)
        signal_count = 1 if anomaly.is_anomaly else 0
        confidence_sum = anomaly.confidence if anomaly.is_anomaly else 0.0
        
        try:
            # Track IP reputation in Redis
            scan_key = f"scan:{packet.tenant_id}:{packet.src_ip}"
            await self._update_ip_reputation(scan_key, packet.dst_port)
            
            unique_ports = await self.redis.scard(scan_key)
            if unique_ports > 15: # Stealth Scans touch many unique ports
                signal_count += 1
                confidence_sum += 0.90
        except Exception as e:
            log_event("WARNING", "DetectorAgent", f"Redis Reputation Check Failed: {e}")
            unique_ports = 0
        
        # Signal 5: Known Suspicious High-Value Port targeting
        suspicious_ports = {23, 445, 3389, 4444, 5900, 8080, 1433, 3306}
        if packet.dst_port in suspicious_ports:
            signal_count += 1
            confidence_sum += 0.6
            
        # 🧠 Signal 6: Historical Stateful Intelligence (IP Profile)
        ip_profile = await ip_reputation_engine.get_profile(src_ip, tenant_id)
        
        # 🧪 Multi-signal Behavioral Analysis
        if ip_profile["kill_chain_max_phase"] >= 4:
            # Attacker has reached exploit stage before
            signal_count += 2
            confidence_sum += 1.8
        elif ip_profile["total_threats"] >= 2:
            signal_count += 1
            confidence_sum += 0.95
            
        if "Aggressive" in ip_profile["behavioral_tags"]:
            signal_count += 1
            confidence_sum += 0.7
            
        if ip_profile["dwell_time_seconds"] < 60:
            # Very new IP (Novelty Penalty)
            signal_count += 1
            confidence_sum += 0.4
        
        combined_confidence = confidence_sum / max(signal_count, 1)
        
        # Step 5: Master Risk Scoring (Now capped by signal consensus + historical multiplier)
        risk = risk_scorer.score(
            anomaly, 
            classification, 
            signal_count, 
            historical_risk_multiplier=ip_profile["historical_risk_multiplier"]
        )
        
        if packet_count > 50 and "VOLATILITY_SPIKE" not in risk.behavior_flags:
            risk.behavior_flags.append("VOLATILITY_SPIKE")
        if unique_ports > 15 and "STEALTH_PORT_SCAN" not in risk.behavior_flags:
            risk.behavior_flags.append("STEALTH_PORT_SCAN")
        if ip_profile["total_threats"] >= 2 and "REPEAT_OFFENDER" not in risk.behavior_flags:
            risk.behavior_flags.append("REPEAT_OFFENDER")
            
        verdict = DetectionVerdict(
            packet=packet,
            features=feature_array,
            anomaly=anomaly,
            classification=classification,
            risk=risk,
            signal_count=signal_count,
            combined_confidence=round(combined_confidence, 4),
            is_repeat_offender=(ip_profile["total_threats"] >= 2),
        )
        
        if verdict.is_threat:
            self.total_threats += 1
        
        if verdict.needs_defense:
            self.total_escalated += 1
        
        return verdict
    
    def get_stats(self) -> dict:
        return {
            "agent": "Detector",
            "role": "Eyes of the SOC",
            "total_inspected": self.total_inspected,
            "total_threats": self.total_threats,
            "total_escalated_to_defender": self.total_escalated,
            "threat_rate": round(self.total_threats / max(self.total_inspected, 1), 4),
        }

# Singleton
detector_agent = DetectorAgent()
