"""
StealthVault AI - IP Reputation Engine
Tracks the long-term behavioral profile of IP addresses using Redis.
Applies a 1.5x risk multiplier to repeat offenders.
"""

import json
import redis.asyncio as redis
from datetime import datetime
from typing import TypedDict, List
from app.models.alert import Severity


class IPProfile(TypedDict):
    ip_address: str
    total_threats: int
    first_seen: str
    last_attack: str
    attack_history: List[str]
    historical_risk_multiplier: float
    
    # 🧠 NEW: Behavioral Intelligence
    avg_pps: float # Average packets per second
    burst_count: int # Number of high-velocity events
    kill_chain_max_phase: int # 1 (Recon) to 7 (Exfil)
    behavioral_tags: List[str] # "Scanner", "Aggressive", etc.
    dwell_time_seconds: float # Time between first and last seen
    block_count: int # Number of times this IP has been blocked
    
    # 🛡️ NEW: Trust & Legitimacy
    trust_score: float # 0.0 to 1.0 (trusted)
    normal_count: int # Total non-malicious packets



class IPReputationEngine:
    """Manages long-term stateful IP Profiles."""

    TTL_SECONDS = 60 * 60 * 24 * 7  # 7 Days Memory Decay

    def __init__(self):
        self.redis = None
        try:
            # ⚡ Safe connection
            import os
            redis_url = os.getenv("REDIS_URL")
            if redis_url:
                self.redis = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=2
                )
            else:
                print("⚠️ Redis not configured, running without it")
        except Exception as e:
            print(f"Redis error: {e}")
            self.redis = None

    def _get_key(self, ip: str, tenant_id: str = "default") -> str:
        return f"tenant:{tenant_id}:ip_profile:{ip}"

    def _default_profile(self, ip: str) -> IPProfile:
        return {
            "ip_address": ip,
            "total_threats": 0,
            "first_seen": datetime.utcnow().isoformat(),
            "last_attack": "",
            "attack_history": [],
            "historical_risk_multiplier": 1.0,
            "avg_pps": 0.0,
            "burst_count": 0,
            "kill_chain_max_phase": 0,
            "behavioral_tags": [],
            "dwell_time_seconds": 0.0,
            "block_count": 0,
            "trust_score": 0.5, # Start neutral
            "normal_count": 0,
        }

    async def get_profile(self, ip: str, tenant_id: str = "default") -> IPProfile:
        """Fetch an IP's reputation profile from Redis."""
        if not self.redis:
            return self._default_profile(ip)
            
        key = self._get_key(ip, tenant_id)
        data = await self.redis.get(key)
        
        if not data:
            return self._default_profile(ip)
            
        try:
            profile: IPProfile = json.loads(data)
            return profile
        except json.JSONDecodeError:
            return self._default_profile(ip)

    async def record_attack(self, ip: str, attack_type: str, severity: Severity, tenant_id: str = "default", phase_idx: int = 0):
        """Asynchronously record a confirmed attack to an IP's permanent record."""
        profile = await self.get_profile(ip, tenant_id)
        
        now = datetime.utcnow()
        profile["total_threats"] += 1
        profile["last_attack"] = now.isoformat()
        
        # 1. Kill Chain Escalation
        if phase_idx > profile["kill_chain_max_phase"]:
            profile["kill_chain_max_phase"] = phase_idx
            if "Escalating" not in profile["behavioral_tags"]:
                profile["behavioral_tags"].append("Escalating")
        
        # 2. Rolling Attack History
        profile["attack_history"].append(f"{attack_type} ({severity.value})")
        if len(profile["attack_history"]) > 10:
            profile["attack_history"].pop(0)
            
        # 3. Aggressiveness Tracking
        if profile["total_threats"] >= 5 and "Aggressive" not in profile["behavioral_tags"]:
            profile["behavioral_tags"].append("Aggressive")
            
        # 4. Multiplier Logic (Locked in escalation bonus)
        if profile["kill_chain_max_phase"] >= 4:
            profile["historical_risk_multiplier"] = 1.75 # Exploit phase reached
        elif profile["total_threats"] >= 2:
            profile["historical_risk_multiplier"] = min(1.5, profile["historical_risk_multiplier"] + 0.1)
            
        # 5. Dwell Time
        first_seen = datetime.fromisoformat(profile["first_seen"])
        profile["dwell_time_seconds"] = (now - first_seen).total_seconds()
            
        # 6. Trust Decay
        profile["trust_score"] = max(0.0, profile["trust_score"] - 0.2)
            
        key = self._get_key(ip, tenant_id)
        if self.redis:
            await self.redis.setex(key, self.TTL_SECONDS, json.dumps(profile))
        
    async def record_normal_traffic(self, ip: str, tenant_id: str = "default"):
        """Increments 'Normal' event count and slowly builds trust."""
        profile = await self.get_profile(ip, tenant_id)
        profile["normal_count"] += 1
        
        # 🛡️ TRUST BUILDING LOGIC
        # Every 100 normal packets increases trust by 0.01
        if profile["normal_count"] % 100 == 0:
            profile["trust_score"] = min(1.0, profile["trust_score"] + 0.01)
            
        # Long-term Dwell Reward: if first seen > 7 days ago and active, boost trust
        first_seen = datetime.fromisoformat(profile["first_seen"])
        dwell_days = (datetime.utcnow() - first_seen).days
        if dwell_days > 7 and profile["trust_score"] < 0.9:
            profile["trust_score"] = min(0.9, profile["trust_score"] + 0.05)
            
        key = self._get_key(ip, tenant_id)
        if self.redis:
            await self.redis.setex(key, self.TTL_SECONDS, json.dumps(profile))


# Singleton
ip_reputation_engine = IPReputationEngine()
