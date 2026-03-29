"""
╔═══════════════════════════════════════════════════════════╗
║         STEALTHVAULT AI — SOC ATTACK SIMULATOR            ║
║                                                           ║
║  Simulates a MULTI-PHASE attack through the full          ║
║  3-agent pipeline (SOC) to generate Attack Stories.       ║
╚═══════════════════════════════════════════════════════════╝

This script simulates a realistic multi-stage cyber intrusion:

Phase 1: Reconnaissance (Port Scan)
Phase 2: Credential Attack (Brute Force SSH)
Phase 3: Exploitation (SQL Injection on web server)
Phase 4: Malware C2 (Command & Control beaconing)
Phase 5: DDoS (Smokescreen)

Each phase is sent through the /api/v1/soc/analyze endpoint,
which triggers all 3 agents and builds Attack Stories.
"""

import requests
import time
import json
import sys

API_BASE = "http://localhost:8000/api/v1"


def send_packet(packet_data: dict) -> dict:
    """Send a packet through the SOC pipeline."""
    try:
        resp = requests.post(f"{API_BASE}/soc/analyze", json=packet_data, timeout=10)
        return resp.json()
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return {}


def print_verdict(result: dict, label: str = ""):
    """Pretty-print a SOC verdict."""
    det = result.get("detection", {})
    intel = result.get("intelligence", {})
    defense = result.get("defense", {})
    brain = result.get("brain", {})
    
    severity = det.get("severity", "?")
    risk = det.get("risk_score", 0)
    attack = det.get("attack_type", "?")
    signals = det.get("signal_count", 0)
    ms = result.get("processing_time_ms", 0)
    
    severity_icons = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢",
    }
    icon = severity_icons.get(severity, "⚪")
    
    print(f"  {icon} [{severity.upper()}] {attack} | Risk: {risk:.3f} | Signals: {signals} | {ms:.1f}ms")
    
    if intel:
        stage = intel.get("attack_stage", "?")
        urgency = intel.get("urgency", "?")
        campaign = intel.get("is_campaign", False)
        print(f"     └─ Stage: {stage} | Urgency: {urgency} | Campaign: {campaign}")
    
    if defense:
        action = defense.get("action_type", "none")
        target = defense.get("target", "?")
        print(f"     └─ 🛡️ DEFENSE: {action} → {target}")
    
    if brain:
        print(f"     └─ 🧠 {brain.get('attack_name', '?')}")


def phase_header(phase_num: int, name: str, description: str):
    """Print a phase header."""
    print()
    print(f"  {'═' * 50}")
    print(f"  Phase {phase_num}: {name}")
    print(f"  {description}")
    print(f"  {'═' * 50}")


def main():
    ATTACKER_IP = "45.33.32.156"   # Simulated external attacker
    ATTACKER_2 = "185.220.101.42"  # Second attacker (for campaign detection)
    TARGET_IP = "10.0.0.1"
    
    print()
    print("╔═══════════════════════════════════════════════════╗")
    print("║     STEALTHVAULT AI — ATTACK STORY SIMULATION    ║")
    print("║                                                   ║")
    print("║  Simulating a multi-phase cyber intrusion...      ║")
    print("╚═══════════════════════════════════════════════════╝")
    print()
    
    # ─── Check server ────────────────────────────────────────
    try:
        health = requests.get("http://localhost:8000/health", timeout=5)
        print(f"  ✅ Server is online")
    except Exception:
        print("  ❌ Server not running. Start with:")
        print("     python -m uvicorn app.main:app --port 8000")
        sys.exit(1)
    
    # ═══════════════════════════════════════════════════════════
    # PHASE 1: RECONNAISSANCE (Port Scan)
    # ═══════════════════════════════════════════════════════════
    phase_header(1, "RECONNAISSANCE", "Port scanning from external IP...")
    
    for port in [22, 80, 443, 3306, 5432, 8080, 8443, 3389, 445, 23]:
        result = send_packet({
            "src_ip": ATTACKER_IP,
            "dst_ip": TARGET_IP,
            "src_port": 54321,
            "dst_port": port,
            "protocol": "TCP",
            "packet_size": 44,
            "flags": "S",   # SYN scan
            "payload_size": 0,
            "ttl": 52,
            "duration": 0.001,
        })
        print_verdict(result, f"  Scan port {port}")
        time.sleep(0.2)
    
    time.sleep(1)
    
    # ═══════════════════════════════════════════════════════════
    # PHASE 2: CREDENTIAL ATTACK (Brute Force SSH)
    # ═══════════════════════════════════════════════════════════
    phase_header(2, "CREDENTIAL ATTACK", "Brute forcing SSH on port 22...")
    
    for i in range(15):
        result = send_packet({
            "src_ip": ATTACKER_IP,
            "dst_ip": TARGET_IP,
            "src_port": 50000 + i,
            "dst_port": 22,
            "protocol": "SSH",
            "packet_size": 200,
            "flags": "SA",
            "payload_size": 150,
            "ttl": 55,
            "duration": 0.05,
        })
        if i % 5 == 0:
            print_verdict(result, f"  Login attempt #{i+1}")
        time.sleep(0.1)
    
    time.sleep(1)
    
    # ═══════════════════════════════════════════════════════════
    # PHASE 3: EXPLOITATION (SQL Injection)
    # ═══════════════════════════════════════════════════════════
    phase_header(3, "EXPLOITATION", "SQL injection on web application...")
    
    for i in range(8):
        result = send_packet({
            "src_ip": ATTACKER_IP,
            "dst_ip": TARGET_IP,
            "src_port": 60000 + i,
            "dst_port": 80,
            "protocol": "HTTP",
            "packet_size": 1500,
            "flags": "PA",
            "payload_size": 1200,
            "ttl": 62,
            "duration": 0.3,
        })
        if i % 3 == 0:
            print_verdict(result, f"  SQLi probe #{i+1}")
        time.sleep(0.2)
    
    time.sleep(1)
    
    # ═══════════════════════════════════════════════════════════
    # PHASE 4: C2 COMMUNICATION (Malware beaconing)
    # ═══════════════════════════════════════════════════════════
    phase_header(4, "COMMAND & CONTROL", "Malware beaconing to C2 server...")
    
    for i in range(10):
        result = send_packet({
            "src_ip": "10.0.0.50",           # Infected internal machine
            "dst_ip": "185.100.87.202",       # C2 server
            "src_port": 49000 + i,
            "dst_port": 4444,
            "protocol": "TCP",
            "packet_size": 120,
            "flags": "PA",
            "payload_size": 80,
            "ttl": 120,
            "duration": 0.01,
        })
        if i % 4 == 0:
            print_verdict(result, f"  Beacon #{i+1}")
        time.sleep(0.3)
    
    time.sleep(1)
    
    # ═══════════════════════════════════════════════════════════
    # PHASE 5: SECOND ATTACKER (Campaign detection)
    # ═══════════════════════════════════════════════════════════
    phase_header(5, "SECOND ATTACKER", "Coordinated attack from different IP...")
    
    for port in [80, 443, 8080]:
        result = send_packet({
            "src_ip": ATTACKER_2,
            "dst_ip": TARGET_IP,
            "src_port": 33000,
            "dst_port": port,
            "protocol": "TCP",
            "packet_size": 40,
            "flags": "S",
            "payload_size": 0,
            "ttl": 48,
            "duration": 0.001,
        })
        print_verdict(result, f"  Scan port {port}")
        time.sleep(0.2)
    
    # ═══════════════════════════════════════════════════════════
    # RESULTS
    # ═══════════════════════════════════════════════════════════
    print()
    print("╔═══════════════════════════════════════════════════╗")
    print("║              SIMULATION COMPLETE                  ║")
    print("╚═══════════════════════════════════════════════════╝")
    print()
    
    # Fetch SOC status
    try:
        status = requests.get(f"{API_BASE}/soc/status").json()
        orch = status.get("orchestrator", {})
        stories = status.get("stories", {})
        
        print(f"  📊 Total Packets Analyzed:  {orch.get('total_processed', 0)}")
        print(f"  🚨 Total Threats:           {orch.get('total_threats', 0)}")
        print(f"  🛡️  Total Defenses:          {orch.get('total_defenses', 0)}")
        print(f"  ⚡ Avg Processing Time:     {orch.get('avg_processing_ms', 0):.2f}ms")
        print(f"  📖 Active Stories:           {stories.get('active_stories', 0)}")
        print()
    except Exception:
        pass
    
    # Fetch attack stories
    try:
        stories_resp = requests.get(f"{API_BASE}/soc/stories").json()
        story_list = stories_resp.get("stories", [])
        
        if story_list:
            print("  🎬 ATTACK STORIES:")
            print("  " + "─" * 50)
            for story in story_list:
                print(f"\n  {story['title']}")
                print(f"  Duration: {story['duration']} | Events: {story['total_events']}")
                print(f"  Sophistication: {story['sophistication']}")
                print(f"  Risk Trend: {story['risk_trend']}")
                print()
                
                for phase in story.get("phases", []):
                    predicted = " ← PREDICTED" if phase.get("is_predicted") else ""
                    print(f"    {phase['icon']} Phase {phase['phase']}: {phase['name']}{predicted}")
                    print(f"       {phase['narrative'][:80]}...")
                    if not phase.get("is_predicted"):
                        print(f"       Events: {phase['event_count']} | Risk: {phase['max_risk']:.3f} | Severity: {phase['severity']}")
                    else:
                        print(f"       Confidence: {phase['prediction_confidence']:.0%}")
                    print()
                
                print(f"    🧠 AI Insight:")
                insight = story.get("ai_insight", "")
                # Word wrap
                words = insight.split()
                line = "       "
                for word in words:
                    if len(line) + len(word) > 75:
                        print(line)
                        line = "       "
                    line += word + " "
                if line.strip():
                    print(line)
                print()
                print(f"    🛡️ Defense: {story.get('defense_action', 'None')}")
                print("  " + "─" * 50)
        else:
            print("  ⚠️  No attack stories generated yet.")
            print("     This may happen if the AI classified all traffic as low-risk.")
            print("     Try running the simulation again or with more extreme packet values.")
    except Exception as e:
        print(f"  ❌ Error fetching stories: {e}")
    
    print()
    print("  🔗 View stories:  http://localhost:8000/api/v1/soc/stories")
    print("  🔗 SOC status:    http://localhost:8000/api/v1/soc/status")
    print("  🔗 Campaigns:     http://localhost:8000/api/v1/soc/campaigns")
    print()


if __name__ == "__main__":
    main()
