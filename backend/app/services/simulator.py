import asyncio
import random
from datetime import datetime
from app.models.alert import NetworkPacket, Protocol
from app.agents.orchestrator import soc_orchestrator
from app.database import log_event

class SimulatorService:
    """
    ⚔️ THE OFFENSIVE SUITE: Generates high-fidelity cyber-attack patterns.
    Allows for real-time stress testing of the AI SOC.
    """

    ATTACK_PROPS = {
        "ddos": {
            "ips": ["185.12.34.5", "103.45.67.8", "45.1.2.3"],
            "protocols": [Protocol.UDP, Protocol.TCP, Protocol.ICMP],
            "ports": [80, 443, 8080],
            "packet_range": (800, 1500),
            "flags": "ACK,PSH",
            "desc": "Distributed Denial of Service (High-Volume Flood)"
        },
        "brute_force": {
            "ips": ["92.45.12.44", "31.5.22.11"],
            "protocols": [Protocol.TCP],
            "ports": [22, 21, 3389],
            "packet_range": (60, 120),
            "flags": "SYN",
            "desc": "Credential Brute Force (SSH/RDP Attack)"
        },
        "port_scan": {
            "ips": ["80.12.33.1"],
            "protocols": [Protocol.TCP],
            "ports": list(range(20, 1025)), # Full range scan
            "packet_range": (40, 60),
            "flags": "SYN",
            "desc": "Reconnaissance: Stealth Port Scan"
        }
    }

    async def launch_attack(self, attack_type: str, intensity: str = "medium", tenant_id: str = "default"):
        """
        Produce a burst of simulated attack packets and feed them into the orchestrator.
        """
        props = self.ATTACK_PROPS.get(attack_type)
        if not props:
            return {"error": "Invalid attack type"}

        # Intensity Scaling
        burst_size = 50 if intensity == "medium" else 150
        delay = 0.05 if intensity == "high" else 0.1

        log_event("COMBAT", "Simulator", f"⚔️ LAUNCHING {attack_type.upper()} BURST ({intensity}) for {tenant_id}")

        async def _run_burst():
            for i in range(burst_size):
                src_ip = random.choice(props["ips"])
                dst_port = random.choice(props["ports"]) if attack_type != "port_scan" else props["ports"][i % len(props["ports"])]
                
                packet = NetworkPacket(
                    src_ip=src_ip,
                    dst_ip="192.168.1.100", # Simulated target node
                    dst_port=dst_port,
                    protocol=random.choice(props["protocols"]),
                    packet_size=random.randint(*props["packet_range"]),
                    flags=props["flags"],
                    tenant_id=tenant_id,
                    timestamp=datetime.utcnow()
                )

                # 🚀 INJECT DIRECTLY INTO SOC BRAIN
                asyncio.create_task(soc_orchestrator.process(packet))
                await asyncio.sleep(delay)

        # Execute as fire-and-forget task
        asyncio.create_task(_run_burst())
        
        return {
            "status": "LAUNCHED",
            "type": attack_type,
            "description": props["desc"],
            "target_node": "ALPHA-NODE-01",
            "packets_scheduled": burst_size
        }

# Singleton
attack_simulator = SimulatorService()
