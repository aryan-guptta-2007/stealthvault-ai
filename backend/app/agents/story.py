"""
╔═══════════════════════════════════════════════════════════╗
║          ATTACK STORY ENGINE — The Viral Feature          ║
║                                                           ║
║  Turns raw detections into human-readable attack stories  ║
║  that show the FULL narrative of a cyber intrusion.       ║
║                                                           ║
║  "Not just alerts. STORIES."                              ║
╚═══════════════════════════════════════════════════════════╝

This is the feature that makes StealthVault AI go viral.

Instead of:
    "DDoS detected from 192.168.1.5"

You get:
    🚨 ATTACK STORY DETECTED
    
    Phase 1: Reconnaissance (14:32:01)
    → Port scanning from 192.168.1.5
    → 847 ports probed in 12 seconds
    
    Phase 2: Access Attempt (14:32:15)
    → Brute force on SSH (port 22)
    → 1,200 login attempts detected
    
    Phase 3: Exploitation (14:32:44) ← PREDICTED
    → Likely malware injection attempt
    
    🧠 AI Insight:
    "This appears to be a coordinated intrusion attempt
     following a classic kill-chain pattern."
    
    🛡️ Action: IP blocked automatically
"""

import time
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict

from app.models.alert import AttackType, Severity


# Kill Chain phases in order
KILL_CHAIN_PHASES = [
    {"phase": 1, "name": "Reconnaissance", "icon": "🔍", "attacks": [AttackType.PORT_SCAN]},
    {"phase": 2, "name": "Weaponization", "icon": "⚙️", "attacks": []},
    {"phase": 3, "name": "Delivery", "icon": "📨", "attacks": [AttackType.BRUTE_FORCE]},
    {"phase": 4, "name": "Exploitation", "icon": "💥", "attacks": [AttackType.SQL_INJECTION, AttackType.XSS]},
    {"phase": 5, "name": "Installation", "icon": "☣️", "attacks": [AttackType.MALWARE]},
    {"phase": 6, "name": "Command & Control", "icon": "📡", "attacks": [AttackType.MALWARE]},
    {"phase": 7, "name": "Actions on Objective", "icon": "🎯", "attacks": [AttackType.DDOS]},
]

# What attack TYPICALLY comes next
PREDICTED_NEXT = {
    AttackType.PORT_SCAN: {
        "prediction": "Exploitation Attempt",
        "detail": "After mapping open services, the attacker will likely attempt to exploit a vulnerability on the discovered ports.",
        "confidence": 0.82,
    },
    AttackType.BRUTE_FORCE: {
        "prediction": "Credential Theft → Lateral Movement",
        "detail": "If successful, the attacker will use the compromised credentials to move laterally through the network.",
        "confidence": 0.78,
    },
    AttackType.SQL_INJECTION: {
        "prediction": "Data Exfiltration",
        "detail": "The attacker is likely to dump database contents including user credentials and sensitive data.",
        "confidence": 0.85,
    },
    AttackType.XSS: {
        "prediction": "Session Hijacking → Account Takeover",
        "detail": "Injected scripts will attempt to steal session tokens and exfiltrate them to the attacker's server.",
        "confidence": 0.74,
    },
    AttackType.MALWARE: {
        "prediction": "Data Exfiltration or Ransomware Deployment",
        "detail": "C2 communication suggests the attacker is preparing to either steal data or deploy ransomware.",
        "confidence": 0.88,
    },
    AttackType.DDOS: {
        "prediction": "Smokescreen for Secondary Attack",
        "detail": "DDoS attacks are often used to distract security teams while a stealthier intrusion occurs on another vector.",
        "confidence": 0.65,
    },
}

# Phase descriptions based on what we observe
PHASE_NARRATIVES = {
    AttackType.PORT_SCAN: "Systematic network probing detected. The attacker is mapping your infrastructure to identify entry points.",
    AttackType.BRUTE_FORCE: "Automated credential attacks targeting authentication services. Password dictionaries are being used.",
    AttackType.SQL_INJECTION: "Database exploitation via malicious SQL payload injection through web application input fields.",
    AttackType.XSS: "Client-side code injection targeting user sessions via malicious JavaScript payloads.",
    AttackType.MALWARE: "Active malware C2 beaconing detected. An internal device is communicating with an external threat actor.",
    AttackType.DDOS: "Volumetric traffic flood targeting service availability. Multiple attack sources coordinated.",
    AttackType.UNKNOWN: "Anomalous behavior patterns that don't match known signatures. Possible zero-day or novel technique.",
}


@dataclass
class StoryPhase:
    """A single phase in an attack story."""
    phase_number: int
    phase_name: str
    icon: str
    attack_type: str
    event_count: int
    first_seen: float
    last_seen: float
    max_risk: float
    max_severity: str
    narrative: str
    is_predicted: bool = False
    prediction_confidence: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "phase": self.phase_number,
            "name": self.phase_name,
            "icon": self.icon,
            "attack_type": self.attack_type,
            "event_count": self.event_count,
            "first_seen": datetime.fromtimestamp(self.first_seen).strftime("%H:%M:%S"),
            "last_seen": datetime.fromtimestamp(self.last_seen).strftime("%H:%M:%S"),
            "duration_seconds": round(self.last_seen - self.first_seen, 1),
            "max_risk": round(self.max_risk, 3),
            "severity": self.max_severity,
            "narrative": self.narrative,
            "is_predicted": self.is_predicted,
            "prediction_confidence": self.prediction_confidence,
        }


@dataclass
class AttackStory:
    """A complete attack story — the viral output."""
    story_id: str
    attacker_ip: str
    target_ip: str
    phases: list[StoryPhase]
    ai_insight: str
    defense_action: str
    total_events: int
    started_at: float
    last_updated: float
    sophistication: str
    risk_trend: str              # escalating, stable, declining
    is_active: bool = True
    
    def to_dict(self) -> dict:
        duration = self.last_updated - self.started_at
        return {
            "story_id": self.story_id,
            "title": f"🚨 ATTACK STORY: {self.attacker_ip}",
            "attacker_ip": self.attacker_ip,
            "target_ip": self.target_ip,
            "phases": [p.to_dict() for p in self.phases],
            "predicted_next": self.phases[-1].to_dict() if self.phases and self.phases[-1].is_predicted else None,
            "ai_insight": self.ai_insight,
            "defense_action": self.defense_action,
            "total_events": self.total_events,
            "started_at": datetime.fromtimestamp(self.started_at).strftime("%Y-%m-%d %H:%M:%S"),
            "duration": f"{int(duration // 60)}m {int(duration % 60)}s" if duration > 60 else f"{int(duration)}s",
            "sophistication": self.sophistication,
            "risk_trend": self.risk_trend,
            "is_active": self.is_active,
            "phase_count": len([p for p in self.phases if not p.is_predicted]),
            "has_prediction": any(p.is_predicted for p in self.phases),
        }


class AttackStoryEngine:
    """
    🎬 The Attack Story Engine
    
    Aggregates individual alerts from the same attacker IP into
    a coherent, multi-phase narrative that shows the FULL story
    of an intrusion attempt.
    
    This is what makes StealthVault go viral:
    - Turns dry alerts into compelling stories
    - Predicts the attacker's next move
    - Shows the kill-chain progression
    - Generates AI insights
    """
    
    def __init__(self, story_timeout: int = 600):
        self.stories: dict[str, AttackStory] = {}
        self.story_timeout = story_timeout  # 10 minutes
        self._ip_events: dict[str, list[dict]] = defaultdict(list)
    
    def add_event(
        self,
        src_ip: str,
        dst_ip: str,
        attack_type: AttackType,
        risk_score: float,
        severity: Severity,
        defense_action: str = "",
        tenant_id: str = "default",
    ) -> Optional[AttackStory]:
        """
        Add a new event and update/create the attack story.
        Returns the updated story if the IP has a multi-phase narrative.
        """
        now = time.time()
        key = f"{tenant_id}:{src_ip}"
        
        event = {
            "attack_type": attack_type,
            "risk_score": risk_score,
            "severity": severity,
            "timestamp": now,
            "defense": defense_action,
        }
        
        self._ip_events[key].append(event)
        
        # Clean old events
        self._ip_events[key] = [
            e for e in self._ip_events[key]
            if now - e["timestamp"] < self.story_timeout
        ]
        
        events = self._ip_events[key]
        
        # Need at least 2 events OR 1 high-severity event to create a story
        if len(events) < 2 and severity not in [Severity.HIGH, Severity.CRITICAL]:
            return None
        
        # Build or update the story
        story = self._build_story(src_ip, dst_ip, events, tenant_id)
        self.stories[key] = story
        
        return story
    
    def _build_story(self, src_ip: str, dst_ip: str, events: list[dict], tenant_id: str) -> AttackStory:
        """Build a complete attack story from events."""
        # Group events by attack type
        type_groups: dict[AttackType, list[dict]] = defaultdict(list)
        for e in events:
            type_groups[e["attack_type"]].append(e)
        
        # Create phases ordered by kill chain position
        phases = []
        observed_types = set()
        
        for kc_phase in KILL_CHAIN_PHASES:
            for attack_type in kc_phase["attacks"]:
                if attack_type in type_groups:
                    group = type_groups[attack_type]
                    observed_types.add(attack_type)
                    
                    severity_order = {
                        Severity.LOW: 0, Severity.MEDIUM: 1,
                        Severity.HIGH: 2, Severity.CRITICAL: 3
                    }
                    max_sev = max(group, key=lambda e: severity_order.get(e["severity"], 0))
                    
                    phases.append(StoryPhase(
                        phase_number=kc_phase["phase"],
                        phase_name=kc_phase["name"],
                        icon=kc_phase["icon"],
                        attack_type=attack_type.value,
                        event_count=len(group),
                        first_seen=min(e["timestamp"] for e in group),
                        last_seen=max(e["timestamp"] for e in group),
                        max_risk=max(e["risk_score"] for e in group),
                        max_severity=max_sev["severity"].value,
                        narrative=PHASE_NARRATIVES.get(attack_type, "Unknown activity detected."),
                    ))
        
        # Handle unknown/unmatched types
        for attack_type, group in type_groups.items():
            if attack_type not in observed_types and attack_type != AttackType.NORMAL:
                severity_order = {
                    Severity.LOW: 0, Severity.MEDIUM: 1,
                    Severity.HIGH: 2, Severity.CRITICAL: 3
                }
                max_sev = max(group, key=lambda e: severity_order.get(e["severity"], 0))
                
                phases.append(StoryPhase(
                    phase_number=0,
                    phase_name="Unknown Phase",
                    icon="🕵️",
                    attack_type=attack_type.value,
                    event_count=len(group),
                    first_seen=min(e["timestamp"] for e in group),
                    last_seen=max(e["timestamp"] for e in group),
                    max_risk=max(e["risk_score"] for e in group),
                    max_severity=max_sev["severity"].value,
                    narrative=PHASE_NARRATIVES.get(attack_type, "Anomalous activity detected."),
                ))
        
        # Sort by first_seen
        phases.sort(key=lambda p: p.first_seen)
        
        # Add PREDICTED next phase
        if phases:
            last_attack = None
            for p in reversed(phases):
                try:
                    last_attack = AttackType(p.attack_type)
                    break
                except ValueError:
                    continue
            
            if last_attack and last_attack in PREDICTED_NEXT:
                pred = PREDICTED_NEXT[last_attack]
                # Find the next kill chain phase
                next_phase_num = max(p.phase_number for p in phases) + 1
                
                phases.append(StoryPhase(
                    phase_number=next_phase_num,
                    phase_name=f"Predicted: {pred['prediction']}",
                    icon="🔮",
                    attack_type="predicted",
                    event_count=0,
                    first_seen=time.time(),
                    last_seen=time.time(),
                    max_risk=0,
                    max_severity="predicted",
                    narrative=pred["detail"],
                    is_predicted=True,
                    prediction_confidence=pred["confidence"],
                ))
        
        # Generate AI insight
        ai_insight = self._generate_insight(phases, src_ip, events)
        
        # Determine sophistication
        unique_types = len(set(e["attack_type"] for e in events if e["attack_type"] != AttackType.NORMAL))
        if unique_types >= 3:
            sophistication = "APT-level (Advanced Persistent Threat)"
        elif unique_types >= 2:
            sophistication = "Coordinated multi-vector attack"
        elif len(events) > 20:
            sophistication = "Automated tooling (scripted)"
        else:
            sophistication = "Opportunistic / low-skill"
        
        # Risk trend
        if len(events) >= 3:
            recent = [e["risk_score"] for e in events[-5:]]
            older = [e["risk_score"] for e in events[:5]]
            if sum(recent) / len(recent) > sum(older) / len(older) * 1.2:
                risk_trend = "⬆️ ESCALATING"
            elif sum(recent) / len(recent) < sum(older) / len(older) * 0.8:
                risk_trend = "⬇️ DECLINING"
            else:
                risk_trend = "➡️ STABLE"
        else:
            risk_trend = "➡️ STABLE"
        
        # Defense action summary
        defenses = [e["defense"] for e in events if e.get("defense")]
        defense_action = defenses[-1] if defenses else "Monitoring — no action taken yet"
        
        return AttackStory(
            story_id=f"story_{tenant_id}_{str(src_ip).replace('.', '_')}_{int(events[0]['timestamp'])}",
            attacker_ip=src_ip,
            target_ip=dst_ip,
            phases=phases,
            ai_insight=ai_insight,
            defense_action=defense_action,
            total_events=len(events),
            started_at=min(e["timestamp"] for e in events),
            last_updated=max(e["timestamp"] for e in events),
            sophistication=sophistication,
            risk_trend=risk_trend,
        )
    
    def _generate_insight(self, phases: list[StoryPhase], attacker_ip: str, events: list[dict]) -> str:
        """Generate a human-readable AI insight about the attack."""
        real_phases = [p for p in phases if not p.is_predicted]
        
        if len(real_phases) == 0:
            return "Insufficient data for analysis."
        
        if len(real_phases) == 1:
            p = real_phases[0]
            return (
                f"Single-vector attack detected from {attacker_ip}. "
                f"The attacker is executing a {p.attack_type} attack "
                f"({p.event_count} events observed). "
                f"This is consistent with {'automated tooling' if p.event_count > 10 else 'manual probing'}. "
                f"Recommend immediate investigation."
            )
        
        # Multi-phase attack
        attack_sequence = " → ".join(p.attack_type for p in real_phases)
        total_events = sum(p.event_count for p in real_phases)
        duration = real_phases[-1].last_seen - real_phases[0].first_seen
        
        insight = (
            f"🚨 MULTI-PHASE INTRUSION DETECTED from {attacker_ip}. "
            f"Attack chain: {attack_sequence}. "
            f"{total_events} total events over {int(duration)}s. "
        )
        
        # Add kill chain analysis
        max_phase = max(p.phase_number for p in real_phases)
        if max_phase >= 5:
            insight += (
                "⚠️ CRITICAL: The attacker has progressed DEEP into the kill chain "
                "(Installation/C2 phase). This indicates an ACTIVE COMPROMISE. "
                "Immediate incident response required."
            )
        elif max_phase >= 3:
            insight += (
                "The attacker has moved from reconnaissance to active exploitation. "
                "If not blocked, the next step is likely malware installation. "
                "Immediate intervention recommended."
            )
        else:
            insight += (
                "The attacker is in the early stages (reconnaissance/delivery). "
                "Block now to prevent escalation to exploitation."
            )
        
        return insight
    
    def get_active_stories(self, tenant_id: str = "default") -> list[dict]:
        """Get all active attack stories for a specific tenant."""
        now = time.time()
        active = []
        prefix = f"{tenant_id}:"
        
        for key, story in self.stories.items():
            if not key.startswith(prefix):
                continue
            if now - story.last_updated < self.story_timeout:
                story.is_active = True
                active.append(story.to_dict())
            else:
                story.is_active = False
        
        return sorted(active, key=lambda s: s["total_events"], reverse=True)
    
    def get_story(self, attacker_ip: str, tenant_id: str = "default") -> Optional[dict]:
        """Get a specific attacker's story."""
        key = f"{tenant_id}:{attacker_ip}"
        if key in self.stories:
            return self.stories[key].to_dict()
        return None
    
    def get_stats(self) -> dict:
        now = time.time()
        active = sum(1 for s in self.stories.values() if now - s.last_updated < self.story_timeout)
        return {
            "total_stories": len(self.stories),
            "active_stories": active,
            "tracked_ips": len(self._ip_events),
        }


# Singleton
story_engine = AttackStoryEngine()
