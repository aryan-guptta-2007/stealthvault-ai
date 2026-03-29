"""
╔═══════════════════════════════════════════════════════════╗
║          SOC ORCHESTRATOR — The Command Center            ║
║  Chains: Detector → Analyst → Defender                    ║
║  "One brain. Three agents. Zero compromise."              ║
╚═══════════════════════════════════════════════════════════╝

This is the master controller that runs the full multi-agent
pipeline on every packet. It's the entry point for the entire
autonomous defense system.
"""

import time
import asyncio
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

from app.models.alert import NetworkPacket, ThreatAlert, Severity
from app.agents.detector import detector_agent, DetectionVerdict
from app.agents.analyst import analyst_agent, ThreatIntelligence
from app.agents.defender import defender_agent, DefenseAction
from app.agents.story import story_engine
from app.websocket.feed import ws_manager
from app.database import persist_soc_results, log_event
from app.decision.ip_reputation import ip_reputation_engine


@dataclass
class SOCVerdict:
    """Complete SOC pipeline result — the full story of what happened."""
    detection: DetectionVerdict
    intelligence: Optional[ThreatIntelligence] = None
    defense_action: Optional[DefenseAction] = None
    processing_time_ms: float = 0.0
    
    def to_dict(self) -> dict:
        result = {
            "packet": {
                "src_ip": self.detection.packet.src_ip,
                "dst_ip": self.detection.packet.dst_ip,
                "src_port": self.detection.packet.src_port,
                "dst_port": self.detection.packet.dst_port,
                "protocol": self.detection.packet.protocol.value,
            },
            "detection": {
                "is_threat": self.detection.is_threat,
                "is_anomaly": self.detection.anomaly.is_anomaly,
                "attack_type": self.detection.classification.attack_type.value,
                "risk_score": self.detection.risk.score,
                "severity": self.detection.risk.severity.value,
                "signal_count": self.detection.signal_count,
                "confidence": self.detection.combined_confidence,
            },
            "processing_time_ms": self.processing_time_ms,
        }
        
        if self.intelligence:
            result["intelligence"] = {
                "attack_stage": self.intelligence.attack_stage,
                "kill_chain_position": self.intelligence.kill_chain_position,
                "sophistication": self.intelligence.estimated_sophistication,
                "is_campaign": self.intelligence.is_part_of_campaign,
                "risk_trajectory": self.intelligence.risk_trajectory,
                "urgency": self.intelligence.urgency,
                "auto_defend": self.intelligence.auto_defend,
            }
            if self.intelligence.brain_analysis:
                result["brain"] = {
                    "attack_name": self.intelligence.brain_analysis.attack_name,
                    "danger_level": self.intelligence.brain_analysis.danger_level,
                    "what_is_happening": self.intelligence.brain_analysis.what_is_happening,
                    "how_to_stop": self.intelligence.brain_analysis.how_to_stop,
                    "recommended_actions": self.intelligence.brain_analysis.recommended_actions,
                }
        
        if self.defense_action:
            result["defense"] = self.defense_action.to_dict()
        
        return result


class SOCOrchestrator:
    """
    🎯 The SOC Orchestrator — Master Controller
    
    Runs the full 3-agent pipeline:
    
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ DETECTOR │ →  │ ANALYST  │ →  │ DEFENDER │
    │ (Eyes)   │    │ (Brain)  │    │ (Fist)   │
    └──────────┘    └──────────┘    └──────────┘
         ↓               ↓               ↓
      Detect          Understand        Act
    
    Each agent operates independently but communicates
    through structured data objects (DetectionVerdict →
    ThreatIntelligence → DefenseAction).
    """
    
    def __init__(self):
        self.total_processed: int = 0
        self.total_threats: int = 0
        self.total_defenses: int = 0
        self.avg_processing_ms: float = 0.0
        
        # 📊 Granular Observability
        self.avg_detector_ms: float = 0.0
        self.avg_analyst_ms: float = 0.0
        self.avg_confidence_score: float = 0.0
        self.total_unknowns: int = 0
    
    async def process(self, packet: NetworkPacket) -> SOCVerdict:
        """
        Run the full 3-agent pipeline on a packet.
        
        Flow:
        1. Detector inspects the packet → DetectionVerdict
        2. If threat → Analyst produces intelligence → ThreatIntelligence
        3. If auto-defend → Defender takes action → DefenseAction
        4. Broadcast via WebSocket
        """
        start = time.perf_counter()
        self.total_processed += 1
        
        # ═══ AGENT 1: DETECTOR ═══
        d_start = time.perf_counter()
        try:
            verdict = await detector_agent.inspect(packet)
        except Exception as e:
            log_event("ERROR", "Orchestrator", f"Detector stage failed: {e}", stack_trace=str(e))
            return None # Fail safe
        
        self.avg_detector_ms = (self.avg_detector_ms * 0.95 + (time.perf_counter() - d_start) * 1000 * 0.05)
        
        intelligence = None
        defense_action = None
        
        # ═══ AGENT 2: ANALYST ═══
        if verdict.is_threat:
            self.total_threats += 1
            a_start = time.perf_counter()
            try:
                intelligence = analyst_agent.analyze(verdict)
            except Exception as e:
                log_event("ERROR", "Orchestrator", f"Analyst stage failed: {e}", stack_trace=str(e))
            
            self.avg_analyst_ms = (self.avg_analyst_ms * 0.95 + (time.perf_counter() - a_start) * 1000 * 0.05)
            
            # ═══ AGENT 3: DEFENDER ═══
            if intelligence and intelligence.auto_defend:
                try:
                    defense_action = await defender_agent.defend(intelligence)
                    if defense_action and defense_action.success:
                        self.total_defenses += 1
                except Exception as e:
                    log_event("ERROR", "Orchestrator", f"Defender stage failed: {e}", stack_trace=str(e))
        
        elapsed_ms = (time.perf_counter() - start) * 1000
        self.avg_processing_ms = (
            self.avg_processing_ms * 0.95 + elapsed_ms * 0.05
        )
        self.avg_confidence_score = (
            self.avg_confidence_score * 0.95 + verdict.classification.confidence * 0.05
        )
        if verdict.classification.attack_type.value == "Unknown":
            self.total_unknowns += 1
        
        soc_verdict = SOCVerdict(
            detection=verdict,
            intelligence=intelligence,
            defense_action=defense_action,
            processing_time_ms=round(elapsed_ms, 2),
        )
        
        # ═══ ATTACK STORY ENGINE ═══
        story = None
        if verdict.is_threat and intelligence and intelligence.brain_analysis:
            alert = ThreatAlert(
                timestamp=packet.timestamp or datetime.utcnow(),
                packet=packet,
                anomaly=verdict.anomaly,
                classification=verdict.classification,
                risk=verdict.risk,
                brain_analysis=intelligence.brain_analysis,
            )
            await ws_manager.broadcast_alert(alert)
            
            story = story_engine.add_event(
                src_ip=packet.src_ip,
                dst_ip=packet.dst_ip,
                attack_type=verdict.classification.attack_type,
                risk_score=verdict.risk.score,
                severity=verdict.risk.severity,
                defense_action=defense_action.action_type if defense_action else "",
                tenant_id=packet.tenant_id,
            )
        
        # ═══ DATABASE PERSISTENCE (Full Audit Trail) ═══
        asyncio.create_task(persist_soc_results(soc_verdict, story))
        
        # ═══ IP REPUTATION ═══
        if verdict.is_threat:
            asyncio.create_task(
                ip_reputation_engine.record_attack(
                    ip=packet.src_ip, 
                    attack_type=verdict.classification.attack_type.value, 
                    severity=verdict.risk.severity,
                    tenant_id=packet.tenant_id,
                    phase_idx=len(story.phases) if story and story.phases else 1
                )
            )

        return soc_verdict

    async def process_verdict(self, verdict: DetectionVerdict) -> SOCVerdict:
        """
        Process an already-computed DetectionVerdict from the Redis Worker.
        Skips the ML inference (Detector) and runs the Analyst/Defender state machine.
        """
        start = time.perf_counter()
        self.total_processed += 1
        
        intelligence = None
        defense_action = None
        packet = verdict.packet
        
        if verdict.is_threat:
            self.total_threats += 1
            intelligence = analyst_agent.analyze(verdict)
            
            if intelligence.auto_defend:
                defense_action = await defender_agent.defend(intelligence)
                if defense_action and defense_action.success:
                    self.total_defenses += 1
        
        elapsed_ms = (time.perf_counter() - start) * 1000
        self.avg_processing_ms = (self.avg_processing_ms * 0.95 + elapsed_ms * 0.05)
        self.avg_confidence_score = (self.avg_confidence_score * 0.95 + verdict.classification.confidence * 0.05)
        
        if verdict.classification.attack_type.value == "Unknown":
            self.total_unknowns += 1
        
        soc_verdict = SOCVerdict(
            detection=verdict,
            intelligence=intelligence,
            defense_action=defense_action,
            processing_time_ms=round(elapsed_ms, 2),
        )
        
        # Threat Alerting
        story = None
        if verdict.is_threat and intelligence and intelligence.brain_analysis:
            alert = ThreatAlert(
                timestamp=packet.timestamp or datetime.utcnow(),
                packet=packet,
                anomaly=verdict.anomaly,
                classification=verdict.classification,
                risk=verdict.risk,
                brain_analysis=intelligence.brain_analysis,
            )
            await ws_manager.broadcast_alert(alert)
            
            story = story_engine.add_event(
                src_ip=packet.src_ip,
                dst_ip=packet.dst_ip,
                attack_type=verdict.classification.attack_type,
                risk_score=verdict.risk.score,
                severity=verdict.risk.severity,
                defense_action=defense_action.action_type if defense_action else "",
                tenant_id=packet.tenant_id,
            )
        
        # ═══ DATABASE PERSISTENCE (Full Audit Trail) ═══
        asyncio.create_task(persist_soc_results(soc_verdict, story))
        
        # ═══ IP REPUTATION ═══
        if verdict.is_threat:
            asyncio.create_task(
                ip_reputation_engine.record_attack(
                    ip=packet.src_ip, 
                    attack_type=verdict.classification.attack_type.value, 
                    severity=verdict.risk.severity,
                    tenant_id=packet.tenant_id,
                    phase_idx=len(story.phases) if story and story.phases else 1
                )
            )
        
        return soc_verdict
    
    def get_stats(self, tenant_id: str = "default") -> dict:
        """Get telemetry and agent status, scoped by tenant."""
        return {
            "orchestrator": {
                "total_processed": self.total_processed,
                "total_threats": self.total_threats,
                "total_defenses": self.total_defenses,
                "threat_rate": round(
                    self.total_threats / max(self.total_processed, 1), 4
                ),
                "avg_processing_ms": round(self.avg_processing_ms, 2),
                "avg_confidence_score": round(self.avg_confidence_score, 4),
                "total_unknowns": self.total_unknowns,
                "unknown_percentage": round(self.total_unknowns / max(self.total_processed, 1), 4),
            },
            "agents": {
                "detector": detector_agent.get_stats(),
                "analyst": analyst_agent.get_stats(),
                "defender": defender_agent.get_stats(tenant_id),
            },
            "stories": story_engine.get_stats(),
        }


# Singleton
soc_orchestrator = SOCOrchestrator()
