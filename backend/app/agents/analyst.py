"""
╔═══════════════════════════════════════════════════════════╗
║            AGENT 2: ANALYST — The Brain                   ║
║  Understands attacks. Tells the story.                    ║
║  "What happened, why, and what it means."                 ║
╚═══════════════════════════════════════════════════════════╝

Role in the AI SOC Team:
    [Detector] → Analyst → [Defender]
    
This agent takes the Detector's verdict and produces a rich,
human-readable intelligence report — like a senior SOC analyst
explaining the situation to the CISO.
"""

import time
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict

from app.agents.detector import DetectionVerdict
from app.decision.brain import security_brain
from app.models.alert import (
    BrainAnalysis,
    ThreatAlert,
    Severity,
    AttackType,
)


@dataclass
class ThreatIntelligence:
    """
    Rich intelligence report from the Analyst Agent.
    Goes beyond basic detection — tells the STORY of the attack.
    """
    verdict: DetectionVerdict
    brain_analysis: Optional[BrainAnalysis]
    
    # Attack narrative
    attack_stage: str = "unknown"       # recon, weaponize, deliver, exploit, persist
    kill_chain_position: int = 0        # 1-7 in Cyber Kill Chain
    estimated_sophistication: str = "low"  # low, medium, high, apt
    
    # Context
    is_part_of_campaign: bool = False
    related_ips: list = field(default_factory=list)
    risk_trajectory: str = "stable"     # rising, stable, declining
    
    # Recommendations
    urgency: str = "routine"            # routine, elevated, urgent, critical
    auto_defend: bool = False           # Should Agent 3 take action?
    
    timestamp: float = field(default_factory=time.time)


# Cyber Kill Chain stages
KILL_CHAIN = {
    AttackType.PORT_SCAN: {
        "stage": "reconnaissance",
        "position": 1,
        "narrative": "The attacker is in the **Reconnaissance** phase. They are actively probing your infrastructure to identify weaknesses before launching the main attack. This is the calm before the storm.",
        "sophistication": "low",
    },
    AttackType.BRUTE_FORCE: {
        "stage": "delivery",
        "position": 3,
        "narrative": "The attacker has moved to the **Delivery** phase. They are attempting to gain access through credential attacks. If they succeed, they will immediately escalate to exploitation.",
        "sophistication": "medium",
    },
    AttackType.SQL_INJECTION: {
        "stage": "exploitation",
        "position": 4,
        "narrative": "The attacker is in the **Exploitation** phase. They are actively manipulating your application layer to extract data or gain code execution. Your database is the target.",
        "sophistication": "medium",
    },
    AttackType.XSS: {
        "stage": "exploitation",
        "position": 4,
        "narrative": "The attacker is executing **Client-Side Exploitation**. They are trying to weaponize your own application against your users. If successful, they can hijack sessions at scale.",
        "sophistication": "medium",
    },
    AttackType.MALWARE: {
        "stage": "installation",
        "position": 5,
        "narrative": "The attacker has reached the **Installation** phase. Malware is communicating with external C2 infrastructure. This means the initial breach has ALREADY happened. You are now in incident response mode.",
        "sophistication": "high",
    },
    AttackType.DDOS: {
        "stage": "actions_on_objectives",
        "position": 7,
        "narrative": "The attacker is executing their **Final Objective** — denial of service. This could be a smokescreen for a more sophisticated parallel attack, or extortion. Check for secondary attack vectors.",
        "sophistication": "medium",
    },
    AttackType.UNKNOWN: {
        "stage": "unknown",
        "position": 0,
        "narrative": "**Unclassified threat activity** detected. The behavioral signature doesn't match any known pattern. This could be a zero-day, a sophisticated APT, or novel attack tooling. Treat with elevated caution.",
        "sophistication": "high",
    },
    AttackType.NORMAL: {
        "stage": "none",
        "position": 0,
        "narrative": "Normal traffic. No attack narrative.",
        "sophistication": "none",
    },
}


class AnalystAgent:
    """
    🧠 Agent 2: The Analyst (Multi-Tenant Version)
    
    Responsibilities:
    - Produce tenant-isolated intelligence reports
    - Map attacks to the Cyber Kill Chain
    - Assess sophistication and campaign likelihood per tenant
    """
    
    def __init__(self):
        self.total_analyzed: int = 0
        self.total_campaigns_detected: int = 0
        
        # Multi-Tenant State
        self._tenant_history: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
        self._tenant_timeline: dict[str, list[dict]] = defaultdict(list)
    
    def analyze(self, verdict: DetectionVerdict) -> ThreatIntelligence:
        """
        Produce a rich intelligence report scoped by tenant.
        """
        self.total_analyzed += 1
        now = time.time()
        tenant_id = getattr(verdict.packet, "tenant_id", "default")
        
        attack_type = verdict.classification.attack_type
        kill_chain = KILL_CHAIN.get(attack_type, KILL_CHAIN[AttackType.UNKNOWN])
        
        # Get brain analysis (human-readable explanation)
        brain_analysis = None
        if verdict.is_threat:
            brain_analysis = security_brain.analyze(
                verdict.anomaly,
                verdict.classification,
                verdict.risk,
            )
        
        # Track this IP's attack history for THIS tenant
        src_ip = verdict.packet.src_ip
        history_map = self._tenant_history[tenant_id]
        
        history_map[src_ip].append({
            "type": attack_type.value,
            "risk": verdict.risk.score,
            "time": now,
        })
        
        # Clean old entries (keep last 5 minutes)
        history_map[src_ip] = [
            e for e in history_map[src_ip] if now - e["time"] < 300
        ]
        
        ip_history = history_map[src_ip]
        
        # Detect campaign behavior: same IP, multiple attack types
        unique_attack_types = set(e["type"] for e in ip_history)
        is_campaign = len(unique_attack_types) >= 2 and len(ip_history) >= 3
        if is_campaign:
            self.total_campaigns_detected += 1
        
        # Determine risk trajectory
        if len(ip_history) >= 3:
            recent_scores = [e["risk"] for e in ip_history[-5:]]
            if recent_scores[-1] > recent_scores[0] * 1.2:
                risk_trajectory = "rising"
            elif recent_scores[-1] < recent_scores[0] * 0.8:
                risk_trajectory = "declining"
            else:
                risk_trajectory = "stable"
        else:
            risk_trajectory = "stable"
        
        # Determine urgency
        if verdict.risk.severity == Severity.CRITICAL:
            urgency = "critical"
        elif verdict.risk.severity == Severity.HIGH or is_campaign:
            urgency = "urgent"
        elif verdict.risk.severity == Severity.MEDIUM:
            urgency = "elevated"
        else:
            urgency = "routine"
        
        # Escalate sophistication for campaigns
        sophistication = kill_chain["sophistication"]
        if is_campaign:
            levels = ["none", "low", "medium", "high", "apt"]
            idx = levels.index(sophistication) if sophistication in levels else 1
            sophistication = levels[min(idx + 1, len(levels) - 1)]
        
        # Should we auto-defend?
        auto_defend = (
            verdict.needs_defense
            or (is_campaign and verdict.risk.score >= 0.7)
            or verdict.risk.severity == Severity.CRITICAL
        )
        
        # Related IPs (other IPs that attacked the same target recently for THIS tenant)
        related = []
        for ip, history in history_map.items():
            if ip != src_ip and len(history) > 0:
                recent = [e for e in history if now - e["time"] < 120]
                if len(recent) > 2:
                    related.append(ip)
        
        # Add to timeline for THIS tenant
        timeline = self._tenant_timeline[tenant_id]
        timeline.append({
            "ip": src_ip,
            "type": attack_type.value,
            "severity": verdict.risk.severity.value,
            "risk": verdict.risk.score,
            "time": now,
            "campaign": is_campaign,
        })
        # Keep timeline bounded
        if len(timeline) > 500:
            self._tenant_timeline[tenant_id] = timeline[-500:]
        
        return ThreatIntelligence(
            verdict=verdict,
            brain_analysis=brain_analysis,
            attack_stage=kill_chain["stage"],
            kill_chain_position=kill_chain["position"],
            estimated_sophistication=sophistication,
            is_part_of_campaign=is_campaign,
            related_ips=related[:5],
            risk_trajectory=risk_trajectory,
            urgency=urgency,
            auto_defend=auto_defend,
        )
    
    def get_campaign_summary(self, tenant_id: str = "default") -> list[dict]:
        """Get summary of detected campaigns for a tenant."""
        campaigns = []
        history_map = self._tenant_history[tenant_id]
        for ip, history in history_map.items():
            types = set(e["type"] for e in history)
            if len(types) >= 2 and len(history) >= 3:
                campaigns.append({
                    "attacker_ip": ip,
                    "attack_types": list(types),
                    "total_events": len(history),
                    "first_seen": min(e["time"] for e in history),
                    "last_seen": max(e["time"] for e in history),
                    "avg_risk": round(sum(e["risk"] for e in history) / len(history), 3),
                })
        return sorted(campaigns, key=lambda c: c["avg_risk"], reverse=True)
    
    def get_stats(self) -> dict:
        return {
            "agent": "Analyst",
            "role": "Brain of the SOC",
            "total_analyzed": self.total_analyzed,
            "campaigns_detected": self.total_campaigns_detected,
            "total_tenants_tracked": len(self._tenant_history),
        }

analyst_agent = AnalystAgent()
