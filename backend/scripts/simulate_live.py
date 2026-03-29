"""
StealthVault AI - Live Demo Simulation
Simulates real-time network traffic feeding into the API.
Run this AFTER starting the server and training the models.

Usage:
    python scripts/simulate_live.py
"""

import asyncio
import httpx
import numpy as np
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.alert import Protocol

SERVER_BASE = "http://localhost:8000"
API_BASE = f"{SERVER_BASE}/api/v1"

# Attack scenarios for simulation
SCENARIOS = [
    {
        "name": "🌊 DDoS Attack Wave",
        "count": 15,
        "packets": lambda i: {
            "src_ip": f"10.0.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}",
            "dst_ip": "10.0.0.1",
            "src_port": np.random.randint(1024, 65535),
            "dst_port": 80,
            "protocol": "TCP",
            "packet_size": np.random.randint(40, 100),
            "flags": "S",
            "payload_size": 0,
            "ttl": np.random.randint(20, 60),
            "duration": 0.001,
        },
    },
    {
        "name": "🔍 Port Scan Detected",
        "count": 10,
        "packets": lambda i: {
            "src_ip": "192.168.1.100",
            "dst_ip": "10.0.0.5",
            "src_port": 54321,
            "dst_port": i * 100 + 1,  # Sequential port scan
            "protocol": "TCP",
            "packet_size": 44,
            "flags": "S",
            "payload_size": 0,
            "ttl": 64,
            "duration": 0.01,
        },
    },
    {
        "name": "🔐 Brute Force SSH",
        "count": 12,
        "packets": lambda i: {
            "src_ip": "172.16.0.5",
            "dst_ip": "10.0.0.2",
            "src_port": np.random.randint(40000, 65535),
            "dst_port": 22,
            "protocol": "SSH",
            "packet_size": np.random.randint(100, 300),
            "flags": "SA",
            "payload_size": np.random.randint(50, 200),
            "ttl": 58,
            "duration": 0.5,
        },
    },
    {
        "name": "✅ Normal Traffic",
        "count": 20,
        "packets": lambda i: {
            "src_ip": f"192.168.1.{np.random.randint(1, 254)}",
            "dst_ip": f"10.0.0.{np.random.randint(1, 50)}",
            "src_port": np.random.randint(1024, 65535),
            "dst_port": np.random.choice([80, 443, 53, 22]),
            "protocol": np.random.choice(["TCP", "HTTP", "HTTPS", "DNS"]),
            "packet_size": np.random.randint(200, 1500),
            "flags": "SA",
            "payload_size": np.random.randint(100, 800),
            "ttl": np.random.randint(55, 128),
            "duration": round(np.random.exponential(0.5), 3),
        },
    },
    {
        "name": "🦠 Malware C2 Communication",
        "count": 8,
        "packets": lambda i: {
            "src_ip": "10.0.0.50",
            "dst_ip": "45.33.32.156",
            "src_port": np.random.randint(40000, 50000),
            "dst_port": np.random.choice([4444, 5555, 8888]),
            "protocol": "TCP",
            "packet_size": np.random.randint(50, 200),
            "flags": "PA",
            "payload_size": np.random.randint(30, 150),
            "ttl": 128,
            "duration": round(np.random.uniform(0.01, 0.1), 3),
        },
    },
]


async def run_simulation():
    """Run the live traffic simulation."""
    print("=" * 60)
    print("  StealthVault AI — LIVE SIMULATION")
    print("=" * 60)
    print()

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Check server health
        try:
            resp = await client.get(f"{SERVER_BASE}/health")
            health = resp.json()
            print(f"  Server Status: {health['status']}")
            print(f"  Anomaly Model: {health['anomaly_model']}")
            print(f"  Classifier Model: {health['classifier_model']}")
            print()
        except Exception as e:
            print(f"  ❌ Cannot connect to server: {e}")
            print("  Make sure the server is running: python -m uvicorn app.main:app --reload")
            return

        total_alerts = 0
        total_critical = 0

        for scenario in SCENARIOS:
            print(f"\n  {scenario['name']}")
            print(f"  {'─' * 50}")

            for i in range(scenario["count"]):
                packet_data = scenario["packets"](i)
                # Convert numpy types to Python types
                packet_data = {
                    k: int(v) if isinstance(v, np.integer) else v
                    for k, v in packet_data.items()
                }

                try:
                    resp = await client.post(
                        f"{API_BASE}/traffic/analyze",
                        json=packet_data,
                    )
                    result = resp.json()

                    severity = result["risk"]["severity"]
                    risk_score = result["risk"]["score"]
                    attack = result["classification"]["attack_type"]

                    icon = {
                        "critical": "🔴",
                        "high": "🟠",
                        "medium": "🟡",
                        "low": "🟢",
                    }.get(severity, "⚪")

                    if severity in ["critical", "high"]:
                        total_critical += 1
                        print(
                            f"    {icon} [{severity.upper()}] "
                            f"Risk: {risk_score:.2f} | "
                            f"Attack: {attack} | "
                            f"From: {packet_data['src_ip']}"
                        )

                    total_alerts += 1

                except Exception as e:
                    print(f"    ❌ Error: {e}")

                await asyncio.sleep(0.1)  # Simulate real-time pace

        # Print summary
        print("\n" + "=" * 60)
        print("  📊 SIMULATION COMPLETE")
        print(f"  Total packets analyzed: {total_alerts}")
        print(f"  Critical/High alerts:   {total_critical}")

        # Get dashboard stats
        try:
            resp = await client.get(f"{API_BASE}/dashboard")
            stats = resp.json()
            print(f"\n  Dashboard Stats:")
            print(f"    Total Alerts:    {stats['total_alerts']}")
            print(f"    Critical:        {stats['critical_alerts']}")
            print(f"    High:            {stats['high_alerts']}")
            print(f"    Avg Risk Score:  {stats['avg_risk_score']:.4f}")
            print(f"    Top Attackers:   {len(stats['top_attackers'])}")
            if stats['attack_distribution']:
                print(f"    Attack Types:    {stats['attack_distribution']}")
        except Exception:
            pass

        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_simulation())
