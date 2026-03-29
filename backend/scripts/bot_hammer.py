import time
import random
import requests
import threading
from datetime import datetime

# 🎯 Target Configuration (Containerized Backend)
TARGET_URL = "http://localhost:8000/api/v1/traffic/analyze"
BOT_COUNT = 5
ATTACK_INTERVAL = 2  # seconds between pulses per bot

# 🧪 Attack Profiles
ATTACK_TYPES = [
    {"type": "SQL Injection", "payload": "SELECT * FROM users WHERE id = 1' OR '1'='1"},
    {"type": "XSS", "payload": "<script>alert('StealthVault_Pwned')</script>"},
    {"type": "Brute Force", "payload": "Auth attempt: admin/password123"},
    {"type": "DDoS", "payload": "GET /index.php HTTP/1.1"},
]

# 🤖 Bot Identities
BOT_IPS = [
    f"192.168.1.{i}" for i in range(100, 100 + BOT_COUNT)
]

def simulate_bot(bot_id, ip_address):
    """Simulates a single bot lifecycle."""
    print(f"🚀 Bot-{bot_id} [{ip_address}] initialized.")
    
    session_packets = 0
    while True:
        try:
            attack = random.choice(ATTACK_TYPES)
            payload = {
                "src_ip": ip_address,
                "dst_ip": "10.0.0.1",
                "src_port": random.randint(1024, 65535),
                "dst_port": 80,
                "protocol": "TCP",
                "payload_size": len(attack["payload"]),
                "payload": attack["payload"]
            }
            
            response = requests.post(TARGET_URL, json=payload, timeout=5)
            session_packets += 1
            
            if response.status_code == 200:
                result = response.json()
                status = "BLOCKED" if result["detection"]["is_threat"] else "BYPASSED"
                risk = result["detection"]["risk_score"]
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Bot-{bot_id} Pulse: {status} (Risk: {risk:.2f})")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Bot-{bot_id} Pulse: API ERROR ({response.status_code})")
                
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Bot-{bot_id} Error: {e}")
            
        time.sleep(ATTACK_INTERVAL + random.uniform(0, 1))

if __name__ == "__main__":
    print("╔═══════════════════════════════════════════════════════╗")
    print("║          STEALTHVAULT AI — 24/7 BOT HAMMER            ║")
    print("║       Simulating Real-World Attack Patterns           ║")
    print("╚═══════════════════════════════════════════════════════╝")
    
    threads = []
    for i in range(BOT_COUNT):
        t = threading.Thread(target=simulate_bot, args=(i+1, BOT_IPS[i]))
        t.daemon = True
        threads.append(t)
        t.start()
        
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Bot Hammer stopped.")
