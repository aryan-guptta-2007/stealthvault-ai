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
import numpy as np
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
from app.ai_engine.learner import continuous_learner
from app.core.logger import logger


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
    - 🧠 Explainability (XAI): Provide reasoning for model decisions
    - 🛡️ Adversarial Protection: Detect and block model evasion attempts
    """
    
    def __init__(self):
        self.total_inspected: int = 0
        self.total_threats: int = 0
        self.total_escalated: int = 0
        # ⚡ Safe Redis initialization
        self.redis = None
        try:
            import os
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            if redis_url and "none" not in redis_url.lower():
                self.redis = redis.from_url(
                    redis_url, 
                    decode_responses=True,
                    socket_connect_timeout=2
                )
        except Exception:
            self.redis = None
    
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
            
        # --- 🧠 ADVANCED AI HARDENING (XAI & ADVERSARIAL) ---
        # 1. Explainability: Identify Top contributing features
        feature_labels = ["src_port", "dst_port", "size", "payload", "ttl", "duration", "tcp", "udp", "icmp", "http"]
        influential_features = {}
        
        # Simple local feature importance (Distance from mean weighted by global importance)
        # Assuming features are scaled (0-1 approx)
        for i, val in enumerate(feature_array[0][:len(feature_labels)]):
            if abs(val) > 1.5: # 1.5 std dev from normal
                influential_features[feature_labels[i]] = round(abs(val) * 0.2, 4)
        
        # Normalize and set XAI data
        total_inf = sum(influential_features.values()) or 1.0
        classification.feature_contributions = {k: round(v/total_inf, 4) for k, v in influential_features.items()}
        classification.explanation = f"Flagged based on {', '.join(list(influential_features.keys())[:3])} deviation."
        
        # 2. Adversarial Protection: Stochastic Denoising
        adversarial_risk = await self._check_adversarial_risk(feature_array)
        if adversarial_risk > 0.7:
            signal_count += 2
            confidence_sum += adversarial_risk
            classification.explanation += " | ⚠️ Potential Adversarial Evasion detected."
            
        # Signal 3 & 4: Distributed Temporal IP State per Tenant
        src_ip = packet.src_ip
        tenant_id = getattr(packet, "tenant_id", "default")
        
        # Step 4: Stateful behavior (Port Scanning / Brute Force)
        signal_count = 1 if anomaly.is_anomaly else 0
        confidence_sum = anomaly.confidence if anomaly.is_anomaly else 0.0
        
        try:
            # Track IP reputation in Redis
            scan_key = f"scan:{packet.tenant_id}:{packet.src_ip}"
            if self.redis:
                await self._update_ip_reputation(scan_key, packet.dst_port)
                unique_ports = await self.redis.scard(scan_key)
            else:
                unique_ports = 0
            
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
        
        if self.total_inspected > 50 and "VOLATILITY_SPIKE" not in risk.behavior_flags:
            risk.behavior_flags.append("VOLATILITY_SPIKE")
        if unique_ports > 15 and "STEALTH_PORT_SCAN" not in risk.behavior_flags:
            risk.behavior_flags.append("STEALTH_PORT_SCAN")
        if ip_profile["total_threats"] >= 2 and "REPEAT_OFFENDER" not in risk.behavior_flags:
            risk.behavior_flags.append("REPEAT_OFFENDER")
            
        # --- 🧠 CONTINUOUS LEARNING INTEGRATION ---
        # 1. Self-Improvement Loop (High Confidence Reinforcement)
        continuous_learner.auto_label_sample(feature_array, classification)
        
        # 2. Drift Monitoring (Is the model losing its touch?)
        is_unknown = classification.attack_type == AttackType.UNKNOWN
        continuous_learner.monitor_drift(
            confidence=combined_confidence, 
            is_unknown=is_unknown, 
            is_anomaly=anomaly.is_anomaly
        )
            
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
        else:
            # 🛡️ Build Trust for legitimate recurring users
            await ip_reputation_engine.record_normal_traffic(src_ip, tenant_id)
        
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

    async def _check_adversarial_risk(self, features: np.ndarray) -> float:
        """
        🛡️ ADVERSARIAL ML SHIELD
        Detects if a packet is engineered to bypass detection (Evaded Attack).
        Uses 'Stochastic Jitter' - if small perturbations flip the label,
        it's high risk for being an adversarial example.
        """
        # 1. Base prediction
        base_class = attack_classifier.predict(features).attack_type
        
        # 2. Add 'Adversarial Jitter'
        jitter = np.random.normal(0, 0.05, features.shape)
        perturbed_features = features + jitter
        
        # 3. New prediction
        perturbed_class = attack_classifier.predict(perturbed_features).attack_type
        
        # If classes differ with tiny jitter, we are on a decision boundary (Adversarial)
        if base_class != perturbed_class:
            return 0.85 # High probability of exploit evasion
        return 0.0

# Singleton
detector_agent = DetectorAgent()
