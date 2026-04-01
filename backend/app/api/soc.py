"""
StealthVault AI - Multi-Agent SOC API
Endpoints for the 3-agent pipeline and defense controls.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.agents.orchestrator import soc_orchestrator
from app.agents.detector import detector_agent
from app.agents.analyst import analyst_agent
from app.agents.defender import defender_agent
from app.agents.story import story_engine
from app.models.alert import NetworkPacket, Protocol
from fastapi import Depends, Request
from app.api.auth import get_current_user, get_optional_user
from app.api.rbac import RoleChecker
from app.core.limiter import limiter

# RBAC Instances
soc_manager_only = Depends(RoleChecker(["soc_manager"]))
soc_analyst_access = Depends(RoleChecker(["soc_analyst"]))


router = APIRouter(prefix="/soc", tags=["🤖 Multi-Agent SOC"])


class PacketInput(BaseModel):
    """Packet data for SOC analysis."""
    src_ip: str = "192.168.1.100"
    dst_ip: str = "10.0.0.1"
    src_port: int = 12345
    dst_port: int = 80
    protocol: str = "TCP"
    packet_size: int = 200
    flags: str = "S"
    payload_size: int = 0
    ttl: int = 64
    duration: float = 0.1


class BlockRequest(BaseModel):
    """Manual IP block request."""
    ip: str
    reason: str = "Manual block by operator"


# ═══ FULL PIPELINE ═══

@router.post("/analyze")
@limiter.limit("100/minute")
async def soc_analyze(request: Request, packet_input: PacketInput, current_user: object = soc_analyst_access):
    """
    🎯 Run the FULL 3-agent pipeline on a packet.
    
    Detector → Analyst → Defender
    
    Returns the complete SOC verdict including detection,
    intelligence, and any defensive actions taken.
    """
    # Convert to NetworkPacket
    try:
        proto = Protocol(packet_input.protocol)
    except ValueError:
        proto = Protocol.TCP

    packet = NetworkPacket(
        src_ip=packet_input.src_ip,
        dst_ip=packet_input.dst_ip,
        src_port=packet_input.src_port,
        dst_port=packet_input.dst_port,
        protocol=proto,
        packet_size=packet_input.packet_size,
        flags=packet_input.flags,
        payload_size=packet_input.payload_size,
        ttl=packet_input.ttl,
        duration=packet_input.duration,
    )

    verdict = await soc_orchestrator.process(packet)
    return verdict.to_dict()


# ═══ AGENT STATUS ═══

@router.get("/status")
@limiter.limit("60/minute")
async def soc_status(request: Request, current_user: dict = soc_analyst_access):
    """Get status of all 3 agents and the orchestrator, scoped by tenant."""
    tenant_id = getattr(current_user, "tenant_id", "default")
    return soc_orchestrator.get_stats(tenant_id)


@router.get("/agents/detector")
@limiter.limit("60/minute")
async def detector_status(request: Request, current_user: object = Depends(get_current_user)):
    """Get Detector Agent (Agent 1) stats (Global Model Stats)."""
    return detector_agent.get_stats()


@router.get("/agents/analyst")
@limiter.limit("60/minute")
async def analyst_status(request: Request, current_user: object = Depends(get_current_user)):
    """Get Analyst Agent (Agent 2) stats."""
    stats = analyst_agent.get_stats()
    stats["campaigns"] = analyst_agent.get_campaign_summary()
    return stats


@router.get("/agents/defender")
@limiter.limit("60/minute")
async def defender_status(request: Request, current_user: dict = Depends(get_current_user)):
    """Get Defender Agent (Agent 3) stats scoped by tenant."""
    tenant_id = getattr(current_user, "tenant_id", "default")
    return defender_agent.get_stats(tenant_id)


# ═══ DEFENSE CONTROLS ═══

@router.post("/defender/arm")
@limiter.limit("10/minute")
async def arm_defender(request: Request, current_user: dict = soc_manager_only):
    """🛡️ ARM the Defender for this tenant."""
    tenant_id = getattr(current_user, "tenant_id", "default")
    return defender_agent.arm(tenant_id)


@router.post("/defender/disarm")
@limiter.limit("10/minute")
async def disarm_defender(request: Request, current_user: dict = soc_manager_only):
    """Disarm the Defender — Enable Shadow Mode for this tenant."""
    tenant_id = getattr(current_user, "tenant_id", "default")
    return defender_agent.disarm(tenant_id)


@router.post("/defender/block")
@limiter.limit("60/minute")
async def manual_block(request: Request, payload: BlockRequest, current_user: dict = soc_manager_only):
    """Manually block an IP address for this tenant."""
    tenant_id = getattr(current_user, "tenant_id", "default")
    action = defender_agent.manual_block(payload.ip, tenant_id, payload.reason)
    return action.to_dict()


@router.post("/defender/unblock")
@limiter.limit("60/minute")
async def unblock_ip(request: Request, payload: BlockRequest, current_user: dict = soc_manager_only):
    """Remove an IP from the blocklist for this tenant."""
    tenant_id = getattr(current_user, "tenant_id", "default")
    action = defender_agent.unblock(payload.ip, tenant_id)
    return action.to_dict()


@router.get("/defender/blocklist")
@limiter.limit("60/minute")
async def get_blocklist(request: Request, current_user: dict = soc_analyst_access):
    """Get the current blocklist for this tenant."""
    tenant_id = getattr(current_user, "tenant_id", "default")
    stats = defender_agent.get_stats(tenant_id)
    return {
        "total_blocked": stats["active_blocks"],
        "blocked_ips": stats["blocked_ips"],
        "is_armed": not stats["shadow_mode"],
        "tenant_id": tenant_id
    }


# ═══ CAMPAIGNS ═══

@router.get("/campaigns")
@limiter.limit("60/minute")
async def get_campaigns(request: Request, current_user: object = Depends(get_current_user)):
    """Get detected multi-stage attack campaigns."""
    campaigns = analyst_agent.get_campaign_summary()
    return {
        "total_campaigns": len(campaigns),
        "campaigns": campaigns,
    }


# ═══ ATTACK STORIES (THE VIRAL FEATURE) ═══

@router.get("/stories")
@limiter.limit("60/minute")
async def get_attack_stories(request: Request, current_user: object | None = Depends(get_optional_user)):
    """
    🎬 Get all active attack stories.
    
    Stories are multi-phase narratives that show the FULL progression
    of an attack from reconnaissance to exploitation, including
    AI-predicted next moves and defense actions taken.
    
    THIS is the feature that makes StealthVault special.
    """
    tenant_id = getattr(current_user, "tenant_id", "default") if current_user else "default"
    stories = story_engine.get_active_stories(tenant_id)

    # Anonymize IPs if public
    if current_user is None:
        for s in stories:
            if s.get("attacker_ip"):
                parts = s["attacker_ip"].split('.')
                if len(parts) == 4:
                    s["attacker_ip"] = f"{parts[0]}.{parts[1]}.x.x"

    return {
        "total_stories": len(stories),
        "stories": stories,
    }


@router.get("/stories/{attacker_ip}")
@limiter.limit("60/minute")
async def get_attack_story(request: Request, attacker_ip: str, current_user: object | None = Depends(get_optional_user)):
    """
    Get a specific attacker's story by IP address.
    
    Returns the complete multi-phase attack narrative including
    kill chain position, AI insights, and predicted next moves.
    """
    tenant_id = getattr(current_user, "tenant_id", "default") if current_user else "default"
    story = story_engine.get_story(attacker_ip, tenant_id)
    
    if current_user is None and story and story.get("attacker_ip"):
        parts = story["attacker_ip"].split('.')
        if len(parts) == 4:
            story["attacker_ip"] = f"{parts[0]}.{parts[1]}.x.x"
            
    if story:
        return story
    return {
        "error": f"No story found for {attacker_ip}",
        "message": "This IP hasn't triggered enough events to build a story yet.",
    }
