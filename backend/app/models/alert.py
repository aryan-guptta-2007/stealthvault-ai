"""
StealthVault AI - Data Models
Pydantic schemas for network packets, threats, and alerts.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
import uuid


class AttackType(str, Enum):
    """Known attack categories."""
    NORMAL = "Normal"
    DDOS = "DDoS"
    PORT_SCAN = "PortScan"
    BRUTE_FORCE = "BruteForce"
    MALWARE = "Malware"
    SQL_INJECTION = "SQLInjection"
    XSS = "XSS"
    UNKNOWN = "Unknown"


class Severity(str, Enum):
    """Threat severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Protocol(str, Enum):
    """Network protocols."""
    TCP = "TCP"
    UDP = "UDP"
    ICMP = "ICMP"
    HTTP = "HTTP"
    HTTPS = "HTTPS"
    DNS = "DNS"
    SSH = "SSH"
    FTP = "FTP"
    OTHER = "OTHER"


class NetworkPacket(BaseModel):
    """Raw network packet data."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tenant_id: str = "default"  # Required for SaaS routing
    src_ip: str
    dst_ip: str
    src_port: int = 0
    dst_port: int = 0
    protocol: Protocol = Protocol.TCP
    packet_size: int = 0
    flags: str = ""
    payload_size: int = 0
    ttl: int = 64
    duration: float = 0.0


class FeatureVector(BaseModel):
    """Extracted features from a packet for AI processing."""
    src_port: float
    dst_port: float
    packet_size: float
    payload_size: float
    ttl: float
    duration: float
    protocol_tcp: float = 0.0
    protocol_udp: float = 0.0
    protocol_icmp: float = 0.0
    protocol_http: float = 0.0
    flag_syn: float = 0.0
    flag_ack: float = 0.0
    flag_fin: float = 0.0
    flag_rst: float = 0.0
    flag_psh: float = 0.0


class AnomalyResult(BaseModel):
    """Output from anomaly detection model."""
    is_anomaly: bool
    anomaly_score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)


class ClassificationResult(BaseModel):
    """Output from attack classifier."""
    attack_type: AttackType
    confidence: float = Field(ge=0.0, le=1.0)
    probabilities: dict[str, float] = {}


class RiskScore(BaseModel):
    """Combined risk assessment."""
    score: float = Field(ge=0.0, le=1.0)
    severity: Severity
    anomaly_contribution: float
    classification_contribution: float
    behavior_flags: list[str] = []


class BrainAnalysis(BaseModel):
    """AI brain analysis output."""
    attack_name: str
    description: str
    danger_level: str
    what_is_happening: str
    how_to_stop: str
    technical_details: str
    recommended_actions: list[str] = []


class ThreatAlert(BaseModel):
    """Complete threat alert combining all analysis."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:12])
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    packet: NetworkPacket
    anomaly: AnomalyResult
    classification: ClassificationResult
    risk: RiskScore
    brain_analysis: Optional[BrainAnalysis] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DashboardStats(BaseModel):
    """Aggregated statistics for the dashboard."""
    total_packets_analyzed: int = 0
    total_alerts: int = 0
    critical_alerts: int = 0
    high_alerts: int = 0
    medium_alerts: int = 0
    low_alerts: int = 0
    attack_distribution: dict[str, int] = {}
    avg_risk_score: float = 0.0
    top_attackers: list[dict] = []
    packets_per_minute: float = 0.0
    system_status: str = "ACTIVE"
