"""
╔═══════════════════════════════════════════════════════════╗
║            AGENT 3: DEFENDER — The Fist                   ║
║  Takes autonomous defensive action.                       ║
║  "Detection without action is just observation."          ║
╚═══════════════════════════════════════════════════════════╝

Role in the AI SOC Team:
    [Detector] → [Analyst] → Defender
    
This agent receives intelligence from the Analyst and takes
autonomous defensive actions: blocking IPs, throttling traffic,
and isolating threats.

⚠️ Windows: Uses netsh advfirewall for IP blocking.
⚠️ Linux: Uses iptables for IP blocking.
"""

import os
import sys
import time
import subprocess
import json
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict

from app.agents.analyst import ThreatIntelligence
from app.decision.ip_reputation import ip_reputation_engine
from app.config import settings
from app.models.alert import Severity


@dataclass
class DefenseAction:
    """Record of a defensive action taken by Agent 3."""
    action_type: str          # block_ip, throttle, alert, isolate
    target: str               # IP address or resource
    reason: str               # Why this action was taken
    severity: str             # Severity that triggered this
    success: bool = True
    timestamp: float = field(default_factory=time.time)
    auto: bool = True         # Was this automatic or manual?
    details: str = ""         # Additional details
    
    def to_dict(self) -> dict:
        return {
            "action_type": self.action_type,
            "target": self.target,
            "reason": self.reason,
            "severity": self.severity,
            "success": self.success,
            "timestamp": self.timestamp,
            "auto": self.auto,
            "details": self.details,
            "time_human": datetime.fromtimestamp(self.timestamp).isoformat(),
        }


# Safe IPs that should NEVER be blocked
SAFE_IPS = {
    "127.0.0.1",
    "localhost",
    "0.0.0.0",
    "::1",
    "192.168.1.1",    # Default gateway
    "10.0.0.1",       # Common gateway
    "8.8.8.8",        # Google DNS
    "8.8.4.4",        # Google DNS
    "1.1.1.1",        # Cloudflare DNS
}


class DefenderAgent:
    """
    🛡️ Agent 3: The Defender (Multi-Tenant Version)
    
    Responsibilities:
    - Block malicious IPs (Windows Firewall / iptables)
    - Track all defensive actions taken per tenant
    - Maintain isolated blocklists with expiration
    - Prevent false-positive blocking with safety checks
    """
    
    def __init__(self):
        # Multi-Tenant State
        self.tenant_shadow_mode: dict[str, bool] = defaultdict(lambda: True)
        self.tenant_blocked_ips: dict[str, dict[str, dict]] = defaultdict(dict)
        self.tenant_action_log: dict[str, list[DefenseAction]] = defaultdict(list)
        
        self.total_blocks: int = 0
        self.total_actions: int = 0
        
        # Shared Infrastructure Safety
        self._last_block_time: dict[str, float] = {}  # IP → last block timestamp (Global to prevent host-level thrashing)
        self._blocks_this_minute: int = 0
        self._minute_start: float = time.time()
        self.max_blocks_per_minute: int = 20
        self.block_cooldown: int = 60  # seconds
        
        # 🧠 Neural Defense Config
        self.neural_threshold_risk: float = 0.9
        self.neural_threshold_confidence: float = 0.8
        
        # Load existing blocklists (Migrating to multi-tenant structure)
        self._blocklist_path = os.path.join(settings.DATA_DIR, "tenant_blocklists.json")
        self._load_blocklist()
        
        # 🧪 Simulation Mode (Skip real OS-level firewall calls)
        self.simulation_mode = os.getenv("STEALTH_SIMULATION_MODE", "false").lower() == "true"
        if self.simulation_mode:
            print("  🧪 DEFENDER: Simulation Mode ACTIVE (Skipping real firewall calls)")
    
    def get_shadow_mode(self, tenant_id: str) -> bool:
        """Helper to get shadow mode for a tenant."""
        return self.tenant_shadow_mode[tenant_id]

    def arm(self, tenant_id: str = "default") -> dict:
        """Arm the defender for a specific tenant."""
        self.tenant_shadow_mode[tenant_id] = False
        return {
            "status": "ARMED",
            "tenant_id": tenant_id,
            "message": f"🛡️ Defender Agent is now ARMED for tenant {tenant_id}.",
            "blocked_ips": len(self.tenant_blocked_ips[tenant_id]),
        }
    
    def disarm(self, tenant_id: str = "default") -> dict:
        """Disarm the defender for a specific tenant."""
        self.tenant_shadow_mode[tenant_id] = True
        return {
            "status": "SHADOW_MODE",
            "tenant_id": tenant_id,
            "message": f"⚠️ Defender Agent returned to SHADOW MODE for tenant {tenant_id}.",
        }
    
    async def defend(self, intel: ThreatIntelligence) -> Optional[DefenseAction]:
        """Process threat intelligence and take defensive action if needed."""
        if not intel.auto_defend:
            return None
        
        src_ip = intel.verdict.packet.src_ip
        tenant_id = getattr(intel.verdict.packet, "tenant_id", "default")
        severity = intel.verdict.risk.severity.value
        attack_type = intel.verdict.classification.attack_type.value
        
        # Safety check 1: Don't block safe IPs
        if src_ip in SAFE_IPS:
            return self._log_action(DefenseAction(
                action_type="skipped",
                target=src_ip,
                reason=f"Safe IP ({attack_type})",
                severity=severity,
                success=False,
                details="IP is in the safe whitelist",
            ), tenant_id)
        
        # Global Infrastructure safety: don't thrash the host firewall
        now = time.time()
        if src_ip in self._last_block_time:
            if now - self._last_block_time[src_ip] < self.block_cooldown:
                return None
        
        if now - self._minute_start > 60:
            self._blocks_this_minute = 0
            self._minute_start = now
        
        if self._blocks_this_minute >= self.max_blocks_per_minute:
            return self._log_action(DefenseAction(
                action_type="rate_limited",
                target=src_ip,
                reason=f"Rate limit exceeded ({attack_type})",
                severity=severity,
                success=False,
                details=f"Max {self.max_blocks_per_minute} blocks/min",
            ), tenant_id)
        
        # 🧠 NEURAL DEFENSE LOGIC: The "Neural Threshold" gate
        risk_score = intel.verdict.risk.score
        confidence = intel.verdict.combined_confidence
        
        is_neural_ready = (
            risk_score >= self.neural_threshold_risk 
            and confidence >= self.neural_threshold_confidence
        )
        
        # If it's a campaign, we lower the threshold slightly for "Surgical Defense"
        if intel.is_part_of_campaign:
            is_neural_ready = risk_score >= 0.8 and confidence >= 0.7

        if not is_neural_ready and severity != Severity.CRITICAL:
            return self._log_action(DefenseAction(
                action_type="analyzing",
                target=src_ip,
                reason=f"Risk ({risk_score:.2f}) or Confidence ({confidence:.2f}) below Neural Threshold",
                severity=severity,
                success=True,
                details="Monitoring for further behavioral evidence before automatic intervention.",
            ), tenant_id)

        # 🪐 LEGITIMATE USER SAFETY CHECK
        profile = await ip_reputation_engine.get_profile(src_ip, tenant_id)
        trust_score = profile.get("trust_score", 0.5)
        
        if trust_score > 0.8:
            # This is a highly trusted IP. Do not block automatically unless CRITICAL.
            if severity != Severity.CRITICAL.value or confidence < 0.95:
                return self._log_action(DefenseAction(
                    action_type="protected_alert",
                    target=src_ip,
                    reason=f"High Trust IP ({trust_score:.2f}) — Block suppressed",
                    severity=severity,
                    success=True,
                    details="This IP is a recognized long-term legitimate user. Automatic blocking is suppressed to prevent system disruption."
                ), tenant_id)

        # 🪜 Multi-Tier Escalation Ladder
        profile = await ip_reputation_engine.get_profile(src_ip, tenant_id)
        block_count = profile.get("block_count", 0)
        
        # Determine TTL based on escalation
        if block_count == 0:
            ttl = 3600 # 1 hour for first breach
            ladder_reason = f"Neural Auto-Block (1h) ({attack_type})"
        elif block_count == 1:
            ttl = 86400 # 24 hours
            ladder_reason = f"Level 2 Escalation (24h) ({attack_type})"
        else:
            ttl = 315360000 # Permanent
            ladder_reason = f"Permanent Exclusion ({attack_type})"
            
        # 🛰️ IAM ISOLATION (Simulated)
        if intel.kill_chain_position >= 5:
            # Malware or Data Exfiltration — Isolate immediately
            self._log_action(DefenseAction(
                action_type="isolate_iam",
                target=src_ip,
                reason="High-Privilege Threat Isolation",
                severity="critical",
                success=True,
                details=f"System recommended session revocation for credentials mapped to {src_ip}"
            ), tenant_id)

        return await self._execute_block(src_ip, attack_type, severity, intel, tenant_id=tenant_id, ttl=ttl, ladder_msg=ladder_reason)
    
    def manual_block(self, ip: str, tenant_id: str = "default", reason: str = "Manual block") -> DefenseAction:
        """Manually block an IP address for a specific tenant."""
        if ip in SAFE_IPS:
            return DefenseAction(
                action_type="rejected",
                target=ip,
                reason="Cannot block safe IP",
                severity="manual",
                success=False,
                auto=False,
            )
        
        # NOTE: Actual firewall block is global to host, but policy is tenant-specific
        success = self._block_ip_firewall(ip)
        action = DefenseAction(
            action_type="block_ip",
            target=ip,
            reason=reason,
            severity="manual",
            success=success,
            auto=False,
            details=f"Manual block by operator for tenant {tenant_id}",
        )
        
        if success:
            self.tenant_blocked_ips[tenant_id][ip] = {
                "blocked_at": time.time(),
                "reason": reason,
                "auto": False,
            }
            self._save_blocklist()
        
        return self._log_action(action, tenant_id)
        
    def waf_block(self, ip: str, duration_min: int, reason: str, tenant_id: str = "default") -> DefenseAction:
        """Called by the API Middleware to automatically block API abusers (Fail2Ban)."""
        if ip in SAFE_IPS or ip in {"127.0.0.1", "localhost", "::1", "0.0.0.0"}:
            return self._log_action(DefenseAction("rejected", ip, "Cannot block safe IP via WAF", "manual", False, False), tenant_id)
            
        ttl = duration_min * 60
        shadow_mode = self.tenant_shadow_mode[tenant_id]
        success = False if shadow_mode else self._block_ip_firewall(ip)
        
        action_type = "shadow_block" if shadow_mode else "waf_block"
        expires_at = time.time() + ttl
        
        if success or shadow_mode:
            self.tenant_blocked_ips[tenant_id][ip] = {
                "blocked_at": time.time(),
                "expires_at": expires_at,
                "reason": reason,
                "auto": True,
                "risk_score": 1.0,  # Max risk for API abusers
                "firewall_applied": not shadow_mode,
            }
            self._save_blocklist()
            
        action = DefenseAction(
            action_type=action_type, 
            target=ip, 
            reason=reason,
            severity="critical", 
            success=success,
            details=f"WAF Auto-Block for {duration_min} minutes. Shadow Mode: {shadow_mode}"
        )
        return self._log_action(action, tenant_id)
    
    def unblock(self, ip: str, tenant_id: str = "default") -> DefenseAction:
        """Remove an IP from the blocklist of a tenant."""
        # Policy Check: Only unblock from firewall if NO other tenant has this blocked
        tenant_count = sum(1 for tid in self.tenant_blocked_ips if ip in self.tenant_blocked_ips[tid])
        
        success = True
        if tenant_count <= 1:
            success = self._unblock_ip_firewall(ip)
        
        if ip in self.tenant_blocked_ips[tenant_id]:
            del self.tenant_blocked_ips[tenant_id][ip]
            self._save_blocklist()
        
        action = DefenseAction(
            action_type="unblock_ip",
            target=ip,
            reason="Operator unblock",
            severity="manual",
            success=success,
            auto=False,
        )
        return self._log_action(action, tenant_id)
    
    def clear_all_blocks(self, tenant_id: str = "default") -> int:
        """🚨 Emergency Switch: Immediately unblocks ALL IPs for a specific tenant."""
        count = 0
        ips = list(self.tenant_blocked_ips[tenant_id].keys())
        for ip in ips:
            self.unblock(ip, tenant_id)
            count += 1
        
        self._log_action(DefenseAction(
            action_type="emergency_unblock_all",
            target="all",
            reason=f"Operator triggered emergency clear for tenant {tenant_id}",
            severity="critical",
            success=True,
            auto=False,
            details=f"Cleared {count} isolated rules."
        ), tenant_id)
        return count
    
    async def _execute_block(
        self, ip: str, attack_type: str, severity: str, intel: ThreatIntelligence, tenant_id: str = "default", ttl: int = 3600, ladder_msg: str = None
    ) -> DefenseAction:
        """Execute an IP block. Evaluates shadow mode for the tenant."""
        shadow_mode = self.tenant_shadow_mode[tenant_id]
        
        if not shadow_mode:
            success = self._block_ip_firewall(ip)
            action_type = "block_ip"
        else:
            success = False  # Shadow Mode — simulate only
            action_type = "shadow_block"
        
        reason = ladder_msg if ladder_msg else f"Auto-defense: {attack_type} (risk={intel.verdict.risk.score:.2f})"
        
        action = DefenseAction(
            action_type=action_type,
            target=ip,
            reason=reason,
            severity=severity,
            success=success,
            details=(
                f"Signals: {intel.verdict.signal_count}, "
                f"Confidence: {intel.verdict.combined_confidence:.2f}, "
                f"Shadow Mode: {shadow_mode}, "
                f"TTL: {ttl}s, "
                f"Tenant: {tenant_id}"
            ),
        )
        
        expires_at = time.time() + ttl
        
        if success or shadow_mode:
            self.tenant_blocked_ips[tenant_id][ip] = {
                "blocked_at": time.time(),
                "expires_at": expires_at,
                "reason": attack_type,
                "auto": True,
                "risk_score": intel.verdict.risk.score,
                "firewall_applied": not shadow_mode,
            }
            self._last_block_time[ip] = time.time()
            self._blocks_this_minute += 1
            self.total_blocks += 1
            self.total_blocks += 1
            self._save_blocklist()
            await ip_reputation_engine.increment_block_count(ip, tenant_id)

            # 📉 PERSIST TO DB FOR AUDITING
            try:
                from app.database import AsyncSessionLocal
                from app.models.db_models import DBBlockedIP
                from sqlalchemy import select
                
                async def save_to_db():
                    async with AsyncSessionLocal() as db:
                        # Check if exists
                        stmt = select(DBBlockedIP).where(
                            DBBlockedIP.ip_address == ip,
                            DBBlockedIP.tenant_id == tenant_id
                        )
                        res = await db.execute(stmt)
                        db_block = res.scalars().first()
                        
                        if not db_block:
                            db_block = DBBlockedIP(
                                ip_address=ip,
                                tenant_id=tenant_id
                            )
                            db.add(db_block)
                        
                        db_block.block_timestamp = datetime.utcnow()
                        db_block.reason = reason
                        db_block.expires_at = datetime.fromtimestamp(expires_at)
                        db_block.risk_score = intel.verdict.risk.score
                        db_block.confidence = intel.verdict.combined_confidence
                        db_block.attack_type = attack_type
                        await db.commit()
                
                import asyncio
                asyncio.create_task(save_to_db())
            except Exception as e:
                print(f"   ⚠️ DB persistence failed for block: {e}")
        
        return self._log_action(action, tenant_id)
    
    def process_expirations(self):
        """Auto-Unblock Daemon: Releases IPs that surpassed their penalty TTL."""
        now = time.time()
        for tenant_id in list(self.tenant_blocked_ips.keys()):
            expired_ips = [
                ip for ip, info in self.tenant_blocked_ips[tenant_id].items() 
                if "expires_at" in info and info["expires_at"] < now
            ]
            for ip in expired_ips:
                print(f"🕰️ Auto-Unblocking {ip} for tenant {tenant_id} (Penalty TTL expired)")
                self.unblock(ip, tenant_id)
    
    def _block_ip_firewall(self, ip: str) -> bool:
        """Block an IP at the OS firewall level."""
        if self.simulation_mode:
            return True
            
        try:
            if sys.platform == "win32":
                rule_name = f"StealthVault_Block_{str(ip).replace('.', '_')}"
                # Check if it already exists to avoid errors on duplicate netsh commands
                cmd = f'netsh advfirewall firewall show rule name="{rule_name}"'
                check = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if check.returncode == 0: return True # Already blocked
                
                cmd = (
                    f'netsh advfirewall firewall add rule '
                    f'name="{rule_name}" '
                    f'dir=in action=block remoteip={ip} '
                    f'enable=yes'
                )
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                return result.returncode == 0
            else:
                cmd = f"iptables -A INPUT -s {ip} -j DROP"
                result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=10)
                return result.returncode == 0
        except Exception:
            return False
    
    def _unblock_ip_firewall(self, ip: str) -> bool:
        """Remove an IP block from the OS firewall."""
        if self.simulation_mode:
            return True
            
        try:
            if sys.platform == "win32":
                rule_name = f"StealthVault_Block_{str(ip).replace('.', '_')}"
                cmd = f'netsh advfirewall firewall delete rule name="{rule_name}"'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                return result.returncode == 0
            else:
                cmd = f"iptables -D INPUT -s {ip} -j DROP"
                result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=10)
                return result.returncode == 0
        except Exception:
            return False
    
    def _log_action(self, action: DefenseAction, tenant_id: str = "default") -> DefenseAction:
        """Log a defensive action."""
        self.tenant_action_log[tenant_id].append(action)
        self.total_actions += 1
        
        if len(self.tenant_action_log[tenant_id]) > 500:
            self.tenant_action_log[tenant_id] = self.tenant_action_log[tenant_id][-500:]
        
        icon = "🛡️" if action.success else "⚠️"
        print(f"  {icon} [{action.action_type.upper()}] {tenant_id}:{action.target} — {action.reason}")
        return action
    
    def _load_blocklist(self):
        """Load blocklist from disk."""
        if os.path.exists(self._blocklist_path):
            try:
                with open(self._blocklist_path, "r") as f:
                    data = json.load(f)
                    # Convert flat dict to multi-tenant structure if needed
                    if "default" not in data and data:
                        self.tenant_blocked_ips["default"] = data
                    else:
                        for tid, items in data.items():
                            self.tenant_blocked_ips[tid] = items
            except Exception:
                pass
    
    def _save_blocklist(self):
        """Save blocklist to disk."""
        try:
            os.makedirs(os.path.dirname(self._blocklist_path), exist_ok=True)
            with open(self._blocklist_path, "w") as f:
                json.dump(self.tenant_blocked_ips, f, indent=2, default=str)
        except Exception:
            pass
    
    def get_stats(self, tenant_id: str = "default") -> dict:
        return {
            "agent": "Defender",
            "role": "Fist of the SOC",
            "tenant_id": tenant_id,
            "shadow_mode": self.tenant_shadow_mode[tenant_id],
            "total_blocks": len(self.tenant_blocked_ips[tenant_id]),
            "total_actions": len(self.tenant_action_log[tenant_id]),
            "active_blocks": len(self.tenant_blocked_ips[tenant_id]),
            "blocked_ips": list(self.tenant_blocked_ips[tenant_id].keys())[:20],
            "recent_actions": [
                a.to_dict() for a in self.tenant_action_log[tenant_id][-10:]
            ],
        }

defender_agent = DefenderAgent()
