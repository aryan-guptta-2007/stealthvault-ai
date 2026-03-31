<p align="center">
  <img src="https://img.shields.io/badge/StealthVault-V1.2.0--BATTLE--MODE-red?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python" />
  <img src="https://img.shields.io/badge/FastAPI-0.100+-green?style=for-the-badge&logo=fastapi" />
  <img src="https://img.shields.io/badge/React-18+-61DAFB?style=for-the-badge&logo=react" />
</p>

<h1 align="center">🛡️ StealthVault AI SOC</h1>

<h3 align="center">
  The World's First Autonomous AI Security Operations Center with "Battle Mode" Simulation
</h3>

<p align="center">
  <strong>StealthVault AI is an elite, multi-tenant autonomous SOC platform that leverages Isolation Forest ML and a 3-agent neural loop to detect, visualize, and neutralize zero-day threats in real-time.</strong>
</p>

<p align="center">
  <a href="#-global-threat-intelligence-map">Live Map</a> | 
  <a href="#-offensive-simulation-battle-mode">Combat Simulator</a> | 
  <a href="#-autonomous-quarantine">Auto-Defense</a> | 
  <a href="#-multi-channel-alerting">External Alerts</a>
</p>

---

## 🚀 The Multi-Agent Intelligence Grid

StealthVault isn't just a dashboard; it's a team of three specialized AI agents working in a recursive neural loop:

| Agent | Core Identity | Advanced Intelligence |
|-------|---------------|-----------------------|
| 🧠 **Detector** | The Neural Eye | Hybrid Isolation Forest + Random Forest. Detects anomalies with 94%+ accuracy. |
| 🔍 **Analyst** | The Strategic Brain | Cyber Kill Chain mapping & Attack Story generation. Predicts the attacker's next move. |
| 🛡️ **Defender** | The Sovereign Fist | Surgical auto-blocking with Multi-Tenant isolation & Neural Safety Gates. |

---

## 🔥 Elite "SOC 2.0" Features

### 🌍 Global Threat Intelligence Map
Visualize your attack surface in 4D. StealthVault maps real-time network packets to their geographic origins, providing a pulsing, high-fidelity visualization of global threat vectors.
> [!TIP]
> **Recruiter Note**: Uses `react-simple-maps` and `d3-geo` for high-performance geospatial rendering.

### ⚔️ Offensive Simulation (Battle Mode)
Don't just defend—stress test. StealthVault includes a high-intensity **Combat Deck** where you can trigger simulated **DDoS Floods**, **Brute Force**, and **Stealth Port Scans** to witness the AI's autonomous response in real-time.

### 🛡️ Autonomous IP Quarantine
When a threat is identified as critical, the Defender Agent autonomously "neutralizes" the attacker at the OS firewall level and records the metadata in a persistent **Active Quarantine** monitor.

### 🔔 Multi-Channel Alerting (Triage)
Operational awareness anywhere. StealthVault integrates with **Telegram** and **Slack** via an asynchronous notification engine, delivering high-priority threat intelligence directly to your security team's mobile devices.

---

## 🏗️ Technical Architecture

```mermaid
graph TD
    %% Source
    Traffic[Network Traffic] --> Sensor[Stealth Sensor]
    Simulator[⚔️ Combat Simulator] --> Sensor
    
    %% Core Orchestration
    Sensor --> Orchestrator[SOC Orchestrator]
    
    subgraph "The Neural Defensive Loop"
    Orchestrator --> Agent1[🧠 Agent 1: Detector]
    Agent1 --> Agent2[🔍 Agent 2: Analyst]
    Agent2 --> Agent3[🛡️ Agent 3: Defender]
    end
    
    %% Outputs
    Agent2 --> Story[📜 Attack Narrative Engine]
    Agent2 --> Notify[🔔 Telegram/Slack Hook]
    Agent3 --> Firewall[🔥 Autonomous Firewall]
    
    subgraph "Persistent SOC State"
    Agent3 --> DB[(Postgres + TimescaleDB)]
    end
    
    %% Frontend
    DB --> UI[🖥️ Mission Control UI]
    UI --> Map[🌍 Live Geo-Threat Map]
    UI --> Quarantine[🔬 Active Quarantine Table]
    
    %% Feedback Loop
    UI --> Feedback[⚖️ Analyst Feedback]
    Feedback --> Learner[🧬 Continuous Learner]
    Learner --> Agent1
```

---

## ⚡ The Tech Stack

- **Backend Logic**: Python 3.10+ (FastAPI, Pydantic V2)
- **AI/ML Engine**: Scikit-Learn (Isolation Forest), NumPy, Pandas
- **Geographic Intel**: IP-API Integration + GeoLite2
- **Persistent Storage**: PostgreSQL + SQLAlchemy (Async)
- **Frontend Command Deck**: Next.js 14, Tailwind CSS, Lucide Icons
- **Data Visualization**: D3-Geo, React-Simple-Maps
- **Alerting Stack**: Telegram Bot API, Slack Webhooks, WebSockets

---

## 🛰️ Deployment & Quickstart

### 1. Repository Setup
```bash
git clone https://github.com/YOUR_USER/stealthvault-ai.git
cd stealthvault-ai
```

### 2. Neural Environment Configuration
Configure your `.env` file in the `backend/` directory:
```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/stealthvault
SV_TELEGRAM_BOT_TOKEN=your_token
SV_SLACK_WEBHOOK_URL=your_webhook
```

### 3. Launch the SOC Command Center
```bash
# Backend (Port 8000)
cd backend && pip install -r requirements.txt
python app/main.py

# Frontend (Port 3000)
cd ../frontend && npm install
npm run dev
```

---

## 🛡️ The Ethical Defense Shield
StealthVault AI is designed for **maximum defensive resilience**. It includes safety mechanisms to prevent "friendly fire" blocks on critical infrastructure:
- **Neural Thresholds**: Prevents hair-trigger blocking.
- **Shadow Mode**: Simulation-only defense for risk-sensitive environments.
- **Admin Safety Gates**: Whitelisting for gateway and core DNS infrastructure.

---

## 📜 Community & License
MIT License. **Built for the next generation of autonomous cyber defense.**

⭐ **Star this repository if you believe in autonomous, AI-driven open-source security.**
