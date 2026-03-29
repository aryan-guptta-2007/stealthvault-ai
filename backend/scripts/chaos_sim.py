import asyncio
import random
import time
import requests
import jwt
import sys
from datetime import datetime, timedelta
from typing import List, Dict

# ═══════════════════════════════════════════════════════════
#         STEALTHVAULT AI — CHAOS & REAL-WORLD SIMULATOR
# ═══════════════════════════════════════════════════════════

API_BASE = "http://localhost:8000/api/v1"
SECRET_KEY = "STEALTHVAULT_SUPER_SECRET_KEY_V1"
ALGORITHM = "HS256"

# 🚩 POOLS for Real-World IP Diversity
BOT_POOLS = [
    "185.220.101.",   # Tor Exit Nodes
    "45.33.32.",      # Botnet CIDR A
    "117.20.0.",      # Botnet CIDR B (APAC)
    "92.242.0.",      # Botnet CIDR C (EU)
    "8.8.8.",         # Spoofed DNS (Rare)
]

NORMAL_POOLS = [
    "192.168.1.",     # Internal Legitimate
    "10.0.0.",        # Corporate LAN
    "172.16.0.",      # Private Cloud
]

# 🧪 ATTACK PAYLOADS (From Low-Risk Probing to High-Risk Exploits)
ATTACK_STAGES = {
    "RECON": [
        {"desc": "Port Scan (SYN)", "flags": "S", "payload_size": 0, "risk_base": 0.1},
        {"desc": "Dir Buster (/admin)", "flags": "PA", "payload_size": 150, "risk_base": 0.2},
        {"desc": "Options Probe", "flags": "PA", "payload_size": 50, "risk_base": 0.15},
    ],
    "EXPLOIT": [
        {"desc": "SQL Injection", "flags": "PA", "payload_size": 1200, "risk_base": 0.8},
        {"desc": "XSS Inject", "flags": "PA", "payload_size": 800, "risk_base": 0.6},
        {"desc": "RCE Attempt", "flags": "PA", "payload_size": 2500, "risk_base": 0.9},
    ],
    "C2": [
        {"desc": "C2 Beacon", "flags": "PA", "payload_size": 120, "risk_base": 0.4},
        {"desc": "Exfil Chunk", "flags": "PA", "payload_size": 5000, "risk_base": 0.7},
    ]
}

def generate_token():
    """Generate a JWT token for the simulation."""
    payload = {
        "sub": "chaos_generator",
        "tenant_id": "default",
        "roles": ["admin"],
        "exp": datetime.utcnow() + timedelta(days=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

TOKEN = generate_token()
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

class ChaosSimulator:
    def __init__(self, target_pps: int = 20):
        self.target_pps = target_pps
        self.active_bots: Dict[str, Dict] = {} # IP -> State
        self.running = False
        self.total_sent = 0

    def get_random_ip(self, pool_list: List[str]) -> str:
        return random.choice(pool_list) + str(random.randint(1, 254))

    async def send_packet(self, data: Dict):
        """Dispatches a packet to the SOC pipeline."""
        try:
            # We use /soc/analyze which is the heavy 3-agent pipeline
            resp = requests.post(f"{API_BASE}/soc/analyze", json=data, headers=HEADERS, timeout=5)
            self.total_sent += 1
            if resp.status_code == 200:
                verdict = resp.json()
                det = verdict.get("detection", {})
                if det.get("is_threat"):
                    print(f"  🚨 Threat Detected: {det.get('attack_type')} | Risk: {det.get('risk_score'):.2f} from {data['src_ip']}")
            elif resp.status_code == 429:
                print(f"  ⚠️  RATE LIMIT TRIGGERED (FastAPI Shield)")
            elif resp.status_code == 413:
                print(f"  🛡️  SIZE LIMIT TRIGGERED (Oversized Payload Blocked)")
        except Exception as e:
            pass

    async def background_noise_loop(self):
        """Simulates 85% of traffic as randomized normal noise."""
        while self.running:
            ip = self.get_random_ip(NORMAL_POOLS)
            packet = {
                "src_ip": ip,
                "dst_ip": "10.1.1.50",
                "src_port": random.randint(1024, 65535),
                "dst_port": random.choice([80, 443, 22, 53]),
                "protocol": random.choice(["TCP", "HTTP", "DNS"]),
                "packet_size": random.randint(64, 1500),
                "payload_size": random.randint(0, 500),
                "flags": "PA",
                "duration": random.uniform(0.01, 1.0)
            }
            asyncio.create_task(self.send_packet(packet))
            await asyncio.sleep(1 / (self.target_pps * 0.85))

    async def bot_attack_loop(self):
        """Simulates 15% of traffic as multi-stage bot attacks."""
        while self.running:
            # 1. Spawn or Pick a Bot
            if len(self.active_bots) < 10 or random.random() < 0.2:
                bot_ip = self.get_random_ip(BOT_POOLS)
                self.active_bots[bot_ip] = {"stage": "RECON", "packets": 0}

            bot_ip = random.choice(list(self.active_bots.keys()))
            bot_state = self.active_bots[bot_ip]
            
            # 2. Select Attack Stage
            stage = bot_state["stage"]
            attacks = ATTACK_STAGES[stage]
            attack = random.choice(attacks)
            
            # 3. Increase Sophistication over time
            packet = {
                "src_ip": bot_ip,
                "dst_ip": "10.1.1." + str(random.randint(50, 100)),
                "src_port": random.randint(1024, 65535),
                "dst_port": random.choice([80, 22, 3389]),
                "protocol": "TCP",
                "packet_size": 200 + random.randint(0, int(attack["risk_base"] * 3000)),
                "payload_size": attack["payload_size"],
                "flags": attack["flags"],
                "duration": random.uniform(0.1, 0.5)
            }
            
            asyncio.create_task(self.send_packet(packet))
            
            # 4. Progress Bot Stage
            bot_state["packets"] += 1
            if bot_state["packets"] > 5:
                if stage == "RECON": bot_state["stage"] = "EXPLOIT"
                elif stage == "EXPLOIT": bot_state["stage"] = "C2"
                bot_state["packets"] = 0

            await asyncio.sleep(1 / (self.target_pps * 0.15))

    async def run(self, duration_s: int = 0):
        self.running = True
        print(f"🚀 Chaos Simulator Started | Target: {self.target_pps} PPS")
        print(f"🔗 API: {API_BASE} | Mode: STOCHASTIC REAL-WORLD")
        
        noise_task = asyncio.create_task(self.background_noise_loop())
        bot_task = asyncio.create_task(self.bot_attack_loop())
        
        start_time = time.time()
        try:
            while self.running:
                await asyncio.sleep(1)
                elapsed = time.time() - start_time
                print(f"📊 Stats: {self.total_sent} packets sent | Elapsed: {int(elapsed)}s | Active Bots: {len(self.active_bots)}")
                
                if duration_s > 0 and elapsed > duration_s:
                    break
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            noise_task.cancel()
            bot_task.cancel()
            print(f"\n🛑 Simulation Stopped. Total packets dispatched: {self.total_sent}")

if __name__ == "__main__":
    pps = 20
    if len(sys.argv) > 1:
        pps = int(sys.argv[1])
        
    sim = ChaosSimulator(target_pps=pps)
    asyncio.run(sim.run())
