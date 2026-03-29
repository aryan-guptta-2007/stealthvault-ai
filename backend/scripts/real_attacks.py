"""
StealthVault AI - Live Live-Fire Testing Suite
Validates the AI detection pipeline and Defender Autonomic Safety system.
Generates true-to-life packet behaviors for Nmap, Hydra, and Slowloris.
"""

import asyncio
import httpx
import time
import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SERVER_BASE = "http://localhost:8000"
API_BASE = f"{SERVER_BASE}/api/v1"

# Target Victim IP
TARGET_IP = "10.0.0.100"

# Attacker IPs (Simulating external threats)
NMAP_IP = "185.15.15.22"
HYDRA_IP = "45.33.22.11"
SLOWLORIS_IP = "91.22.33.44"

async def _fire_packet(client: httpx.AsyncClient, packet: dict) -> dict:
    """Send a single packet into the ingestion stream."""
    try:
        resp = await client.post(f"{API_BASE}/traffic/analyze", json=packet)
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

async def simulate_nmap_stealth(client: httpx.AsyncClient):
    """
    Nmap -sS (TCP SYN Scan)
    Behavior: Rapid connection attempts across 100 sequential ports.
    Flags: SYN only. Tiny packet size.
    """
    print(f"\n[💥] LAUNCHING: Nmap Stealth SYN Scan from {NMAP_IP}")
    tasks = []
    
    for port in range(1, 101):
        packet = {
            "src_ip": NMAP_IP,
            "dst_ip": TARGET_IP,
            "src_port": random.randint(40000, 60000),
            "dst_port": port,
            "protocol": "TCP",
            "packet_size": 44,      # Nmap SYN packets are usually 44 bytes (Ethernet + IP + TCP)
            "flags": "S",           # SYN Only
            "payload_size": 0,      # No payload
            "ttl": 55,              # Linux default TTL behavior
            "duration": 0.001       # Tears connection down instantly
        }
        tasks.append(_fire_packet(client, packet))
        # Nmap timing profile
        await asyncio.sleep(0.01)
        
    results = await asyncio.gather(*tasks)
    
    blocked = False
    criticals = 0
    for res in results:
        if "risk" in res and res["risk"]["severity"] == "critical":
            criticals += 1
        if "action" in res and res["action"] in ["block_ip", "shadow_block"]:
            blocked = True

    print(f"  └── 📡 Packets Fired: 100")
    print(f"  └── 🔴 Critical AI Alerts: {criticals}")
    print(f"  └── 🛡️ Defender Block Triggered: {'YES ✓' if blocked else 'NO ❌'}")


async def simulate_hydra_brute(client: httpx.AsyncClient):
    """
    Hydra SSH Brute Force
    Behavior: Large payloads attempting to negotiate SSH auth protocol repeatedly.
    Flags: SYN, ACK, PUSH. Extended duration. Same port.
    """
    print(f"\n[🔑] LAUNCHING: Hydra SSH Brute Force from {HYDRA_IP}")
    tasks = []
    
    # 50 brute force attempts over SSH
    for _ in range(50):
        packet = {
            "src_ip": HYDRA_IP,
            "dst_ip": TARGET_IP,
            "src_port": random.randint(30000, 65000),
            "dst_port": 22,         # SSH Port specifically
            "protocol": "SSH",
            "packet_size": 512,     # SSH Key exchange and auth packet sizing
            "flags": "PA",          # Push + Ack (Sending credentials)
            "payload_size": 300,    # Large comparative payload
            "ttl": 64,              
            "duration": random.uniform(0.5, 2.0)  # SSH auth handshake takes time
        }
        tasks.append(_fire_packet(client, packet))
        await asyncio.sleep(0.05) # Hydra is relatively slow compared to Nmap
        
    results = await asyncio.gather(*tasks)
    
    blocked = False
    for res in results:
        if "action" in res and res["action"] in ["block_ip", "shadow_block"]:
            blocked = True
            
    print(f"  └── 📡 Packets Fired: 50")
    print(f"  └── 🛡️ Defender Block Triggered: {'YES ✓' if blocked else 'NO ❌'}")


async def simulate_slowloris(client: httpx.AsyncClient):
    """
    Slowloris HTTP DDoS
    Behavior: Thousands of HTTP connections held open indefinitely with single byte transfers.
    Flags: ACK, PUSH. Very small payload. HUGE duration.
    """
    print(f"\n[🐢] LAUNCHING: Slowloris Socket Exhaustion from {SLOWLORIS_IP}")
    tasks = []
    
    # 200 hanging sockets
    for _ in range(200):
        packet = {
            "src_ip": SLOWLORIS_IP,
            "dst_ip": TARGET_IP,
            "src_port": random.randint(10000, 60000),
            "dst_port": 443,         # Exhausting HTTPS Threadpool
            "protocol": "HTTPS",
            "packet_size": 60,       # Tiny partial header size
            "flags": "PA",           
            "payload_size": 1,       # Slowly bleeding 1 byte at a time
            "ttl": 110,              # Mixed OS TTL
            "duration": 600.0        # Socket held open for 10 straight minutes
        }
        tasks.append(_fire_packet(client, packet))
        # Blast them all at once
        
    results = await asyncio.gather(*tasks)
    
    blocked = False
    for res in results:
        if "action" in res and res["action"] in ["block_ip", "shadow_block"]:
            blocked = True
            
    print(f"  └── 📡 Packets Fired: 200")
    print(f"  └── 🛡️ Defender Block Triggered: {'YES ✓' if blocked else 'NO ❌'}")


async def check_defender_status(client: httpx.AsyncClient):
    """Validate Defender's internal blocklist after attacks."""
    print(f"\n[🛡️] VALIDATING DEFENDER SOC STATE")
    try:
        resp = await client.get(f"{API_BASE}/dashboard")
        stats = resp.json()
        
        shadow_mode = stats['defender_status']['shadow_mode']
        active_blocks = stats['defender_status']['active_blocks']
        
        print(f"  └── 🕶️ Shadow Mode: {'ACTIVE' if shadow_mode else 'DISABLED (Live Fire)'}")
        print(f"  └── 🧱 Total IPs Formally Blocked: {active_blocks}")
        
    except Exception as e:
        print(f"  └── ❌ Failed to read Defender stats: {e}")


async def main():
    print("=" * 60)
    print("  StealthVault AI — REAL ATTACK VALIDATION SUITE")
    print("=" * 60)
    print("  Ensuring Nmap, Hydra, and Slowloris are effectively mitigated.")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Pre-Flight check
        try:
            await client.get(f"{SERVER_BASE}/health")
        except Exception:
            print("❌ Cannot connect to SOC backend. Start it first: uvicorn app.main:app --reload")
            return

        print("\n⏳ Commencing Attack Run in 3 seconds...\n")
        await asyncio.sleep(3)
        
        # 1. Fire Nmap Scan
        await simulate_nmap_stealth(client)
        await asyncio.sleep(2)
        
        # 2. Fire Hydra Brute Force
        await simulate_hydra_brute(client)
        await asyncio.sleep(2)
        
        # 3. Fire Slowloris Exhaustion
        await simulate_slowloris(client)
        await asyncio.sleep(2)
        
        # 4. Final Verification
        await check_defender_status(client)

if __name__ == "__main__":
    asyncio.run(main())
